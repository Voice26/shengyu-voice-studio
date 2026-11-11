'use strict';
// Chinese source strings remain the default locale for existing deployments.
const english = {
  '声屿': 'Shengyu',
  '声屿首页': 'Shengyu home',
  '声屿 · 本地换声工作台': 'Shengyu · Voice Conversion Studio',
  '声屿 · 换声工作台': 'Shengyu · Voice Conversion Studio',
  '最近生成 · 声屿': 'Recent Results · Shengyu',
  '跳转到主要内容': 'Skip to main content',
  '工作空间': 'Workspace',
  '主导航': 'Main navigation',
  '换声工作台': 'Conversion',
  '最近生成': 'Recent results',
  '本地工作空间': 'Local workspace',
  '内网工作空间': 'Private workspace',
  '免登录，本机保存结果。': 'No sign-in. Results are saved locally.',
  '免登录，结果保存在服务器。': 'No sign-in. Results are saved on the server.',
  '换声使用服务器 GPU。': 'Conversion runs on the server GPU.',
  '换声使用本机 CPU。': 'Conversion runs on this computer.',
  '音频由内网服务器处理。': 'Audio is processed on the private server.',
  '音频在本机处理': 'Audio is processed locally',
  '服务器 GPU 推理': 'Server GPU inference',
  '推理通过 SSH 连接你的服务器': 'Inference runs on your server over SSH',
  '无需登录': 'No sign-in required',
  '声音转换': 'Voice conversion',
  '正在检查环境': 'Checking environment',
  '重新检查连接': 'Check connection',
  '任务状态暂时无法同步，正在自动重连。请保持网络连接。': 'Reconnecting to sync task status. Please stay connected.',
  '导入歌曲或人声，转换音色，试听并下载。': 'Upload a song or vocal recording, convert the voice, then listen and download.',
  '查看最近生成': 'View recent results',
  '查看进度': 'View progress',
  '导入音频': 'Upload audio',
  '歌曲或干声均可': 'Songs or dry vocals',
  '音频类型': 'Audio type',
  '带伴奏歌曲': 'Song with backing track',
  '先分离人声与伴奏': 'Separate vocals and accompaniment first',
  '纯人声 / 干声': 'Vocals only',
  '直接转换，处理更快': 'Convert directly for faster processing',
  '选择或拖入音频文件': 'Choose or drop an audio file',
  '将音频拖到这里': 'Drop your audio here',
  '选择音频文件': 'Choose an audio file',
  '单个文件最大 80 MB · 最长 10 分钟': 'Up to 80 MB per file · Up to 10 minutes',
  '正在导入…': 'Uploading…',
  '文件上传进度': 'Upload progress',
  '移除': 'Remove',
  '原始音频波形': 'Source audio waveform',
  '原始人声试听': 'Preview source vocals',
  '浏览器暂时无法预览此格式，转换成功后可试听标准 WAV 版本。': 'This browser cannot preview this format. A WAV preview will be available after conversion.',
  '先用示例试一试': 'Try an example',
  '已准备好的干声': 'Prepared dry vocals',
  '男': 'M',
  '女': 'F',
  '男声示例': 'Male vocal',
  '女声示例': 'Female vocal',
  '平凡的一天 · 18.6s': 'An Ordinary Day · 18.6s',
  '男声 · 平凡的一天': 'Male vocal · An Ordinary Day',
  '女声 · Safe and Sound': 'Female vocal · Safe and Sound',
  '目标女声 · 水星记': 'Target voice · Mercury Records',
  '有乐器、伴奏时请选择“带伴奏歌曲”。示例已是干声。': 'Choose “Song with backing track” for audio with instruments. The examples contain vocals only.',
  '目标音色与参数': 'Target voice & settings',
  '正在读取': 'Loading',
  '正在读取…': 'Loading…',
  '选择目标音色': 'Choose a target voice',
  '目标原声试听': 'Original target voice',
  '目标音色原声试听': 'Preview the original target voice',
  '我的音色 · 第二版': 'Personal voice · v2',
  '我的音色': 'Personal voice · v1',
  '清柔女声': 'Soft female voice',
  '6 段录音训练': 'Trained on 6 recordings',
  '个人歌声 · 第一版': 'Personal singing voice · v1',
  '中文女声 · GTSinger': 'Chinese female voice · GTSinger',
  '群青 · 留出的原声片段': 'Gunjō · Held-out original recording',
  '水星记 · 原声片段': 'Mercury Records · Original recording',
  '换声参数': 'Conversion settings',
  '恢复默认': 'Reset',
  '自动适配目标音区': 'Match the target vocal range',
  '分析人声音高，按需升降八度；下方可手动微调': 'Analyse pitch and shift by an octave when needed. Fine-tune below.',
  '音高调整': 'Pitch shift',
  '在自动建议上额外调整': 'Fine-tune the suggested shift',
  '在自动建议上额外调整，最终限制在 ±12 半音': 'Fine-tune the suggested shift, within ±12 semitones',
  '直接指定转换音高，0 为原调': 'Set the pitch shift directly. 0 keeps the original key.',
  '0 半音': '0 semitones',
  '不额外调整': 'No fine-tuning',
  '原调': 'Original key',
  '人声会额外变调，伴奏保持原调；整曲试听时留意是否和谐。': 'The vocals will shift in pitch while the backing track keeps its original key. Check the harmony in the mix.',
  '目标音色融合': 'Target voice blend',
  '越高越偏向目标音色': 'Higher values favour the target voice',
  '静音与起音优化': 'Pause & onset cleanup',
  '柔和降低停顿杂音，保护轻声和人声边界': 'Reduce noise in pauses while preserving quiet vocals and note onsets',
  '高级设置': 'Advanced settings',
  '辅音保护、音量包络': 'Consonant protection and volume envelope',
  '辅音保护': 'Consonant protection',
  '越低保护越强，0.5 关闭': 'Lower values give stronger protection. 0.5 disables it.',
  '音量包络': 'Volume envelope',
  '0 跟随原声，1 使用生成音量': '0 follows source dynamics. 1 uses generated dynamics.',
  '导入一段人声，就可以开始了': 'Upload a vocal recording to get started',
  '导入一段歌曲或人声，即可开始': 'Upload a song or vocal recording to get started',
  '开始换声': 'Convert voice',
  '最近 50 条换声记录保存在本机，可随时试听和下载。': 'Your 50 most recent conversions are saved locally for playback and download.',
  '这里显示此浏览器最近 50 条换声记录，可随时试听或下载。': 'Your 50 most recent conversions from this browser, ready to play or download.',
  '搜索音频名称…': 'Search audio names…',
  '搜索转换记录': 'Search conversions',
  '筛选任务状态': 'Filter by task status',
  '全部状态': 'All statuses',
  '已完成': 'Completed',
  '处理中': 'Processing',
  '未完成': 'Failed',
  '还没有转换记录。': 'No conversions yet.',
  '去工作台试试': 'Try a conversion',
  '没有符合条件的记录，试试其他名称或状态。': 'No matching results. Try another name or status.',
  '显示更多记录': 'Show more',
  '试听转换结果': 'Listen to the result',
  '等待生成': 'Awaiting conversion',
  '转换结果会显示在这里': 'Your result will appear here',
  '完成后可试听、比较原声并下载音频。': 'Listen, compare with the source, and download when the conversion is complete.',
  '正在准备转换': 'Preparing conversion',
  '音频较长时需要更多时间，请保持服务运行。': 'Longer recordings take more time. Keep the service running.',
  '发送音频': 'Send audio',
  '分离伴奏': 'Separate stems',
  '分析音区': 'Analyse pitch',
  '转换人声': 'Convert vocals',
  '合成整曲': 'Mix audio',
  '回传结果': 'Return result',
  '这次转换没有完成': 'This conversion could not be completed',
  '使用相同参数重试': 'Retry with these settings',
  '查看任务日志': 'View task log',
  '转换完成': 'Conversion complete',
  '原始人声': 'Source vocals',
  '结果中的原始人声': 'Source vocals for this result',
  '下载分离人声 WAV': 'Download isolated vocals',
  '目标人声': 'Target vocals',
  '转换结果': 'Converted',
  '转换结果试听': 'Preview converted vocals',
  '人声音量匹配对比': 'Loudness-matched comparison',
  '输入人声 → 1 秒静音 → 转换人声': 'Source vocals → 1 second of silence → Converted vocals',
  '音量匹配对比试听': 'Play the loudness-matched comparison',
  '伴奏与整曲试听': 'Backing track & full mix',
  '原伴奏': 'Original backing track',
  '分离后的伴奏试听': 'Preview the separated backing track',
  '下载伴奏 WAV': 'Download backing track',
  '目标人声 + 原伴奏': 'Target vocals + original backing track',
  '带伴奏换声结果试听': 'Preview the converted full mix',
  '复用此音频与参数': 'Reuse audio & settings',
  '下载换声人声': 'Download vocals',
  '下载带伴奏版': 'Download full mix',
  '下载对比': 'Download comparison',
  '暂无音色': 'No voices available',
  '模型未就绪': 'Model unavailable',
  '已就绪': 'Ready',
  '未附参考录音': 'No reference recording',
  '请求失败，请重试': 'Request failed. Please try again.',
  '服务响应超时，请检查连接后重试': 'The service timed out. Check the connection and try again.',
  '转换时检查时长': 'Duration will be checked during conversion',
  '已恢复默认参数': 'Default settings restored',
  '正在提交…': 'Submitting…',
  '队列已满': 'Queue full',
  '加入转换队列': 'Add to queue',
  '正在导入音频，请稍候': 'Uploading audio. Please wait.',
  '已有 3 个任务，请等待一个任务完成': 'Three tasks are queued. Wait for one to finish.',
  '正在处理其他任务，可继续准备下一段音频': 'Other tasks are processing. You can prepare the next recording.',
  '准备就绪，生成你的目标音色': 'Ready to convert to your target voice',
  '请选择 WAV、MP3、FLAC、M4A 或 OGG 音频文件': 'Choose a WAV, MP3, FLAC, M4A or OGG audio file.',
  '请选择大于 0、小于 80MB 的音频文件': 'Choose a non-empty audio file smaller than 80 MB.',
  '正在检查音频…': 'Checking audio…',
  '音频已导入': 'Audio uploaded',
  '导入失败，请重试': 'Upload failed. Please try again.',
  '连接本地服务失败，请确认工作台正在运行': 'Cannot reach the studio. Check that the service is running.',
  '上传超时，请重试或选择更小的音频': 'Upload timed out. Try again or choose a smaller file.',
  '每次请选择一段音频': 'Choose one audio file at a time.',
  '正在检查本机 CPU': 'Checking local CPU',
  '正在连接 GPU': 'Connecting to GPU',
  'GPU 已连接': 'GPU connected',
  'GPU 未连接': 'GPU unavailable',
  '服务未连接': 'Service unavailable',
  '已分离换声': 'Separated & converted',
  '已优化': 'Cleaned up',
  '分离后的人声': 'Isolated source vocals',
  '日志读取失败': 'Could not load the log',
  '试听': 'Listen',
  '查看': 'View',
  '下载带伴奏结果': 'Download the full mix',
  '下载转换人声': 'Download converted vocals',
  '这条记录使用的音色暂未就绪': 'The voice used in this recording is currently unavailable.',
  '已载入该音频和参数，可调整后重新生成': 'Audio and settings loaded. Adjust them and convert again.',
  '记录详情': 'Result details',
  '我的音色参考': 'Personal voice reference',
  '偏低音区': 'Lower vocal range',
  '中音区': 'Mid vocal range',
  '偏高音区': 'Higher vocal range',
  '有效有声音频不足，保持原调': 'Too little voiced audio for pitch analysis. Keeping the original key.',
  '换声参数格式不正确': 'Invalid conversion settings.',
  '找不到选定的目标音色': 'The selected target voice was not found.',
  '换声参数超出允许范围：': 'Conversion setting out of range: ',
  '音高需要填写整数半音': 'Pitch must be a whole number of semitones.',
  '静音优化开关格式不正确': 'Invalid pause cleanup setting.',
  '不支持的处理选项：': 'Unsupported processing option: ',
  '上次服务关闭时任务中断，请重新转换': 'The previous session ended before this task finished. Please convert again.',
  '本机 CPU 就绪': 'Local CPU ready',
  '本机模型或推理库不完整，请重新配置环境': 'Local models or inference libraries are incomplete. Run environment setup again.',
  '服务器模型、索引或 GPU 尚未就绪': 'Server models, indices or GPU are not ready.',
  '无法连接服务器，请检查网络和 SSH 免密连接': 'Cannot reach the server. Check the network and SSH key authentication.',
  '示例音频不存在': 'Example audio was not found.',
  '请先上传音频或选择示例': 'Upload audio or choose an example first.',
  '上传记录不存在，请重新上传': 'The upload could not be found. Please upload it again.',
  '上传的音频不存在': 'The uploaded audio was not found.',
  '该目标音色暂未就绪': 'This target voice is not ready.',
  '当前已有 3 个任务，请稍后再试': 'Three tasks are already queued. Please try again shortly.',
  '等待转换': 'Queued for conversion',
  '正在解码音频': 'Decoding audio',
  '正在发送音频到 GPU 服务器': 'Sending audio to the GPU server',
  '正在解码音频并准备处理': 'Decoding audio and preparing to process',
  '正在分离人声与伴奏': 'Separating vocals and accompaniment',
  '正在分析人声音区': 'Analysing the vocal range',
  '正在生成目标人声': 'Generating target vocals',
  '正在合成新的人声与原伴奏': 'Mixing converted vocals with the original backing track',
  '正在校验生成的音频': 'Validating generated audio',
  '任务超时，请尝试较短的音频或稍后重试': 'The task timed out. Try a shorter recording or retry later.',
  '服务器连接失败，请检查网络和 SSH 免密连接后重试': 'Cannot connect to the server. Check the network and SSH key authentication, then retry.',
  '音频时长需在 0.2 秒到 10 分钟之间': 'Audio must be between 0.2 seconds and 10 minutes.',
  '音频转换失败，请确认文件可正常播放；详情可查看任务日志': 'Conversion failed. Check that the file plays correctly, or open the task log for details.',
  '请求的工作台地址未配置': 'This studio address is not configured.',
  '不允许来自其他页面的请求': 'Requests from other sites are not allowed.',
  '不允许跨站请求': 'Cross-site requests are not allowed.',
  '请求缺少本地页面标识': 'The request is missing its studio identifier.',
  '需要 JSON 请求': 'A JSON request is required.',
  '请求大小不正确': 'Invalid request size.',
  'JSON 请求格式不正确': 'Invalid JSON request.',
  '请求格式不正确': 'Invalid request format.',
  '文件不存在': 'File not found.',
  '无效的音频范围': 'Invalid audio byte range.',
  '任务不存在': 'Task not found.',
  '音频尚未生成': 'The audio is not ready yet.',
  '页面不存在': 'Page not found.',
  '读取失败，请刷新重试': 'Could not load the data. Refresh and try again.',
  '接口不存在': 'Endpoint not found.',
  '操作失败，请重试': 'The operation failed. Please try again.',
  '文件大小不正确': 'Invalid file size.',
  '请选择小于 80MB 的音频': 'Choose an audio file smaller than 80 MB.',
  '不支持这个文件格式，请使用 WAV、MP3、FLAC、M4A 或 OGG': 'Unsupported format. Use WAV, MP3, FLAC, M4A or OGG.',
  '文件上传不完整，请重试': 'The upload was incomplete. Please try again.',
  '无法读取这个音频，请检查文件是否损坏': 'Cannot read this audio. Check whether the file is damaged.',
  '暂无日志': 'No log entries yet.',
  ' · 40 kHz WAV · 总用时 ': ' · 40 kHz WAV · Total time ',
  ' · 伴奏保持原调': ' · Backing track in its original key',
  ' · 静音优化已开启': ' · Pause cleanup enabled',
  ' · 音频较长时需要更多时间': ' · Longer recordings take more time',
  ' 个任务': ' tasks',
  ' 个任务已完成，可在最近生成中试听': ' tasks completed. Listen in Recent results.',
  ' 半音': ' semitones',
  ' 换声完成，可在最近生成中试听': ' converted. Listen in Recent results.',
  ' 的带伴奏结果': ' — full mix',
  ' 的转换人声': ' — converted vocals',
  ' 秒': ' s',
  ' 轮': ' epochs',
  '下载 ': 'Download ',
  '本地服务连接失败：': 'Cannot reach the studio: ',
  '音区分析：': 'Vocal range analysis: ',
  '正在导入 {percent}%': 'Uploading {percent}%',
  '显示 {shown} / {total} 条': 'Showing {shown} of {total}',
  '{range} · 中位音高 {median} Hz · 建议 {suggestion} 半音 · 本次使用 {applied} 半音': '{range} · Median pitch {median} Hz · Suggested {suggestion} semitones · Applied {applied} semitones',
  '音高 {pitch} 半音 · 音色融合 {blend}%': 'Pitch {pitch} semitones · Voice blend {blend}%',
};

