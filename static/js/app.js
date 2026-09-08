(function(){
  'use strict';

  // Lightweight, dependency-free SVG charts.  The old page depended on Chart.js
  // from a CDN, so charts disappeared when the CDN was blocked/offline.  SVGs
  // render natively in every supported browser and resize with their card.
  const NS='http://www.w3.org/2000/svg';
  const esc=v=>String(v==null?'':v).replace(/[&<>"']/g,m=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[m]));
  const num=v=>Number(v)||0;
  const niceMax=v=>v<=0?1:Math.ceil(v*1.1);

  function chartShell(el,title){
    el.innerHTML='';
    el.classList.add('svg-chart');
    const svg=document.createElementNS(NS,'svg');
    svg.setAttribute('viewBox','0 0 760 340');
    svg.setAttribute('role','img');
    svg.setAttribute('aria-label',title||'Analytics chart');
    svg.setAttribute('preserveAspectRatio','xMidYMid meet');
    el.appendChild(svg);
    return svg;
  }
  function line(svg,x1,y1,x2,y2,cls){
    const e=document.createElementNS(NS,'line');
    [['x1',x1],['y1',y1],['x2',x2],['y2',y2]].forEach(([k,v])=>e.setAttribute(k,v));
    e.setAttribute('class',cls||'chart-gridline'); svg.appendChild(e); return e;
  }
  function text(svg,x,y,value,cls,anchor='middle'){
    const e=document.createElementNS(NS,'text'); e.setAttribute('x',x); e.setAttribute('y',y);
    e.setAttribute('class',cls||'chart-label'); e.setAttribute('text-anchor',anchor); e.textContent=value; svg.appendChild(e); return e;
  }
  function rect(svg,x,y,w,h,cls){
    const e=document.createElementNS(NS,'rect'); [['x',x],['y',y],['width',Math.max(0,w)],['height',Math.max(0,h)]].forEach(([k,v])=>e.setAttribute(k,v));
    e.setAttribute('class',cls||'chart-bar'); svg.appendChild(e); return e;
  }
  function path(svg,d,cls){const e=document.createElementNS(NS,'path');e.setAttribute('d',d);e.setAttribute('class',cls||'chart-line');svg.appendChild(e);return e;}
  function circle(svg,cx,cy,r,cls){const e=document.createElementNS(NS,'circle');[['cx',cx],['cy',cy],['r',r]].forEach(([k,v])=>e.setAttribute(k,v));e.setAttribute('class',cls||'chart-point');svg.appendChild(e);return e;}

  function axes(svg,max,yLabel){
    const L=58,R=18,T=18,B=58,H=340,W=760, plotH=H-T-B;
    line(svg,L,T,L,H-B,'chart-axis'); line(svg,L,H-B,W-R,H-B,'chart-axis');
    for(let i=0;i<=4;i++){const y=T+plotH*i/4; line(svg,L,y,W-R,y,'chart-gridline'); text(svg,L-10,y+4,String(Math.round(max*(1-i/4))),'chart-y-label','end');}
    if(yLabel) text(svg,14,T+plotH/2,yLabel,'chart-axis-title','middle');
    return {L,R,T,B,H,W,plotH,plotW:W-L-R};
  }

  function barChart(id,labels,values,title,horizontal=false){
    const el=document.getElementById(id); if(!el)return;
    const svg=chartShell(el,title); const a=axes(svg,niceMax(Math.max(...values,0)), '');
    const max=niceMax(Math.max(...values,0));
    if(horizontal){
      // Rebuild as horizontal bars for long feature names.
      svg.innerHTML=''; const L=170,R=25,T=18,B=28,W=760,H=340,ph=H-T-B,pw=W-L-R;
      line(svg,L,T,L,H-B,'chart-axis');
      for(let i=0;i<=4;i++){const x=L+pw*i/4;line(svg,x,T,x,H-B,'chart-gridline');text(svg,x,H-B+18,String(Math.round(max*i/4)),'chart-x-label');}
      const row=ph/Math.max(labels.length,1), bh=Math.min(28,row*.58);
      labels.forEach((lab,i)=>{const y=T+i*row+(row-bh)/2; const w=(num(values[i])/max)*pw; rect(svg,L,y,w,bh,'chart-bar'); text(svg,L-9,y+bh*.68,String(lab).replace(/_/g,' '),'chart-y-label','end'); text(svg,Math.min(L+w+8,W-R),y+bh*.68,num(values[i]).toFixed(3),'chart-value','start');});
    } else {
      const n=Math.max(labels.length,1), slot=a.plotW/n, bw=Math.min(62,slot*.58);
      labels.forEach((lab,i)=>{const v=num(values[i]),x=a.L+i*slot+(slot-bw)/2,h=(v/max)*a.plotH,y=a.T+a.plotH-h;rect(svg,x,y,bw,h,'chart-bar');text(svg,x+bw/2,a.H-a.B+22,String(lab).replace(/_/g,' '),'chart-x-label');text(svg,x+bw/2,Math.max(y-7,12),v.toFixed(v%1?1:0),'chart-value');});
    }
  }

  function lineChart(id,labels,values,title,yMin=0,yMax=null){
    const el=document.getElementById(id); if(!el)return;
    const vals=values.map(num); yMax=yMax==null?niceMax(Math.max(...vals,0)):yMax; yMax=Math.max(yMax,yMin+1);
    const svg=chartShell(el,title); const a=axes(svg,yMax,'');
    // Correct the scale when a non-zero minimum is supplied.
    const n=Math.max(labels.length,1), step=n>1?a.plotW/(n-1):0;
    const pts=vals.map((v,i)=>[a.L+i*step,a.T+a.plotH-(Math.max(yMin,Math.min(yMax,v))-yMin)/(yMax-yMin)*a.plotH]);
    if(pts.length){path(svg,pts.map((p,i)=>(i?'L':'M')+p[0].toFixed(1)+' '+p[1].toFixed(1)).join(' '),'chart-line');pts.forEach((p,i)=>{circle(svg,p[0],p[1],4,'chart-point');text(svg,p[0],a.H-a.B+22,String(labels[i]),'chart-x-label');text(svg,p[0],Math.max(p[1]-9,12),vals[i].toFixed(vals[i]%1?1:0),'chart-value');});}
  }

  function rocChart(id,roc,title){
    const el=document.getElementById(id); if(!el||!roc)return;
    const svg=chartShell(el,title), L=58,R=18,T=18,B=58,W=760,H=340,pw=W-L-R,ph=H-T-B;
    line(svg,L,T,L,H-B,'chart-axis');line(svg,L,H-B,W-R,H-B,'chart-axis');
    for(let i=0;i<=5;i++){const x=L+pw*i/5,y=H-B-ph*i/5;line(svg,x,T,x,H-B,'chart-gridline');line(svg,L,y,W-R,y,'chart-gridline');text(svg,x,H-B+18,(i/5).toFixed(1),'chart-x-label');text(svg,L-10,y+4,(i/5).toFixed(1),'chart-y-label','end');}
    line(svg,L,H-B,W-R,T,'chart-baseline');
    const pts=(roc.fpr||[]).map((x,i)=>[L+num(x)*pw,H-B-num((roc.tpr||[])[i])*ph]);
    if(pts.length>1)path(svg,pts.map((p,i)=>(i?'L':'M')+p[0].toFixed(1)+' '+p[1].toFixed(1)).join(' '),'chart-line');
    text(svg,W/2,H-10,'False Positive Rate','chart-axis-title');
    text(svg,15,H/2,'True Positive Rate','chart-axis-title');
  }

  function makeChart(id,type,labels,data,label){
    if(type==='bar')barChart(id,labels,data,label,false);
    else lineChart(id,labels,data,label);
  }

  if(window.studentTrend)makeChart('studentTrend','line',window.studentTrendLabels.map(x=>x.slice(5,16)),window.studentTrend,'Predicted Score');
  if(window.detailTrend)makeChart('detailTrend','line',window.detailTrendLabels.map(x=>x.slice(5,16)),window.detailTrend,'Predicted Score');
  if(window.teacherTrend)makeChart('teacherTrend','line',window.teacherTrendLabels,window.teacherTrend,'Average Score');
  // Analytics data is embedded as data-* attributes instead of an inline <script>.
  // This is required by the app's Content-Security-Policy, which intentionally blocks inline scripts.
  const analyticsEl=document.getElementById('analyticsData');
  if(analyticsEl){
    const parse=(name,fallback)=>{try{return JSON.parse(analyticsEl.dataset[name]||'null')??fallback}catch(e){console.error('Invalid analytics data:',name,e);return fallback;}};
    const d={
      category:parse('category',{}),
      attendanceLabels:parse('attendanceLabels',[]),
      attendanceValues:parse('attendanceValues',[]),
      parent:parse('parent',{}),
      importance:parse('importance',[]),
      roc:parse('roc',null)
    };
    makeChart('categoryChart','bar',Object.keys(d.category||{}),Object.values(d.category||{}),'Students');
    makeChart('attendanceChart','line',d.attendanceLabels||[],d.attendanceValues||[],'Score');
    makeChart('parentChart','bar',Object.keys(d.parent||{}),Object.values(d.parent||{}),'Score');
    const imp=(d.importance||[]).slice(0,8);
    barChart('importanceChart',imp.map(x=>x.feature),imp.map(x=>x.importance),'Feature Importance',true);
    rocChart('rocChart',d.roc,'At-Risk ROC Curve');
  }

  const search=document.getElementById('studentSearch'), filter=document.getElementById('riskFilter');
  function apply(){if(!search)return;const q=search.value.toLowerCase(),f=filter.value;document.querySelectorAll('#studentTable tbody tr').forEach(r=>{r.hidden=!(r.dataset.search.includes(q)&&(!f||r.dataset.risk===f));});}
  if(search){search.addEventListener('input',apply);filter.addEventListener('change',apply);}

  const chatForm=document.getElementById('chatForm');
  const chatInput=document.getElementById('chatInput');
  const chatMessages=document.getElementById('chatMessages');
  function addChat(text,who){if(!chatMessages)return;const div=document.createElement('div');div.className='chat-bubble '+who;div.textContent=text;chatMessages.appendChild(div);chatMessages.scrollTop=chatMessages.scrollHeight;}
  async function askAssistant(q){if(!q)return;addChat(q,'user');try{const r=await fetch('/api/assistant',{method:'POST',headers:{'Content-Type':'application/json','X-CSRF-Token':document.querySelector('meta[name=csrf-token]')?.content||''},body:JSON.stringify({message:q})});const d=await r.json();addChat(d.answer||d.error||'Unable to answer right now.','bot');}catch(e){addChat('The assistant could not connect. Please try again.','bot');}}
  if(chatForm){chatForm.addEventListener('submit',e=>{e.preventDefault();const q=chatInput.value.trim();chatInput.value='';askAssistant(q);});document.querySelectorAll('[data-question]').forEach(b=>b.addEventListener('click',()=>askAssistant(b.dataset.question)));}
})();
