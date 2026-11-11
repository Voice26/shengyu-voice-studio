// UI state regressions without a browser, network, or GPU job.
const {test}=require('node:test');
const assert=require('node:assert/strict');
const vm=require('node:vm');
const fs=require('node:fs');
const code=fs.readFileSync('platform_app/static/app.js','utf8').replace('updateSettings();init();','updateSettings();');
function harness(url='/', browserLanguage='zh-CN', savedLanguage=null){
  const elements=new Map(),radios=[],scheduled=[];
  const location=new URL(url,'http://localhost');
  const history={replaceState(_state,_title,path){location.href=new URL(path,location).href;},
    pushState(_state,_title,path){this.replaceState(null,'',path);}};
  function element(id=''){
    const classes=new Set();
    return {id,value:'',checked:false,disabled:false,hidden:false,textContent:'',dataset:{},children:[],events:{},
      classList:{add:x=>classes.add(x),remove:x=>classes.delete(x),toggle(x,v){v?classes.add(x):classes.delete(x);}},
      setAttribute(k,v){this[k]=v;},getAttribute(k){return this[k];},removeAttribute(k){delete this[k];},
      addEventListener(k,v){this.events[k]=v;},append(...items){this.children.push(...items);},replaceChildren(){this.children=[];},
      pause(){this.paused=true;},load(){},scrollIntoView(){},focus(){},
      getContext(){return {clearRect(){},fillRect(){}};}};
  }
  const get=id=>{if(!elements.has(id))elements.set(id,element(id));return elements.get(id);};
  for(const [id,value] of Object.entries({pitch:'0',indexRate:'.75',protect:'.33',rmsMix:'1',historyFilter:'all'}))get(id).value=value;
  get('autoPitch').checked=get('pauseCleanup').checked=true;
  for(const value of ['song','vocals']){const radio=element();radio.value=value;let checked=value==='song';Object.defineProperty(radio,'checked',{get:()=>checked,set:v=>{if(v)radios.filter(x=>x!==radio).forEach(x=>x.checked=false);checked=v;}});radios.push(radio);}
  const stored=new Map(savedLanguage?[['shengyu-language',savedLanguage]]:[]);
  const context=vm.createContext({document:{hidden:false,documentElement:{lang:'zh-CN'},getElementById:get,createElement:element,addEventListener(){},
    querySelector(sel){return sel.includes(':checked')?radios.find(x=>x.checked):radios.find(x=>sel.includes(`value="${x.value}"`));},
    querySelectorAll(sel){if(sel==='[name="sourceType"]')return radios;if(sel==='#completedResult audio')return [get('resultPlayer'),get('mixPlayer')];if(sel==='.history-row')return get('historyList').children;return [];},},
    window:{addEventListener(){},scrollTo(){}},location,history,setTimeout(fn,ms){scheduled.push(ms);return scheduled.length;},clearTimeout(){},
    navigator:{language:browserLanguage},URLSearchParams,
    localStorage:{getItem:key=>stored.get(key)||null,setItem:(key,value)=>stored.set(key,value)},
    fetch:async()=>{throw new Error('Network disabled in test');},AbortController,console,XMLHttpRequest:class{open(){} setRequestHeader(){} upload={}; send(){context.request=this;}}});
  vm.runInContext(code,context);
  return {run:s=>vm.runInContext(s,context),get,radios,scheduled,context};
}
const job=(id,status)=>({id,status,name:id,created_at:'2026-11-08T00:00:00Z',updated_at:'1',settings:{pitch:0,index_rate:.75},report:{},message:'正在转换',input_url:'/api/audio/sample/male'});

test('explicit language overrides saved and browser preferences on direct history links',()=>{
  const explicit=harness('/history?lang=en','zh-CN','zh');
  assert.equal(explicit.context.document.documentElement.lang,'en');
  assert.equal(explicit.get('pageName').textContent,'Recent results');
  assert.equal(harness('/','en-HK','zh').context.document.documentElement.lang,'zh-CN');
  assert.equal(harness('/','en-HK').context.document.documentElement.lang,'en');
});