function initialLanguage() {
  const requested = new URLSearchParams(location.search).get('lang');
  if (requested === 'zh' || requested === 'en') return requested;
  try {
    const saved = localStorage.getItem('shengyu-language');
    if (saved === 'zh' || saved === 'en') return saved;
  } catch { /* Storage can be unavailable in restricted browsers. */ }
  return typeof navigator === 'undefined' || navigator.language.startsWith('zh') ? 'zh' : 'en';
}

let language = initialLanguage();

function t(message, values = {}) {
  let text = String(message ?? '');
  if (language === 'en') {
    if (Object.hasOwn(english, text)) {
      text = english[text];
    } else {
      for (const prefix of ['换声参数超出允许范围：', '不支持的处理选项：']) {
        if (text.startsWith(prefix)) text = english[prefix] + text.slice(prefix.length);
      }
      text = text.replace(/^请选择小于 (\d+)MB 的音频$/, 'Choose an audio file smaller than $1 MB.');
    }
  }
  return text.replace(/\{(\w+)\}/g, (match, key) => Object.hasOwn(values, key) ? values[key] : match);
}

function applyStaticLanguage() {
  document.documentElement.lang = language === 'en' ? 'en' : 'zh-CN';
  document.querySelectorAll('[data-i18n]').forEach(element => {
    element.textContent = t(element.dataset.i18n);
  });
  for (const attribute of ['aria-label', 'title', 'placeholder']) {
    document.querySelectorAll('[data-i18n-' + attribute + ']').forEach(element => {
      element.setAttribute(attribute, t(element.getAttribute('data-i18n-' + attribute)));
    });
  }
  document.querySelectorAll('[data-language]').forEach(button => {
    button.setAttribute('aria-pressed', String(button.dataset.language === language));
  });
}

