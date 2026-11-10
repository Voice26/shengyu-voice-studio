"""Source-guided pause attenuation with conservative voiced/edge protection.

Does not trim time or infer speech from the converted signal. A supplied raw
10 ms RMVPE voicing track protects quiet sung notes independently of loudness.
NumPy-only so the same processing can be verified locally and on the GPU host.
"""
import numpy as np

VERSION = 'pause-guard-v1'
HEAD_PADDING_SECONDS = .4
TAIL_PADDING_SECONDS = .5


def frame_rms(audio, sample_rate):
    audio = np.asarray(audio, dtype=np.float32)
    if audio.ndim != 1 or not len(audio) or not np.isfinite(audio).all():
        raise ValueError('Expected finite, non-empty mono audio')
    hop = max(1, round(sample_rate*.01))
    window = max(2, round(sample_rate*.02))
    padded = np.pad(audio, (window//2, window))
    squares = np.r_[0., np.cumsum(padded.astype(np.float64)**2)]
    centers = np.arange(0, len(audio), hop)
    return np.sqrt(np.maximum(0, (squares[centers+window]-squares[centers])/window)), centers


def runs(mask):
    edges = np.diff(np.r_[False, np.asarray(mask, dtype=bool), False].astype(np.int8))
    return zip(np.flatnonzero(edges == 1), np.flatnonzero(edges == -1))


def voiced_protection(voiced, frame_count, before_frames=12, after_frames=20):
    track = np.zeros(frame_count, dtype=bool)
    if voiced is None:
        return track
    voiced = np.asarray(voiced, dtype=bool).reshape(-1)
    track[:min(len(voiced), frame_count)] = voiced[:frame_count]
    protected = np.zeros(frame_count, dtype=bool)
    for begin, end in runs(track):
        protected[max(0, begin-before_frames):min(frame_count, end+after_frames)] = True
    return protected


def pause_envelope(source, sample_rate, voiced=None):
    rms, centers = frame_rms(source, sample_rate)
    db = 20*np.log10(np.maximum(rms, 1e-8))
    noise, active = np.percentile(db, [10, 95])
    # A conservative relative threshold; no gate when there is no clear noise/voice gap.
    threshold = float(np.clip(min(noise+9, active-28), -70, -38))
    protection = voiced_protection(voiced, len(rms))
    quiet = (db < threshold) & ~protection
    gain = np.ones(len(rms), dtype=np.float32)
    regions = []
    if active-noise >= 16 or active < -80:
        for begin, end in runs(quiet):
            if end-begin < 18:  # Never chase brief spaces between syllables.
                continue
            # Keep energy transitions even when raw F0 misses an unvoiced consonant.
            start = int(begin + (0 if begin == 0 else 10))
            stop = int(end - (0 if end == len(rms) else 8))
            if stop-start < 12:
                continue
            floor = 10**(-30/20)
            section = np.full(stop-start, floor, dtype=np.float32)
            fade = min(8, (stop-start)//2)
            curve = np.linspace(0, 1, fade, dtype=np.float32)
            curve = curve*curve*(3-2*curve)
            if start:
                section[:fade] = 1-(1-floor)*curve
            if stop < len(rms):
                section[-fade:] = floor+(1-floor)*curve
            gain[start:stop] = np.minimum(gain[start:stop], section)
            regions.append(dict(start_seconds=round(centers[start]/sample_rate, 3),
                                end_seconds=round(min(len(source), stop*round(sample_rate*.01))/sample_rate, 3)))
    sample_gain = np.interp(np.arange(len(source)), centers, gain).astype(np.float32)
    return sample_gain, dict(version=VERSION, threshold_db=round(threshold, 2),
                             noise_floor_db=round(float(noise), 2), active_level_db=round(float(active), 2),
                             protected_voiced_frames=int(protection.sum()), regions=regions,
                             attenuated_seconds=round(float(np.mean(sample_gain < .99)*len(source)/sample_rate), 3),
                             maximum_attenuation_db=30)


def trim_padding(converted, source_length, sample_rate, head_seconds=HEAD_PADDING_SECONDS):
    head = round(sample_rate*head_seconds)
    converted = np.asarray(converted, dtype=np.float32)
    if converted.ndim != 1 or not np.isfinite(converted).all():
        raise ValueError('Invalid converted audio')
    if len(converted) < head+source_length:
        raise ValueError('Padded inference output is too short')
    return converted[head:head+source_length].copy()


def apply_cleanup(source, converted, sample_rate, voiced=None):
    source = np.asarray(source, dtype=np.float32)
    converted = np.asarray(converted, dtype=np.float32)
    if len(source) != len(converted) or source.ndim != 1 or converted.ndim != 1:
        raise ValueError('Input and output must have identical mono timelines')
    if not np.isfinite(converted).all():
        raise ValueError('Invalid converted audio')
    gain, report = pause_envelope(source, sample_rate, voiced)
    cleaned = converted*gain
    suppressed = gain < .25
    if np.any(suppressed):
        before = float(np.sqrt(np.mean(converted[suppressed].astype(np.float64)**2)))
        after = float(np.sqrt(np.mean(cleaned[suppressed].astype(np.float64)**2)))
        report.update(pause_rms_before_db=round(20*np.log10(max(before, 1e-8)), 2),
                      pause_rms_after_db=round(20*np.log10(max(after, 1e-8)), 2),
                      pause_reduction_db=round(20*np.log10(max(before, 1e-8)/max(after, 1e-8)), 2))
    return cleaned, report