test('switching language preserves the selected audio, parameters and history filter',()=>{
  const h=harness();
  h.context.fixture=[job('old','completed')];
  h.run("state.models=[{id:legacyVoice,name:'清柔女声',reference_seconds:1,pitch_analysis:true}];state.jobs=fixture;state.source={name:'个人录音.wav',url:'/draft'};error('文件上传不完整，请重试')");
  h.get('voiceSelect').value='gtsinger_zh_alto';
  h.get('pitch').value='3';
  h.get('historyFilter').value='completed';
  h.run("setLanguage('en')");
  assert.equal(h.get('pitch').value,'3');
  assert.equal(h.get('pitchValue').textContent,'+3 semitones');
  assert.equal(h.get('historyFilter').value,'completed');
  assert.equal(h.run('state.source.url'),'/draft');
  assert.equal(h.get('sourceName').textContent,'个人录音.wav');
  assert.equal(h.get('pageError').textContent,'The upload was incomplete. Please try again.');
  assert.equal(h.get('historyList').children[0].children[3].textContent,'Listen');
  h.run("navigate('history')");
  assert.equal(h.context.location.search,'?lang=en');
  h.run("setLanguage('zh')");
  assert.equal(h.get('pageError').textContent,'文件上传不完整，请重试');
  assert.equal(h.get('historyList').children[0].children[3].textContent,'试听');
});