function updatePageLanguage() {
  const isHistory = state.page === 'history';
  document.title = t(isHistory ? '最近生成 · 声屿' : '声屿 · 换声工作台');
  $('pageName').textContent = t(isHistory ? '最近生成' : '声音转换');
  $('resultTitle').textContent = t(isHistory ? '记录详情' : '试听转换结果');
  if (state.executionMode === 'server') {
    $('workspaceLocation').textContent = t('内网工作空间');
    $('storageIntro').textContent = t('免登录，结果保存在服务器。');
    $('historyLocation').textContent = t('这里显示此浏览器最近 50 条换声记录，可随时试听或下载。');
    $('modeIntro').textContent = t('音频由内网服务器处理。');
    $('modeFooter').textContent = t('服务器 GPU 推理');
  }
  if (state.localCPU) {
    $('modeIntro').textContent = t('换声使用本机 CPU。');
    $('modeFooter').textContent = t('音频在本机处理');
  }
}

function setLanguage(next) {
  if (!['zh', 'en'].includes(next)) return;
  language = next;
  try { localStorage.setItem('shengyu-language', language); } catch {}
  const params = new URLSearchParams(location.search);
  params.set('lang', language);
  history.replaceState(null, '', location.pathname + '?' + params + location.hash);
  applyStaticLanguage();
  updatePageLanguage();
  document.querySelectorAll('#voiceSelect option').forEach(option => {
    option.textContent = t(state.models.find(model => model.id === option.value)?.name || option.value);
  });
  updateVoice();
  renderCurrent(state.current);
  renderHistory();
  if (state.source) {
    $('sourceName').textContent = t(state.source.name);
    $('sourceName').title = t(state.source.name);
  }
  $('pageError').textContent = t(state.errorMessage);
  $('toast').textContent = t(state.toastMessage);
  if (state.uploading) {
    const percent = Number($('uploadBar').value);
    $('uploadText').textContent = percent === 100 ? t('正在检查音频…') : t('正在导入 {percent}%', {percent});
  }
  if (state.health) {
    $('connectionText').textContent = t(state.localCPU ? state.health.message : state.health.ready ? 'GPU 已连接' : 'GPU 未连接');
    $('connectionBadge').title = state.health.gpu || t(state.health.message);
  } else {
    $('connectionText').textContent = t(state.healthChecking ? '正在检查环境' : '服务未连接');
  }
}


