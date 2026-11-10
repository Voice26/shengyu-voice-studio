'use strict';
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
  return job.model_name||state.models.find(model=>model.id===key)?.name||(key===legacyVoice?'清柔女声':key);
}
function updateVoice() {
  const model=selectedVoice();
  const unavailable=state.health?.models?.[model?.id]===false;
  $('voiceStatus').textContent=!model?'暂无音色':unavailable?'模型未就绪':'已就绪';
  $('voiceStatus').className='pill'+(model&&!unavailable?' soft-green':'');
  $('voiceDescription').textContent=model?model.description+' · '+model.epochs+' 轮':'';
  $('referenceTitle').textContent=model?.reference_url?model.reference_title+' · '+model.reference_seconds.toFixed(1)+' 秒':'未附参考录音';
  $('targetPlayer').hidden=!model?.reference_url;
  if(model?.reference_url)audioSrc('targetPlayer',model.reference_url);
  else $('targetPlayer').pause();
  $('autoPitch').disabled=!model?.pitch_analysis;
  if($('autoPitch').disabled)$('autoPitch').checked=false;
  updateSettings();updateAction();
}
$('voiceSelect').addEventListener('change',updateVoice);

function toast(message) {
  $('toast').textContent=message; $('toast').hidden=false;
  clearTimeout(toastTimer); toastTimer=setTimeout(()=>$('toast').hidden=true,4000);
}
function error(message) { $('pageError').textContent=message; $('pageError').hidden=!message; }
async function api(path, options={}) {
  const controller=new AbortController(),timer=setTimeout(()=>controller.abort(),45000);
  try {
    const response=await fetch(path,{...options,signal:controller.signal,headers:{'X-Voice-Studio':'1',...options.headers}});
    const data=await response.json();
    if(!response.ok) throw new Error(data.error||'请求失败，请重试');
    return data;
  } catch(e) {if(e.name==='AbortError')throw new Error('服务响应超时，请检查连接后重试');throw e;}
  finally {clearTimeout(timer);}
}
function duration(seconds) {
  if(!Number.isFinite(seconds)) return '转换时检查时长';
  return `${Math.floor(seconds/60)}:${String(Math.floor(seconds%60)).padStart(2,'0')}`;
}
function settings() { return {model_id:$('voiceSelect').value||legacyVoice,pitch:Number($('pitch').value),index_rate:Number($('indexRate').value),protect:Number($('protect').value),rms_mix_rate:Number($('rmsMix').value),pause_cleanup:$('pauseCleanup').checked,source_type:document.querySelector('input[name="sourceType"]:checked').value,pitch_mode:$('autoPitch').checked?'auto':'manual'}; }
function updateSettings() {
  const values=settings();
  $('pitchValue').textContent=(values.pitch>0?'+':'')+values.pitch+' 半音';
  $('indexValue').textContent=Math.round(values.index_rate*100)+'%';
  $('protectValue').textContent=values.protect.toFixed(2);
  $('rmsValue').textContent=values.rms_mix_rate.toFixed(2);
  $('pitchHelp').textContent=values.pitch_mode==='auto'?'在自动建议上额外调整，最终限制在 ±12 半音':'直接指定转换音高，0 为原调';
  $('pitchCenter').textContent=values.pitch_mode==='auto'?'不额外调整':'原调';
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
  $('convertText').textContent=state.submitting?'正在提交…':full?'队列已满':active.length?'加入转换队列':'开始换声';
  $('actionHint').textContent=state.uploading?'正在导入音频，请稍候':full?'已有 3 个任务，请等待一个任务完成':state.source?(active.length?'正在处理其他任务，可继续准备下一段音频':'准备就绪，生成你的目标音色'):'导入一段歌曲或人声，即可开始';
  $('activeTask').hidden=!active.length;
  const running=active.find(job=>job.status!=='queued')||active[0];
  if(running){$('activeTaskText').textContent=running.message+' · '+running.name;$('activeTaskCount').textContent=active.length+' 个任务';$('viewActiveTask').onclick=()=>showJob(running,'workspace',true);}
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
  $('sourceName').textContent=source.name;
  $('sourceMeta').textContent=duration(source.seconds)+(source.sample_rate?' · '+(source.sample_rate/1000)+' kHz':'')+(source.bytes?' · '+(source.bytes/1024/1024).toFixed(1)+' MB':'');
  $('sourcePlayer').src=source.url;
  $('selectedSource').hidden=false; $('dropzone').classList.add('compact');
  document.querySelectorAll('[data-sample]').forEach(el=>el.classList.toggle('selected',el.dataset.sample===source.sample_id));
  $('sourceName').title=source.name;
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
  state.uploading=true;error('');updateAction();$('uploadProgress').hidden=false;$('uploadBar').value=0;$('uploadText').textContent='正在导入…';
  const request=new XMLHttpRequest();
  request.open('POST','/api/uploads'); request.timeout=120000;
  request.setRequestHeader('X-Voice-Studio','1');request.setRequestHeader('X-Filename',encodeURIComponent(file.name));
  request.setRequestHeader('Content-Type','application/octet-stream');
  request.upload.onprogress=event=>{if(event.lengthComputable){const percent=Math.round(event.loaded/event.total*100);$('uploadBar').value=percent;$('uploadText').textContent=percent===100?'正在检查音频…':`正在导入 ${percent}%`;}};
  const finish=()=>{state.uploading=false;$('uploadProgress').hidden=true;$('fileInput').value='';updateAction();};
  request.onload=()=>{try{const data=JSON.parse(request.responseText);if(request.status>=400)throw new Error(data.error);selectSource({...data,upload_id:data.id});toast('音频已导入');}catch(e){error(e.message||'导入失败，请重试');}finally{finish();}};
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
  $('connectionBadge').className='connection checking';$('connectionText').textContent='正在连接 GPU';
  try{
    const data=await api('/api/health'+(refresh?'?refresh=1':''));state.health=data;
    updateVoice();
    $('connectionBadge').className='connection '+(data.ready?'online':'offline');
    $('connectionText').textContent=data.ready?'GPU 已连接':'GPU 未连接';
    $('connectionBadge').title=data.ready?data.gpu:data.message;
    if(refresh)toast(data.message);
  }catch{ $('connectionBadge').className='connection offline';$('connectionText').textContent='服务未连接'; }
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
    $('resultBadge').textContent='等待生成';$('resultBadge').className='pill';
    return;
  }
  if(state.page==='history')document.querySelectorAll('.history-row').forEach(row=>row.classList.toggle('selected',row.dataset.job===job.id));
  const isActive=activeStates.includes(job.status),done=job.status==='completed',failed=job.status==='failed';
  $('emptyResult').hidden=true;$('processingResult').hidden=!isActive;$('completedResult').hidden=!done;$('failedResult').hidden=!failed;
  $('resultBadge').textContent=isActive?'处理中':done?(job.report.separation?.enabled?'已分离换声':job.report.pause_cleanup?.enabled?'已优化':'已完成'):'未完成';
  $('resultBadge').className='pill'+(done?' soft-green':'');
  if(isActive){
    $('processingMessage').textContent=job.message;
    $('processingMeta').textContent=job.name+' · 音频较长时需要更多时间';
    const steps=['uploading','separating','analyzing','converting','mixing','downloading'],current=steps.indexOf(job.status);
    document.querySelectorAll('[data-step]').forEach(el=>{const index=steps.indexOf(el.dataset.step);el.hidden=job.settings.source_type!=='song'&&['separating','mixing'].includes(el.dataset.step);el.classList.toggle('current',index===current);el.classList.toggle('done',current>=0&&index<current);});
  }
  if(done){
    $('resultName').textContent=job.name+' → '+jobVoiceName(job);
    $('resultMeta').textContent=duration(job.report.output_seconds)+' · 40 kHz WAV · 总用时 '+job.elapsed_seconds+' 秒';
    audioSrc('resultSourcePlayer',job.source_url);audioSrc('resultPlayer',job.result_url);audioSrc('comparisonPlayer',job.comparison_url);
    const separated=Boolean(job.report.separation?.enabled&&job.instrumental_url&&job.mix_url);
    $('resultSourceLabel').textContent=separated?'分离后的人声':'原始人声';
    $('separationResults').hidden=!separated;$('downloadMix').hidden=!separated;$('downloadSource').hidden=!separated;if(separated)$('downloadSource').href=job.source_url+'?download=1';
    if(separated){audioSrc('instrumentalPlayer',job.instrumental_url);audioSrc('mixPlayer',job.mix_url);$('downloadInstrumental').href=job.instrumental_url+'?download=1';$('downloadMix').href=job.mix_url+'?download=1';}
    else{$('instrumentalPlayer').pause();$('mixPlayer').pause();}
    const analysis=job.report.pitch_analysis;
    $('analysisSummary').hidden=!analysis;
    if(analysis){$('analysisSummary').textContent=analysis.available?`${analysis.range_label} · 中位音高 ${analysis.median_hz} Hz · 建议 ${analysis.suggested_pitch>0?'+':''}${analysis.suggested_pitch} 半音 · 本次使用 ${analysis.applied_pitch>0?'+':''}${analysis.applied_pitch} 半音`:'音区分析：'+analysis.message;}
    $('downloadResult').href=job.result_url+'?download=1';$('downloadComparison').href=job.comparison_url+'?download=1';
    const s=job.settings,actualPitch=analysis?.applied_pitch??s.pitch;$('resultParams').textContent=`音高 ${actualPitch>0?'+':''}${actualPitch} 半音 · 音色融合 ${Math.round(s.index_rate*100)}%`+(job.report.pause_cleanup?.enabled?' · 静音优化已开启':'')+(separated&&actualPitch%12!==0?' · 伴奏保持原调':'');
  }
  if(failed&&changed){$('failureMessage').textContent=job.message;$('failureLog').textContent='正在读取…';api('/api/jobs/'+job.id+'/log').then(data=>{if(state.current?.id===job.id)$('failureLog').textContent=data.log;}).catch(()=>{if(state.current?.id===job.id)$('failureLog').textContent='日志读取失败';});}
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
  $('historyShown').textContent=`显示 ${Math.min(matches.length,state.historyLimit)} / ${matches.length} 条`;
  const key=JSON.stringify([state.jobs.map(job=>[job.id,job.status,job.updated_at]),query,filter,state.historyLimit]);
  if(key===state.historyKey)return;
  state.historyKey=key;
  const container=$('historyList');container.replaceChildren();
  matches.slice(0,state.historyLimit).forEach(job=>{
    const row=document.createElement('div');row.className='history-row';
    row.dataset.job=job.id;row.classList.toggle('selected',job.id===state.selection.history?.id);
    const symbol=document.createElement('span');symbol.className='history-symbol';symbol.innerHTML='<svg><use href="#i-wave"/></svg>';
    const info=document.createElement('div');info.className='history-info';
    const name=document.createElement('strong');name.textContent=job.name;name.title=job.name;
    const actualPitch=job.report?.pitch_analysis?.applied_pitch??job.settings.pitch;
    const meta=document.createElement('small');meta.textContent=new Date(job.created_at).toLocaleString('zh-CN',{month:'2-digit',day:'2-digit',hour:'2-digit',minute:'2-digit'})+' · '+jobVoiceName(job)+' · '+(actualPitch>0?'+':'')+actualPitch+' 半音';
    info.append(name,meta);
    const badge=document.createElement('span');badge.className='history-state'+(job.status==='failed'?' failed':activeStates.includes(job.status)?' active':'');
    badge.textContent=job.status==='completed'?(job.report.separation?.enabled?'已分离换声':job.report.pause_cleanup?.enabled?'已优化':'已完成'):job.status==='failed'?'未完成':'处理中';
    const open=document.createElement('button');open.className='history-open';open.textContent=job.status==='completed'?'试听':'查看';
    open.setAttribute('aria-label',open.textContent+' '+job.name+' '+new Date(job.created_at).toLocaleString('zh-CN'));
    open.addEventListener('click',()=>showJob(job,'history',true));
    row.append(symbol,info,badge,open);
    if(job.result_url){const link=document.createElement('a');link.className='history-download';link.href=(job.mix_url||job.result_url)+'?download=1';link.setAttribute('download','');link.setAttribute('aria-label','下载 '+job.name+(job.mix_url?' 的带伴奏结果':' 的转换人声'));link.title=job.mix_url?'下载带伴奏结果':'下载转换人声';link.innerHTML='<svg><use href="#i-download"/></svg>';row.append(link);}
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
    if(finished.length)toast(finished.length===1?finished[0].name+' 换声完成，可在最近生成中试听':finished.length+' 个任务已完成，可在最近生成中试听');
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
    const songOption=document.querySelector('input[name="sourceType"][value="song"]');
    songOption.disabled=!data.capabilities?.separation;
    if(songOption.disabled){state.uploadMode='vocals';document.querySelector('input[name="sourceType"][value="vocals"]').checked=true;}
    state.models=data.models;
    const picker=$('voiceSelect');
    picker.replaceChildren();
    for(const model of state.models){
      const option=document.createElement('option');
      option.value=model.id;option.textContent=model.name;picker.append(option);
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
  document.title=isHistory?'最近生成 · 声屿':'声屿 · 本地换声工作台';
  $('resultStep').hidden=isHistory;
  $('resultTitle').textContent=isHistory?'记录详情':'试听转换结果';
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
  history.pushState(null,'',pagePaths[page]);
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
updateNav();
updateSettings();init();