test('an existing failed result translates when language changes without retrying the task',()=>{
  const h=harness('/history');
  const failed=job('failed','failed');
  failed.message='音频时长需在 0.2 秒到 10 分钟之间';
  h.context.failed=failed;
  h.run("state.jobs=[failed];showJob(failed,'history');setLanguage('en')");
  assert.equal(h.get('failureMessage').textContent,'Audio must be between 0.2 seconds and 10 minutes.');
  assert.equal(h.get('resultBadge').textContent,'Failed');
  assert.equal(h.run('state.jobs[0].status'),'failed');
});
test('direct and bookmarked history links open only the history list',()=>{
  for(const url of ['/history','/history/','/?q=test#history']){
    const h=harness(url);
    assert.equal(h.get('workspace').hidden,true);
    assert.equal(h.get('history').hidden,false);
    assert.equal(h.get('resultPanel').hidden,true);
    assert.equal(h.context.location.hash,'');
    if(url.includes('?'))assert.equal(h.context.location.search,'?q=test');
  }
});
test('history audition keeps the workspace draft and current conversion independent',()=>{
  const h=harness();h.context.fixture=[job('new','converting'),job('old','completed')];
  h.run('state.jobs=fixture;showJob(fixture[0],"workspace");selectSource({name:"Draft",sample_id:"male",url:"/draft"});navigate("history");renderHistory()');
  h.get('pitch').value='3';
  h.get('historyList').children[1].children[3].events.click();
  assert.equal(h.get('workspace').hidden,true);
  assert.equal(h.get('completedResult').hidden,false);
  assert.equal(h.run('state.current.id'),'old');
  h.run('navigate("workspace")');
  assert.equal(h.get('processingResult').hidden,false);
  assert.equal(h.run('state.current.id'),'new');
  assert.equal(h.run('state.source.name'),'Draft');
  assert.equal(h.get('pitch').value,'3');
  h.run('navigate("history")');assert.equal(h.run('state.current.id'),'old');
});
test('reusing an archived job restores its input and settings on the workspace',()=>{
  const h=harness('/history'),saved=job('saved','completed');
  saved.settings={pitch:5,index_rate:.4,protect:.2,rms_mix_rate:.8,source_type:'vocals',pitch_mode:'manual'};
  h.context.saved=saved;
  h.run('state.models=[{id:legacyVoice,reference_seconds:1,pitch_analysis:true}];showJob(saved,"history")');
  h.get('reuseSource').events.click();
  assert.equal(h.context.location.pathname,'/');
  assert.equal(h.get('workspace').hidden,false);
  assert.equal(h.get('history').hidden,true);
  assert.equal(h.run('state.source.sample_id'),'male');
  assert.equal(h.run('settings().pitch'),5);
  assert.equal(h.run('settings().index_rate'),.4);
});
test('target selection changes submission and preview while old results keep their own voice',()=>{
  const h=harness();
  h.context.models=[
    {id:'personal_20261109',name:'我的音色',reference_url:'/personal',reference_seconds:12,pitch_analysis:true},
    {id:'gtsinger_zh_alto',name:'清柔女声',reference_url:'/original',reference_seconds:13.6,pitch_analysis:true}
  ];
  h.run('state.models=models');
  h.get('voiceSelect').value='personal_20261109';h.get('voiceSelect').events.change();
  assert.equal(h.get('targetPlayer').src,'/personal');
  assert.equal(h.run('settings().model_id'),'personal_20261109');
  assert.equal(h.run('jobVoiceName({settings:{}})'),'清柔女声');
  h.get('voiceSelect').value='gtsinger_zh_alto';h.get('voiceSelect').events.change();
  assert.equal(h.get('targetPlayer').src,'/original');
  assert.equal(h.run('jobVoiceName({settings:{model_id:"personal_20261109"}})'),'我的音色');
});
test('browsing an old result does not hide active jobs or bypass full queue',()=>{
  const h=harness();h.context.fixture=[job('one','converting'),job('two','queued'),job('three','queued')];
  h.run('state.jobs=fixture;state.source={};state.current={status:"completed"};updateAction()');
  assert.equal(h.get('activeTask').hidden,false);assert.equal(h.get('convertButton').disabled,true);
  h.run('state.jobs.pop();updateAction()');assert.equal(h.get('convertButton').disabled,false);
  assert.equal(h.get('convertText').textContent,'加入转换队列');
});
test('a dry example does not change the selected mode for future uploaded songs',()=>{
  const h=harness();h.run('selectSource({sample_id:"male",name:"Example",seconds:18,url:"/sample"})');
  assert.equal(h.radios[1].checked,true);
  h.run('selectSource({upload_id:"upload",name:"Song",seconds:24,url:"/upload"})');
  assert.equal(h.radios[0].checked,true);
});
test('failed upload resets the file input so the same file can be retried',()=>{
  const h=harness();h.get('fileInput').value='same.wav';
  h.run('uploadFile({name:"same.wav",size:10})');h.context.request.onerror();
  assert.equal(h.get('fileInput').value,'');assert.equal(h.run('state.uploading'),false);
});
test('switching to a processing task stops hidden result playback',()=>{
  const h=harness();h.context.fixture=job('new','converting');
  h.run('state.current={id:"old",status:"completed"};renderCurrent(fixture)');
  assert.equal(h.get('mixPlayer').paused,true);assert.equal(h.get('completedResult').hidden,true);
});
test('history search, status filtering and pagination operate on retained jobs',()=>{
  const h=harness();h.context.fixture=Array.from({length:10},(_,i)=>job('voice '+i,i<8?'completed':'failed'));
  h.run('state.jobs=fixture;renderHistory()');assert.equal(h.get('historyList').children.length,6);
  h.run('state.historyLimit+=6;renderHistory()');assert.equal(h.get('historyList').children.length,10);
  h.get('historyFilter').value='failed';h.run('renderHistory()');assert.equal(h.get('historyList').children.length,2);
  h.get('historySearch').value='missing';h.run('renderHistory()');assert.equal(h.get('historyNoMatch').hidden,false);
});
test('unchanged polling preserves history controls and their focus',()=>{
  const h=harness();h.context.fixture=[job('same','completed')];h.run('state.jobs=fixture;renderHistory()');
  const original=h.get('historyList').children[0];h.run('renderHistory()');assert.equal(h.get('historyList').children[0],original);
});
test('idle polling continues to discover jobs from other tabs',async()=>{
  const h=harness();h.run('api=async()=>({jobs:[]})');await h.run('pollJobs()');
  assert.equal(h.scheduled.at(-1),12000);assert.equal(h.get('syncNotice').hidden,true);
});
test('completion is announced even while viewing another recording',async()=>{
  const h=harness();h.context.fixture=[job('running','converting')];
  h.run('state.jobs=fixture;api=async()=>({jobs:fixture.map(j=>({...j,status:"completed"}))})');
  await h.run('pollJobs()');assert.match(h.get('toast').textContent,/running.*换声完成/);
});