const $ = id => document.getElementById(id);
const state = {source:null, jobs:[], current:null, uploading:false, submitting:false, health:null, waveSequence:0, historyLimit:6, historyKey:'', polling:false, uploadMode:'song', capabilities:{}, healthChecking:false};
let pollTimer;
let toastTimer;
const activeStates = ['queued','uploading','separating','analyzing','converting','mixing','downloading'];
const legacyVoice = 'gtsinger_zh_alto';
state.models = [];
state.page = null;
state.selection = {workspace:null, history:null};

function selectedVoice() {
  return state.models.find(model => model.id === $('voiceSelect').value);
}
function jobVoiceName(job) {
  const key=job.settings?.model_id||legacyVoice;
  return t(job.model_name||state.models.find(model=>model.id===key)?.name||(key===legacyVoice?t('清柔女声'):key));
}
function updateVoice() {
  const model=selectedVoice();
  const unavailable=state.health?.models?.[model?.id]===false;
  $('voiceStatus').textContent=!model?t('暂无音色'):unavailable?t('模型未就绪'):t('已就绪');
  $('voiceStatus').className='pill'+(model&&!unavailable?' soft-green':'');
  $('voiceDescription').textContent=model?t(model.description)+' · '+model.epochs+t(' 轮'):'';
  $('referenceTitle').textContent=model?.reference_url?t(model.reference_title)+' · '+model.reference_seconds.toFixed(1)+t(' 秒'):t('未附参考录音');
  $('targetPlayer').hidden=!model?.reference_url;
  if(model?.reference_url)audioSrc('targetPlayer',model.reference_url);
  else $('targetPlayer').pause();
  $('autoPitch').disabled=!model?.pitch_analysis;
  if($('autoPitch').disabled)$('autoPitch').checked=false;
  updateSettings();updateAction();
}
$('voiceSelect').addEventListener('change',updateVoice);

