"""Pitch-range suggestions and level-safe remixing; no gender inference."""
import numpy as np


def pitch_summary(f0, target, frame_energy=None):
    values = np.asarray(f0, dtype=np.float64).reshape(-1)
    valid = np.isfinite(values) & (values >= 50) & (values <= 1100)
    if frame_energy is not None:
        energy = np.asarray(frame_energy, dtype=np.float64)
        n = min(len(values), len(energy))
        valid[n:] = False
        if n:
            valid[:n] &= energy[:n] > max(float(np.percentile(energy[:n], 95))*.04, 1e-6)
    values = values[valid]
    if len(values) < 50:
        return dict(available=False, suggested_pitch=0, voiced_seconds=len(values)/100,
                    message='有效有声音频不足，保持原调')
    low, median, high = np.percentile(values, [10, 50, 90])
    source_notes = 69+12*np.log2(values/440)
    target_low = 69+12*np.log2(target['p10_hz']/440)-2
    target_high = 69+12*np.log2(target['p90_hz']/440)+2
    target_mid = 69+12*np.log2(target['median_hz']/440)
    scores = {}
    for shift in [0, -12, 12]:
        notes = source_notes+shift
        outside = np.maximum(target_low-notes, 0)**2+np.maximum(notes-target_high, 0)**2
        scores[shift] = float(np.mean(outside)+.05*(np.median(notes)-target_mid)**2+.2*abs(shift))
    suggested = min(scores, key=scores.get)
    label = '偏低音区' if median < 170 else '中音区' if median < 260 else '偏高音区'
    return dict(available=True, median_hz=round(float(median), 1), p10_hz=round(float(low), 1),
                p90_hz=round(float(high), 1), range_label=label, voiced_seconds=round(len(values)/100, 2),
                suggested_pitch=suggested, target_profile=target,
                method='Octave-only range matching; does not infer sex or gender')


def applied_pitch(settings, analysis):
    suggestion = analysis['suggested_pitch'] if settings.get('pitch_mode') == 'auto' else 0
    return int(np.clip(suggestion+settings['pitch'], -12, 12))


def stereo(audio):
    audio = np.asarray(audio, dtype=np.float32)
    if audio.ndim == 1:
        return np.repeat(audio[:, None], 2, axis=1)
    if audio.ndim != 2 or audio.shape[1] not in (1, 2):
        raise ValueError('Expected mono or stereo audio with samples on the first axis')
    return np.repeat(audio, 2, axis=1) if audio.shape[1] == 1 else audio


def remix(converted, original_vocals, instrumental):
    voice = np.asarray(converted, dtype=np.float32)
    reference = np.asarray(original_vocals, dtype=np.float32)
    music = stereo(instrumental)
    if voice.ndim != 1 or reference.ndim != 1 or len(voice) != len(reference) or len(voice) != len(music):
        raise ValueError('Remix stems must have the same timeline')
    if not all(np.isfinite(x).all() for x in (voice, reference, music)):
        raise ValueError('Non-finite remix stems')
    threshold = max(float(np.percentile(np.abs(reference), 70)), float(np.max(np.abs(reference)))*.02, 1e-5)
    active = np.abs(reference) > threshold
    gain = 1.
    if np.any(active):
        ref_rms = np.sqrt(np.mean(reference[active].astype(np.float64)**2))
        new_rms = np.sqrt(np.mean(voice[active].astype(np.float64)**2))
        gain = float(np.clip(ref_rms/max(new_rms, 1e-8), .05, 5))
    mixed = music+voice[:, None]*gain
    peak = float(np.max(np.abs(mixed)))
    headroom = min(1., .98/max(peak, 1e-8))
    return (mixed*headroom).astype(np.float32), dict(vocal_gain=gain, common_gain=headroom,
                                                    channels=2, peak_before_headroom=peak)