function toast(message) {
  state.toastMessage=message; $('toast').textContent=t(message); $('toast').hidden=false;
  clearTimeout(toastTimer); toastTimer=setTimeout(()=>$('toast').hidden=true,4000);
}
function error(message) { state.errorMessage=message; $('pageError').textContent=t(message); $('pageError').hidden=!message; }
async function api(path, options={}) {
  const controller=new AbortController(),timer=setTimeout(()=>controller.abort(),45000);
  try {
    const response=await fetch(path,{...options,signal:controller.signal,headers:{'X-Voice-Studio':'1',...options.headers}});
    const data=await response.json();
    if(!response.ok) throw new Error(data.error||t('请求失败，请重试'));
    return data;
  } catch(e) {if(e.name==='AbortError')throw new Error('服务响应超时，请检查连接后重试');throw e;}
  finally {clearTimeout(timer);}
}
function duration(seconds) {
  if(!Number.isFinite(seconds)) return t('转换时检查时长');
  return `${Math.floor(seconds/60)}:${String(Math.floor(seconds%60)).padStart(2,'0')}`;
}
function settings() { return {model_id:$('voiceSelect').value||legacyVoice,pitch:Number($('pitch').value),index_rate:Number($('indexRate').value),protect:Number($('protect').value),rms_mix_rate:Number($('rmsMix').value),pause_cleanup:$('pauseCleanup').checked,source_type:document.querySelector('input[name="sourceType"]:checked').value,pitch_mode:$('autoPitch').checked?'auto':'manual'}; }
function updateSettings() {
  const values=settings();
  $('pitchValue').textContent=(values.pitch>0?'+':'')+values.pitch+t(' 半音');
  $('indexValue').textContent=Math.round(values.index_rate*100)+'%';
  $('protectValue').textContent=values.protect.toFixed(2);
  $('rmsValue').textContent=values.rms_mix_rate.toFixed(2);
  $('pitchHelp').textContent=values.pitch_mode==='auto'?t('在自动建议上额外调整，最终限制在 ±12 半音'):t('直接指定转换音高，0 为原调');
  $('pitchCenter').textContent=values.pitch_mode==='auto'?t('不额外调整'):t('原调');
  $('pitchNotice').hidden=values.source_type!=='song'||values.pitch%12===0;
}
function setSettings(values) {
  $('pitch').value=values.pitch; $('indexRate').value=values.index_rate;
  $('protect').value=values.protect; $('rmsMix').value=values.rms_mix_rate;
  $('pauseCleanup').checked=values.pause_cleanup!==false;
  $('autoPitch').checked=!$('autoPitch').disabled&&values.pitch_mode!=='manual';
  updateSettings();
}
['pitch','indexRate','protect','rmsMix'].forEach(id=>$(id).addEventListener('input',updateSettings));
$('autoPitch').addEventListener('change',updateSettings);
document.querySelectorAll('[name="sourceType"]').forEach(input=>input.addEventListener('change',()=>{state.uploadMode=input.value;updateSettings();}));
$('resetSettings').addEventListener('click',()=>{setSettings({pitch:0,index_rate:.75,protect:.33,rms_mix_rate:1});toast('已恢复默认参数');});

function updateAction() {
  const active=state.jobs.filter(job=>activeStates.includes(job.status)),full=active.length>=3;
  const voiceUnavailable=$('voiceSelect').disabled||state.health?.models?.[$('voiceSelect').value]===false;
  $('convertButton').disabled=!state.source||state.uploading||state.submitting||full||voiceUnavailable;
  $('convertText').textContent=state.submitting?t('正在提交…'):full?t('队列已满'):active.length?t('加入转换队列'):t('开始换声');
  $('actionHint').textContent=state.uploading?t('正在导入音频，请稍候'):full?t('已有 3 个任务，请等待一个任务完成'):state.source?(active.length?t('正在处理其他任务，可继续准备下一段音频'):t('准备就绪，生成你的目标音色')):t('导入一段歌曲或人声，即可开始');
  $('activeTask').hidden=!active.length;
  const running=active.find(job=>job.status!=='queued')||active[0];
  if(running){$('activeTaskText').textContent=t(running.message)+' · '+t(running.name);$('activeTaskCount').textContent=active.length+t(' 个任务');$('viewActiveTask').onclick=()=>showJob(running,'workspace',true);}
  $('retryButton').disabled=state.submitting||full;
  $('clearSource').disabled=state.uploading;
}
async function drawWaveform(url) {
  const sequence=++state.waveSequence;
  const canvas=$('waveform');
  const ctx=canvas.getContext('2d');
  canvas.width=800; canvas.height=116; ctx.clearRect(0,0,800,116);
  let context;
  try {
    const response=await fetch(url);
    context=new AudioContext();
    const audio=await context.decodeAudioData(await response.arrayBuffer());
    if(sequence!==state.waveSequence) return;
    const samples=audio.getChannelData(0), bars=155;
    const values=Array.from({length:bars},(_,i)=>{
      const start=Math.floor(i*samples.length/bars),end=Math.floor((i+1)*samples.length/bars);
      let sum=0; for(let j=start;j<end;j++) sum+=samples[j]*samples[j];
      return Math.sqrt(sum/Math.max(1,end-start));
    });
    const maximum=Math.max(...values,1e-5);
    values.forEach((value,i)=>{const height=Math.max(3,value/maximum*83);ctx.fillStyle=i%3===0?'#6a9272':'#b3c9a9';ctx.fillRect(i*800/bars,58-height/2,3.2,height);});
  } catch {
    if(sequence===state.waveSequence){ctx.fillStyle='#e2e9dd';ctx.fillRect(0,57,800,2);}
  } finally {if(context) await context.close();}
}
function selectSource(source) {
  state.source=source;
  document.querySelector(`input[name="sourceType"][value="${source.sample_id?'vocals':state.uploadMode}"]`).checked=true;
  $('sourceName').textContent=t(source.name);
  $('sourceMeta').textContent=duration(source.seconds)+(source.sample_rate?' · '+(source.sample_rate/1000)+' kHz':'')+(source.bytes?' · '+(source.bytes/1024/1024).toFixed(1)+' MB':'');
  $('sourcePlayer').src=source.url;
  $('selectedSource').hidden=false; $('dropzone').classList.add('compact');
  document.querySelectorAll('[data-sample]').forEach(el=>el.classList.toggle('selected',el.dataset.sample===source.sample_id));
  $('sourceName').title=t(source.name);
  $('sourcePlaybackNotice').hidden=true;
  error(''); updateAction(); updateSettings(); drawWaveform(source.url);
}
$('sourcePlayer').addEventListener('loadedmetadata',()=>{
  if(state.source&&Number.isFinite($('sourcePlayer').duration)){
    state.source.seconds=$('sourcePlayer').duration;
    $('sourceMeta').textContent=duration(state.source.seconds)+(state.source.bytes?' · '+(state.source.bytes/1024/1024).toFixed(1)+' MB':'');
  }
});
$('sourcePlayer').addEventListener('error',()=>{if(state.source)$('sourcePlaybackNotice').hidden=false;});
$('clearSource').addEventListener('click',()=>{
  state.source=null; state.waveSequence++;
  $('sourcePlayer').pause(); $('sourcePlayer').removeAttribute('src'); $('sourcePlayer').load();
  $('selectedSource').hidden=true; $('dropzone').classList.remove('compact'); $('fileInput').value='';
  document.querySelectorAll('[data-sample]').forEach(el=>el.classList.remove('selected'));updateAction();
});
function uploadFile(file) {
  if(!file||state.uploading) return;
  const extension=file.name.split('.').pop().toLowerCase();
  if(!['wav','mp3','flac','m4a','ogg','aac','wma','opus'].includes(extension)) return error('请选择 WAV、MP3、FLAC、M4A 或 OGG 音频文件');
  if(file.size>80*1024*1024||!file.size) return error('请选择大于 0、小于 80MB 的音频文件');
  state.uploading=true;error('');updateAction();$('uploadProgress').hidden=false;$('uploadBar').value=0;$('uploadText').textContent=t('正在导入…');
  const request=new XMLHttpRequest();
  request.open('POST','/api/uploads'); request.timeout=120000;
  request.setRequestHeader('X-Voice-Studio','1');request.setRequestHeader('X-Filename',encodeURIComponent(file.name));
  request.setRequestHeader('Content-Type','application/octet-stream');
  request.upload.onprogress=event=>{if(event.lengthComputable){const percent=Math.round(event.loaded/event.total*100);$('uploadBar').value=percent;$('uploadText').textContent=percent===100?t('正在检查音频…'):t('正在导入 {percent}%',{percent});}};
  const finish=()=>{state.uploading=false;$('uploadProgress').hidden=true;$('fileInput').value='';updateAction();};
  request.onload=()=>{try{const data=JSON.parse(request.responseText);if(request.status>=400)throw new Error(data.error);selectSource({...data,upload_id:data.id});toast('音频已导入');}catch(e){error(e.message||t('导入失败，请重试'));}finally{finish();}};
  request.onerror=()=>{error('连接本地服务失败，请确认工作台正在运行');finish();};
  request.ontimeout=()=>{error('上传超时，请重试或选择更小的音频');finish();};
  request.send(file);
}
$('fileInput').addEventListener('change',event=>uploadFile(event.target.files[0]));
$('dropzone').addEventListener('keydown',event=>{if(event.key==='Enter'||event.key===' '){event.preventDefault();$('fileInput').click();}});
['dragenter','dragover'].forEach(name=>$('dropzone').addEventListener(name,event=>{event.preventDefault();$('dropzone').classList.add('dragover');}));
['dragleave','drop'].forEach(name=>$('dropzone').addEventListener(name,event=>{event.preventDefault();$('dropzone').classList.remove('dragover');}));
$('dropzone').addEventListener('drop',event=>{if(event.dataTransfer.files.length>1)return error('每次请选择一段音频');uploadFile(event.dataTransfer.files[0]);});

async function health(refresh=false) {
  if(state.healthChecking)return;
  state.healthChecking=true;
  $('refreshConnection').disabled=true;
  $('connectionBadge').className='connection checking';$('connectionText').textContent=state.localCPU?t('正在检查本机 CPU'):t('正在连接 GPU');
  try{
    const data=await api('/api/health'+(refresh?'?refresh=1':''));state.health=data;
    updateVoice();
    $('connectionBadge').className='connection '+(data.ready?'online':'offline');
    $('connectionText').textContent=state.localCPU?t(data.message):(data.ready?t('GPU 已连接'):t('GPU 未连接'));
    $('connectionBadge').title=data.gpu||t(data.message);
    if(refresh)toast(data.message);
  }catch{ $('connectionBadge').className='connection offline';$('connectionText').textContent=t('服务未连接'); }
  finally{$('refreshConnection').disabled=false;state.healthChecking=false;}
}
$('refreshConnection').addEventListener('click',()=>health(true));

function audioSrc(id,url) {
  const audio=$(id);if(audio.getAttribute('src')!==url){audio.pause();audio.src=url;}
}
function renderCurrent(job) {
  const changed=state.current?.id!==job?.id||state.current?.status!==job?.status;
  if(changed)document.querySelectorAll('#completedResult audio').forEach(audio=>audio.pause());
  state.current=job; updateAction();
  $('resultPanel').hidden=state.page==='history'&&!job;
  if(!job){
    $('emptyResult').hidden=false;
    for(const id of ['processingResult','completedResult','failedResult'])$(id).hidden=true;
    $('resultBadge').textContent=t('等待生成');$('resultBadge').className='pill';
    return;
  }
  if(state.page==='history')document.querySelectorAll('.history-row').forEach(row=>row.classList.toggle('selected',row.dataset.job===job.id));
  const isActive=activeStates.includes(job.status),done=job.status==='completed',failed=job.status==='failed';
  $('emptyResult').hidden=true;$('processingResult').hidden=!isActive;$('completedResult').hidden=!done;$('failedResult').hidden=!failed;
  $('resultBadge').textContent=isActive?t('处理中'):done?(job.report.separation?.enabled?t('已分离换声'):job.report.pause_cleanup?.enabled?t('已优化'):t('已完成')):t('未完成');
  $('resultBadge').className='pill'+(done?' soft-green':'');
  if(isActive){
    $('processingMessage').textContent=t(job.message);
    $('processingMeta').textContent=t(job.name)+t(' · 音频较长时需要更多时间');
    const steps=['uploading','separating','analyzing','converting','mixing','downloading'],current=steps.indexOf(job.status);
    document.querySelectorAll('[data-step]').forEach(el=>{const index=steps.indexOf(el.dataset.step);el.hidden=job.settings.source_type!=='song'&&['separating','mixing'].includes(el.dataset.step);el.classList.toggle('current',index===current);el.classList.toggle('done',current>=0&&index<current);});
  }
  if(done){
    $('resultName').textContent=t(job.name)+' → '+jobVoiceName(job);
    $('resultMeta').textContent=duration(job.report.output_seconds)+t(' · 40 kHz WAV · 总用时 ')+job.elapsed_seconds+t(' 秒');
    audioSrc('resultSourcePlayer',job.source_url);audioSrc('resultPlayer',job.result_url);audioSrc('comparisonPlayer',job.comparison_url);
    const separated=Boolean(job.report.separation?.enabled&&job.instrumental_url&&job.mix_url);
    $('resultSourceLabel').textContent=separated?t('分离后的人声'):t('原始人声');
    $('separationResults').hidden=!separated;$('downloadMix').hidden=!separated;$('downloadSource').hidden=!separated;if(separated)$('downloadSource').href=job.source_url+'?download=1';
    if(separated){audioSrc('instrumentalPlayer',job.instrumental_url);audioSrc('mixPlayer',job.mix_url);$('downloadInstrumental').href=job.instrumental_url+'?download=1';$('downloadMix').href=job.mix_url+'?download=1';}
    else{$('instrumentalPlayer').pause();$('mixPlayer').pause();}
    const analysis=job.report.pitch_analysis;
    $('analysisSummary').hidden=!analysis;
    if (analysis) {
      $('analysisSummary').textContent = analysis.available
        ? t('{range} · 中位音高 {median} Hz · 建议 {suggestion} 半音 · 本次使用 {applied} 半音', {
            range: t(analysis.range_label), median: analysis.median_hz,
            suggestion: (analysis.suggested_pitch > 0 ? '+' : '') + analysis.suggested_pitch,
            applied: (analysis.applied_pitch > 0 ? '+' : '') + analysis.applied_pitch,
          })
        : t('音区分析：') + t(analysis.message);
    }
    $('downloadResult').href=job.result_url+'?download=1';$('downloadComparison').href=job.comparison_url+'?download=1';
    const s=job.settings, actualPitch=analysis?.applied_pitch??s.pitch;
    $('resultParams').textContent = t('音高 {pitch} 半音 · 音色融合 {blend}%', {
      pitch: (actualPitch > 0 ? '+' : '') + actualPitch, blend: Math.round(s.index_rate*100),
    }) + (job.report.pause_cleanup?.enabled ? t(' · 静音优化已开启') : '')
       + (separated && actualPitch%12!==0 ? t(' · 伴奏保持原调') : '');
  }
  if(failed)$('failureMessage').textContent=t(job.message);
  if(failed&&changed){$('failureLog').textContent=t('正在读取…');api('/api/jobs/'+job.id+'/log').then(data=>{if(state.current?.id===job.id)$('failureLog').textContent=data.log;}).catch(()=>{if(state.current?.id===job.id)$('failureLog').textContent=t('日志读取失败');});}
}
function showJob(job,page,focus=false) {
  state.selection[page]=job;
  if(state.page!==page)return;
  renderCurrent(job);
  if(focus){
    $('resultHeading').focus({preventScroll:true});
    $('resultHeading').scrollIntoView({behavior:'smooth',block:'start'});
  }
}
function renderHistory() {
  $('historyCount').textContent=state.jobs.length;
  $('historyEmpty').hidden=state.jobs.length>0;
  const query=$('historySearch').value.trim().toLocaleLowerCase(),filter=$('historyFilter').value;
  const matches=state.jobs.filter(job=>job.name.toLocaleLowerCase().includes(query)&&(filter==='all'||(filter==='active'?activeStates.includes(job.status):job.status===filter)));
  $('historyNoMatch').hidden=!state.jobs.length||matches.length>0;
  $('historyMore').hidden=matches.length<=state.historyLimit;
  $('historyShown').textContent=t('显示 {shown} / {total} 条',{shown:Math.min(matches.length,state.historyLimit),total:matches.length});
  const key=JSON.stringify([state.jobs.map(job=>[job.id,job.status,job.updated_at]),query,filter,state.historyLimit,language]);
  if(key===state.historyKey)return;
  state.historyKey=key;
  const container=$('historyList');container.replaceChildren();
  matches.slice(0,state.historyLimit).forEach(job=>{
    const row=document.createElement('div');row.className='history-row';
    row.dataset.job=job.id;row.classList.toggle('selected',job.id===state.selection.history?.id);
    const symbol=document.createElement('span');symbol.className='history-symbol';symbol.innerHTML='<svg><use href="#i-wave"/></svg>';
    const info=document.createElement('div');info.className='history-info';
    const name=document.createElement('strong');name.textContent=t(job.name);name.title=t(job.name);
    const actualPitch=job.report?.pitch_analysis?.applied_pitch??job.settings.pitch;
    const meta=document.createElement('small');meta.textContent=new Date(job.created_at).toLocaleString(language==='en'?'en-HK':'zh-CN',{month:'2-digit',day:'2-digit',hour:'2-digit',minute:'2-digit'})+' · '+jobVoiceName(job)+' · '+(actualPitch>0?'+':'')+actualPitch+t(' 半音');
    info.append(name,meta);
    const badge=document.createElement('span');badge.className='history-state'+(job.status==='failed'?' failed':activeStates.includes(job.status)?' active':'');
    badge.textContent=job.status==='completed'?(job.report.separation?.enabled?t('已分离换声'):job.report.pause_cleanup?.enabled?t('已优化'):t('已完成')):job.status==='failed'?t('未完成'):t('处理中');
    const open=document.createElement('button');open.className='history-open';open.textContent=job.status==='completed'?t('试听'):t('查看');
    open.setAttribute('aria-label',open.textContent+' '+t(job.name)+' '+new Date(job.created_at).toLocaleString(language==='en'?'en-HK':'zh-CN'));
    open.addEventListener('click',()=>showJob(job,'history',true));
    row.append(symbol,info,badge,open);
    if(job.result_url){const link=document.createElement('a');link.className='history-download';link.href=(job.mix_url||job.result_url)+'?download=1';link.setAttribute('download','');link.setAttribute('aria-label',t('下载 ')+t(job.name)+(job.mix_url?t(' 的带伴奏结果'):t(' 的转换人声')));link.title=job.mix_url?t('下载带伴奏结果'):t('下载转换人声');link.innerHTML='<svg><use href="#i-download"/></svg>';row.append(link);}
    container.append(row);
  });
}
async function pollJobs() {
  if(state.polling)return;
  state.polling=true;
  clearTimeout(pollTimer);
  try{
    const data=await api('/api/jobs');
    const finished=data.jobs.filter(job=>job.status==='completed'&&state.jobs.some(old=>old.id===job.id&&activeStates.includes(old.status)));
    state.jobs=data.jobs;renderHistory();updateAction();$('syncNotice').hidden=true;
    if(state.current){const updated=state.jobs.find(item=>item.id===state.current.id);if(updated)showJob(updated,state.page);}
    if(finished.length)toast(finished.length===1?t(finished[0].name)+t(' 换声完成，可在最近生成中试听'):finished.length+t(' 个任务已完成，可在最近生成中试听'));
  }catch{$('syncNotice').hidden=false;}
  finally{state.polling=false;pollTimer=setTimeout(pollJobs,state.jobs.some(job=>activeStates.includes(job.status))?2500:12000);}
}
async function convert(retryJob=null) {
  if(state.submitting||state.uploading||state.jobs.filter(job=>activeStates.includes(job.status)).length>=3)return;
  let payload;
  if(retryJob){payload={settings:retryJob.settings};if(retryJob.input_url.includes('/sample/'))payload.sample_id=retryJob.input_url.split('/').pop();else payload.upload_id=retryJob.input_url.split('/').pop();}
  else {if(!state.source)return;payload={settings:settings()};if(state.source.sample_id)payload.sample_id=state.source.sample_id;else payload.upload_id=state.source.upload_id;}
  const page=state.page;
  state.submitting=true;updateAction();error('');
  try{const job=await api('/api/jobs',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify(payload)});state.jobs.unshift(job);showJob(job,page,true);renderHistory();await pollJobs();}
  catch(e){error(e.message);}
  finally{state.submitting=false;updateAction();}
}
$('convertButton').addEventListener('click',()=>convert());
$('retryButton').addEventListener('click',()=>{if(state.current)convert(state.current);});

async function init() {
  try{
    const data=await api('/api/bootstrap');state.jobs=data.jobs;
    state.capabilities=data.capabilities||{};
    state.localCPU=data.execution?.mode==='cpu';
    state.executionMode=data.execution?.mode||'ssh';
    updatePageLanguage();
    const songOption=document.querySelector('input[name="sourceType"][value="song"]');
    songOption.disabled=!data.capabilities?.separation;
    if(songOption.disabled){state.uploadMode='vocals';document.querySelector('input[name="sourceType"][value="vocals"]').checked=true;}
    state.models=data.models;
    const picker=$('voiceSelect');
    picker.replaceChildren();
    for(const model of state.models){
      const option=document.createElement('option');
      option.value=model.id;option.textContent=t(model.name);picker.append(option);
    }
    picker.disabled=!state.models.length;
    updateVoice();
    document.querySelectorAll('[data-sample]').forEach(button=>{
      const sample=data.samples.find(item=>item.id===button.dataset.sample);
      button.disabled=!sample;
      if(sample)button.addEventListener('click',()=>{if(!state.uploading)selectSource({...sample,sample_id:sample.id});});
    });
    renderHistory();
    if(state.jobs.length){const ongoing=state.jobs.find(job=>activeStates.includes(job.status));showJob(ongoing||state.jobs[0],'workspace');}
    updateSettings();updateAction();health();pollJobs();
  }catch(e){error('本地服务连接失败：'+e.message);}
}
document.addEventListener('play',event=>{document.querySelectorAll('audio').forEach(audio=>{if(audio!==event.target)audio.pause();});},true);
$('historySearch').addEventListener('input',()=>{state.historyLimit=6;renderHistory();});
$('historyFilter').addEventListener('change',()=>{state.historyLimit=6;renderHistory();});
$('historyMore').addEventListener('click',()=>{state.historyLimit+=6;renderHistory();});
$('reuseSource').addEventListener('click',()=>{
  if(!state.current||state.uploading)return;
  const job=state.current;
  const modelId=job.settings.model_id||legacyVoice;
  if(!state.models.some(model=>model.id===modelId))return error('这条记录使用的音色暂未就绪');
  navigate('workspace');
  $('voiceSelect').value=modelId;
  updateVoice();
  state.uploadMode=job.settings.source_type==='song'&&state.capabilities.separation?'song':'vocals';
  const sample=job.input_url.includes('/sample/');
  selectSource({...job.input_info,name:job.name,url:job.input_url,[sample?'sample_id':'upload_id']:job.input_url.split('/').pop()});
  document.querySelector(`input[name="sourceType"][value="${state.uploadMode}"]`).checked=true;
  setSettings({...job.settings,pitch_mode:job.settings.pitch_mode||'manual'});
  $('sourceHeading').scrollIntoView({behavior:'smooth',block:'start'});toast('已载入该音频和参数，可调整后重新生成');
});
const pagePaths={workspace:'/',history:'/history'};
function updateNav(focus=false){
  if(location.hash==='#history'||location.hash==='#workspace'){
    history.replaceState(null,'',pagePaths[location.hash.slice(1)]+location.search);
  }
  const isHistory=location.pathname.replace(/\/$/,'')==='/history';
  const page=isHistory?'history':'workspace';
  if(state.page===page)return;
  document.querySelectorAll('audio').forEach(audio=>audio.pause());
  state.page=page;
  $('workspace').hidden=isHistory;
  $('history').hidden=!isHistory;
  const heading=$(page+'Heading');
  $('pageName').textContent=heading.textContent;
  updatePageLanguage();
  $('resultStep').hidden=isHistory;
  $('resultTitle').textContent=isHistory?t('记录详情'):t('试听转换结果');
  document.querySelectorAll('.nav-item').forEach(link=>{
    const active=link.dataset.page===page;
    link.classList.toggle('active',active);
    if(active)link.setAttribute('aria-current','page');else link.removeAttribute('aria-current');
  });
  const selected=state.selection[page];
  renderCurrent(state.jobs.find(job=>job.id===selected?.id)||selected);
  if(focus){heading.focus({preventScroll:true});window.scrollTo(0,0);}
}
function navigate(page){
  if(state.page===page)return;
  history.pushState(null,'',pagePaths[page]+location.search);
  updateNav(true);
}
document.querySelectorAll('a[data-page]').forEach(link=>link.addEventListener('click',event=>{
  if(event.defaultPrevented||event.button!==0||event.ctrlKey||event.metaKey||event.shiftKey||event.altKey)return;
  event.preventDefault();
  navigate(link.dataset.page);
}));
window.addEventListener('popstate',()=>updateNav(true));
window.addEventListener('hashchange',()=>updateNav(true));
document.addEventListener('visibilitychange',()=>{if(!document.hidden){pollJobs();health();}});
applyStaticLanguage();
document.querySelectorAll('[data-language]').forEach(button=>button.addEventListener('click',()=>setLanguage(button.dataset.language)));
try { localStorage.setItem('shengyu-language',language); } catch {}
updateNav();
updateSettings();init();
