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
  function path(svg,d,cls){
    const e=document.createElementNS(NS,'path');
    e.setAttribute('d',d);
    e.setAttribute('class',cls||'chart-line');
    svg.appendChild(e);
    if(cls==='chart-line'||!cls){
      try {
        const len=e.getTotalLength?e.getTotalLength():1200;
        if(len>0){
          e.style.strokeDasharray=len;
          e.style.strokeDashoffset=len;
          e.style.transition='stroke-dashoffset 1.1s cubic-bezier(0.16, 1, 0.3, 1)';
          requestAnimationFrame(()=>{
            requestAnimationFrame(()=>{
              e.style.strokeDashoffset='0';
            });
          });
        }
      }catch(err){}
    }
    return e;
  }
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
      labels.forEach((lab,i)=>{
        const y=T+i*row+(row-bh)/2; const w=(num(values[i])/max)*pw;
        const b=rect(svg,L,y,w,bh,'chart-bar');
        b.style.opacity='0'; b.style.transform='translateX(-12px)';
        b.style.transition=`opacity 0.4s ease ${i*45}ms, transform 0.4s cubic-bezier(0.16,1,0.3,1) ${i*45}ms`;
        text(svg,L-9,y+bh*.68,String(lab).replace(/_/g,' '),'chart-y-label','end');
        text(svg,Math.min(L+w+8,W-R),y+bh*.68,num(values[i]).toFixed(3),'chart-value','start');
        requestAnimationFrame(()=>{ requestAnimationFrame(()=>{ b.style.opacity='1'; b.style.transform='translateX(0)'; }); });
      });
    } else {
      const n=Math.max(labels.length,1), slot=a.plotW/n, bw=Math.min(62,slot*.58);
      labels.forEach((lab,i)=>{
        const v=num(values[i]),x=a.L+i*slot+(slot-bw)/2,h=(v/max)*a.plotH,y=a.T+a.plotH-h;
        const b=rect(svg,x,y,bw,h,'chart-bar');
        b.style.opacity='0'; b.style.transform='translateY(16px)';
        b.style.transition=`opacity 0.45s ease ${i*45}ms, transform 0.45s cubic-bezier(0.16,1,0.3,1) ${i*45}ms`;
        text(svg,x+bw/2,a.H-a.B+22,String(lab).replace(/_/g,' '),'chart-x-label');
        text(svg,x+bw/2,Math.max(y-7,12),v.toFixed(v%1?1:0),'chart-value');
        requestAnimationFrame(()=>{ requestAnimationFrame(()=>{ b.style.opacity='1'; b.style.transform='translateY(0)'; }); });
      });
    }
  }

  function lineChart(id,labels,values,title,yMin=0,yMax=null){
    const el=document.getElementById(id); if(!el)return;
    const vals=values.map(num); yMax=yMax==null?niceMax(Math.max(...vals,0)):yMax; yMax=Math.max(yMax,yMin+1);
    const svg=chartShell(el,title); const a=axes(svg,yMax,'');
    // Correct the scale when a non-zero minimum is supplied.
    const n=Math.max(labels.length,1), step=n>1?a.plotW/(n-1):0;
    const pts=vals.map((v,i)=>[a.L+i*step,a.T+a.plotH-(Math.max(yMin,Math.min(yMax,v))-yMin)/(yMax-yMin)*a.plotH]);
    if(pts.length){
      path(svg,pts.map((p,i)=>(i?'L':'M')+p[0].toFixed(1)+' '+p[1].toFixed(1)).join(' '),'chart-line');
      pts.forEach((p,i)=>{
        const pt=circle(svg,p[0],p[1],4,'chart-point');
        pt.style.opacity='0';
        pt.style.transition=`opacity 0.3s ease ${350 + i * 45}ms`;
        requestAnimationFrame(()=>{ requestAnimationFrame(()=>{ pt.style.opacity='1'; }); });
        text(svg,p[0],a.H-a.B+22,String(labels[i]),'chart-x-label');
        text(svg,p[0],Math.max(p[1]-9,12),vals[i].toFixed(vals[i]%1?1:0),'chart-value');
      });
    }
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

  // =======================================================
  // INTELLIGENT AI ASSISTANT CONTROLLER
  // =======================================================
  const chatForm = document.getElementById('chatForm');
  const chatInput = document.getElementById('chatInput');
  const chatMessages = document.getElementById('chatMessages');
  let typingBubble = null;

  function renderMarkdown(text) {
    if (!text) return '';
    let html = text
      .replace(/&/g, '&amp;')
      .replace(/</g, '&lt;')
      .replace(/>/g, '&gt;');
    
    // Blockquote
    html = html.replace(/^&gt;\s+(.+)$/gm, '<blockquote class="chat-quote">$1</blockquote>');
    
    // Code blocks
    html = html.replace(/```([a-z]*)\n([\s\S]*?)```/g, (m, lang, code) => {
      return `<pre><code>${code.trim()}</code></pre>`;
    });

    // Inline code
    html = html.replace(/`([^`]+)`/g, '<code class="chat-code">$1</code>');

    // Headers
    html = html.replace(/^###\s+(.+)$/gm, '<h3>$1</h3>');
    html = html.replace(/^####\s+(.+)$/gm, '<h4>$1</h4>');

    // Markdown tables (| col | col |)
    const lines = html.split('\n');
    let inTable = false;
    let tableHtml = '';
    const newLines = [];

    for (let i = 0; i < lines.length; i++) {
      const line = lines[i].trim();
      if (line.startsWith('|') && line.endsWith('|')) {
        const cells = line.slice(1, -1).split('|').map(c => c.trim());
        if (cells.every(c => /^:?-+:?$/.test(c))) {
          continue;
        }
        if (!inTable) {
          inTable = true;
          tableHtml = '<div class="chat-table-wrapper"><table class="chat-table"><thead><tr>';
          cells.forEach(c => { tableHtml += `<th>${c}</th>`; });
          tableHtml += '</tr></thead><tbody>';
        } else {
          tableHtml += '<tr>';
          cells.forEach(c => { tableHtml += `<td>${c}</td>`; });
          tableHtml += '</tr>';
        }
      } else {
        if (inTable) {
          inTable = false;
          tableHtml += '</tbody></table></div>';
          newLines.push(tableHtml);
          tableHtml = '';
        }
        newLines.push(lines[i]);
      }
    }
    if (inTable) {
      tableHtml += '</tbody></table></div>';
      newLines.push(tableHtml);
    }
    html = newLines.join('\n');

    // Unordered list items
    html = html.replace(/^[\s]*[•\-]\s+(.+)$/gm, '<li>$1</li>');
    html = html.replace(/(<li>.*<\/li>)/s, '<ul>$1</ul>');

    // Bold & Italic
    html = html.replace(/\*\*([^*]+)\*\*/g, '<strong>$1</strong>');
    html = html.replace(/\*([^*]+)\*/g, '<em>$1</em>');

    // Paragraph wrapping
    html = html.replace(/\n{2,}/g, '</p><p>');
    html = '<p>' + html + '</p>';
    html = html
      .replace(/<p><\/p>/g, '')
      .replace(/<p>(<h3>.*?<\/h3>)<\/p>/g, '$1')
      .replace(/<p>(<h4>.*?<\/h4>)<\/p>/g, '$1')
      .replace(/<p>(<div class="chat-table-wrapper">.*?<\/div>)<\/p>/g, '$1')
      .replace(/<p>(<pre>.*?<\/pre>)<\/p>/g, '$1')
      .replace(/<p>(<blockquote.*?<\/blockquote>)<\/p>/g, '$1')
      .replace(/<p>(<ul>.*?<\/ul>)<\/p>/g, '$1');

    return html;
  }

  function showTyping() {
    if (typingBubble || !chatMessages) return;
    typingBubble = document.createElement('div');
    typingBubble.className = 'chat-typing';
    typingBubble.innerHTML = '<span></span><span></span><span></span>';
    chatMessages.appendChild(typingBubble);
    chatMessages.scrollTop = chatMessages.scrollHeight;
  }

  function hideTyping() {
    if (typingBubble && typingBubble.parentNode) {
      typingBubble.parentNode.removeChild(typingBubble);
    }
    typingBubble = null;
  }

  function updateSuggestions(suggestions) {
    const cont = document.getElementById('chatSuggestions');
    if (!cont || !Array.isArray(suggestions) || suggestions.length === 0) return;
    cont.innerHTML = '';
    suggestions.forEach(q => {
      const btn = document.createElement('button');
      btn.type = 'button';
      btn.dataset.question = q;
      btn.innerHTML = `<span>💬</span> ${q}`;
      btn.addEventListener('click', () => askAssistant(q));
      cont.appendChild(btn);
    });
  }

  function addChat(text, who) {
    if (!chatMessages) return;
    const div = document.createElement('div');
    div.className = 'chat-bubble ' + who;
    if (who === 'user') {
      div.textContent = text;
    } else {
      div.innerHTML = renderMarkdown(text);
    }
    chatMessages.appendChild(div);
    chatMessages.scrollTop = chatMessages.scrollHeight;
  }

  async function askAssistant(q) {
    if (!q) return;
    addChat(q, 'user');
    showTyping();
    try {
      const r = await fetch('/api/assistant', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'X-CSRF-Token': document.querySelector('meta[name=csrf-token]')?.content || ''
        },
        body: JSON.stringify({ message: q })
      });
      const d = await r.json();
      hideTyping();
      addChat(d.answer || d.error || 'Unable to answer right now.', 'bot');
      if (d.suggestions && d.suggestions.length > 0) {
        updateSuggestions(d.suggestions);
      }
    } catch (e) {
      hideTyping();
      addChat('The assistant could not connect. Please try again.', 'bot');
    }
  }

  if (chatForm) {
    chatForm.addEventListener('submit', e => {
      e.preventDefault();
      const q = chatInput.value.trim();
      chatInput.value = '';
      askAssistant(q);
    });
    document.querySelectorAll('[data-question]').forEach(b => {
      b.addEventListener('click', () => askAssistant(b.dataset.question));
    });
  }

  // =======================================================
  // REAL-TIME WHAT-IF SIMULATION STUDIO CONTROLLER
  // =======================================================
  function initWhatIfSimulator() {
    const liveView = document.getElementById('liveStudioView');
    if (!liveView) return;

    const tabLiveBtn = document.getElementById('tabLiveBtn');
    const tabFormBtn = document.getElementById('tabFormBtn');
    const standardView = document.getElementById('standardFormView');

    if (tabLiveBtn && tabFormBtn && standardView) {
      tabLiveBtn.addEventListener('click', () => {
        tabLiveBtn.classList.add('active');
        tabFormBtn.classList.remove('active');
        liveView.style.display = 'block';
        standardView.style.display = 'none';
      });
      tabFormBtn.addEventListener('click', () => {
        tabFormBtn.classList.add('active');
        tabLiveBtn.classList.remove('active');
        liveView.style.display = 'none';
        standardView.style.display = 'block';
      });
    }

    // Inputs & Sliders
    const sAtt = document.getElementById('slideAttendance');
    const sStu = document.getElementById('slideStudy');
    const sExm = document.getElementById('slideExam');
    const sAsg = document.getElementById('slideAssignment');
    const sInt = document.getElementById('slideInternal');
    const sSlp = document.getElementById('slideSleep');
    const chkExtra = document.getElementById('chkExtracurricular');
    const lblExtra = document.getElementById('lblExtracurricular');
    const parentalBtns = document.querySelectorAll('#parentalGroup .segmented-btn');

    // Badges
    const vAtt = document.getElementById('valAttendance');
    const vStu = document.getElementById('valStudy');
    const vExm = document.getElementById('valExam');
    const vAsg = document.getElementById('valAssignment');
    const vInt = document.getElementById('valInternal');
    const vSlp = document.getElementById('valSleep');

    // Outputs
    const needle = document.getElementById('gaugeNeedleGroup');
    const scoreVal = document.getElementById('simScoreVal');
    const catBadge = document.getElementById('simCategoryBadge');
    const riskBanner = document.getElementById('simRiskBanner');
    const riskIcon = document.getElementById('simRiskIcon');
    const riskTitle = document.getElementById('simRiskTitle');
    const riskPct = document.getElementById('simRiskPct');
    const profileSpan = document.getElementById('simProfile');
    const anomalySpan = document.getElementById('simAnomaly');
    const attrList = document.getElementById('simAttrList');
    const scenariosList = document.getElementById('simScenarios');
    const recsList = document.getElementById('simRecs');

    let currentParental = 1;

    parentalBtns.forEach(btn => {
      btn.addEventListener('click', () => {
        parentalBtns.forEach(b => b.classList.remove('active'));
        btn.classList.add('active');
        currentParental = parseInt(btn.dataset.val, 10);
        triggerSimulation();
      });
    });

    if (chkExtra) {
      chkExtra.addEventListener('change', () => {
        if (lblExtra) lblExtra.textContent = chkExtra.checked ? 'Active' : 'None';
        triggerSimulation();
      });
    }

    // Preset configurations
    const presets = {
      balanced: { attendance: 85, study: 16, exam: 72, assignment: 70, internal: 70, sleep: 7.5, parental: 1, extra: true },
      achiever: { attendance: 96, study: 26, exam: 90, assignment: 92, internal: 88, sleep: 8.0, parental: 2, extra: true },
      cliff: { attendance: 68, study: 6, exam: 48, assignment: 50, internal: 46, sleep: 5.5, parental: 0, extra: false },
      remedial: { attendance: 82, study: 18, exam: 65, assignment: 72, internal: 66, sleep: 7.5, parental: 1, extra: true }
    };

    document.querySelectorAll('.preset-pill').forEach(pill => {
      pill.addEventListener('click', () => {
        document.querySelectorAll('.preset-pill').forEach(p => p.classList.remove('active'));
        pill.classList.add('active');
        const p = presets[pill.dataset.preset];
        if (p) applyPreset(p);
      });
    });

    function applyPreset(p) {
      if (sAtt) sAtt.value = p.attendance;
      if (sStu) sStu.value = p.study;
      if (sExm) sExm.value = p.exam;
      if (sAsg) sAsg.value = p.assignment;
      if (sInt) sInt.value = p.internal;
      if (sSlp) sSlp.value = p.sleep;
      if (chkExtra) {
        chkExtra.checked = p.extra;
        if (lblExtra) lblExtra.textContent = p.extra ? 'Active' : 'None';
      }
      currentParental = p.parental;
      parentalBtns.forEach(b => {
        b.classList.toggle('active', parseInt(b.dataset.val, 10) === currentParental);
      });
      updateBadges();
      triggerSimulation();
    }

    function updateBadges() {
      if (vAtt && sAtt) {
        const val = parseFloat(sAtt.value);
        vAtt.textContent = val + '%';
        vAtt.classList.toggle('cliff-warn', val < 75);
      }
      if (vStu && sStu) vStu.textContent = sStu.value + ' hrs';
      if (vExm && sExm) vExm.textContent = sExm.value + ' / 100';
      if (vAsg && sAsg) vAsg.textContent = sAsg.value + ' / 100';
      if (vInt && sInt) vInt.textContent = sInt.value + ' / 100';
      if (vSlp && sSlp) vSlp.textContent = sSlp.value + ' hrs';
    }

    [sAtt, sStu, sExm, sAsg, sInt, sSlp].forEach(slider => {
      if (!slider) return;
      const handleSliderChange = () => {
        updateBadges();
        triggerSimulation();
      };
      slider.addEventListener('input', handleSliderChange);
      slider.addEventListener('change', handleSliderChange);
    });

    let simTimer = null;
    let currentAbort = null;
    function triggerSimulation() {
      clearTimeout(simTimer);
      simTimer = setTimeout(runSimulation, 40);
    }

    const csrf = document.querySelector('meta[name="csrf-token"]')?.content || '';

    async function runSimulation() {
      if (currentAbort) {
        try { currentAbort.abort(); } catch (_) {}
      }
      currentAbort = new AbortController();

      const payload = {
        attendance_percentage: parseFloat(sAtt?.value || 85),
        study_hours_per_week: parseFloat(sStu?.value || 16),
        previous_exam_score: parseFloat(sExm?.value || 72),
        assignment_score: parseFloat(sAsg?.value || 70),
        internal_assessment_score: parseFloat(sInt?.value || 70),
        sleep_hours: parseFloat(sSlp?.value || 7.5),
        parental_support: currentParental,
        extracurricular_activities: chkExtra?.checked ? 1 : 0
      };

      try {
        const res = await fetch('/api/what-if', {
          method: 'POST',
          signal: currentAbort.signal,
          headers: {
            'Content-Type': 'application/json',
            'X-CSRF-Token': csrf
          },
          body: JSON.stringify(payload)
        });

        if (!res.ok) return;
        const data = await res.json();
        renderSimulationResults(data.baseline, data.scenarios);
      } catch (err) {
        if (err.name === 'AbortError') return;
        console.error('What-If simulation error:', err);
      }
    }

    function renderSimulationResults(b, scenarios) {
      if (!b) return;

      // 1. Score & needle
      const score = Math.max(0, Math.min(100, b.predicted_score));
      if (scoreVal) scoreVal.textContent = score.toFixed(1);

      // Angle: 0 -> -90 deg, 50 -> 0 deg, 100 -> +90 deg
      const angle = -90 + (score / 100) * 180;
      if (needle) {
        needle.style.transform = `rotate(${angle.toFixed(1)}deg)`;
      }

      // 2. Category badge
      if (catBadge) {
        catBadge.textContent = b.performance_category + ' Performance';
        catBadge.className = 'pill ' + b.performance_category.toLowerCase();
      }

      // 3. Risk Banner
      if (riskBanner) {
        if (b.at_risk) {
          riskBanner.style.background = 'var(--rose-bg)';
          riskBanner.style.color = 'var(--rose-text)';
          riskBanner.style.borderColor = 'rgba(244, 63, 94, 0.25)';
          if (riskIcon) riskIcon.textContent = '🚨';
          if (riskTitle) riskTitle.textContent = 'Early Warning Triggered';
          if (riskPct) riskPct.textContent = b.risk_probability + '%';
        } else {
          riskBanner.style.background = 'var(--emerald-bg)';
          riskBanner.style.color = 'var(--emerald-text)';
          riskBanner.style.borderColor = 'rgba(16, 185, 129, 0.25)';
          if (riskIcon) riskIcon.textContent = '✅';
          if (riskTitle) riskTitle.textContent = 'Academic Standing Safe';
          if (riskPct) riskPct.textContent = b.risk_probability + '%';
        }
      }

      // 4. Archetype & Anomaly
      if (profileSpan) profileSpan.textContent = b.learning_profile || 'General Learner';
      if (anomalySpan) {
        anomalySpan.textContent = b.unusual_pattern ? 'Needs Review' : 'Conforming Profile';
        anomalySpan.style.color = b.unusual_pattern ? 'var(--rose)' : 'var(--emerald)';
      }

      // 5. Additive Feature Attributions
      if (attrList && b.feature_impacts) {
        attrList.innerHTML = '';
        const maxImpact = Math.max(1, ...b.feature_impacts.map(x => Math.abs(x.impact)));
        b.feature_impacts.slice(0, 5).forEach(f => {
          const row = document.createElement('div');
          row.className = 'attr-bar-row';
          const isPos = f.impact >= 0;
          const pct = Math.min(100, Math.round((Math.abs(f.impact) / maxImpact) * 100));
          const name = f.feature.replace(/_/g, ' ');
          row.innerHTML = `
            <span style="white-space: nowrap; overflow: hidden; text-overflow: ellipsis; text-transform: capitalize;">${esc(name)}</span>
            <div class="attr-bar-track">
              <div class="attr-bar-fill ${isPos ? 'pos' : 'neg'}" style="width: ${pct}%;"></div>
            </div>
            <span style="font-weight: 700; text-align: right; color: ${isPos ? 'var(--emerald-text)' : 'var(--rose-text)'};">
              ${isPos ? '+' : ''}${f.impact.toFixed(1)} pts
            </span>
          `;
          attrList.appendChild(row);
        });
      }

      // 6. Sensitivity Scenarios (1-click apply)
      if (scenariosList && scenarios) {
        scenariosList.innerHTML = '';
        const labels = {
          attendance_percentage: 'Raise Attendance +5%',
          study_hours_per_week: 'Add +5 Study Hours',
          previous_exam_score: 'Review Exam Weak Topics (+5)',
          assignment_score: 'Improve Assignment Marks (+5)',
          internal_assessment_score: 'Boost Internal Assessment (+5)'
        };

        scenarios.forEach(sc => {
          const delta = sc.score_change;
          const item = document.createElement('div');
          item.className = 'scenario-item';
          item.innerHTML = `
            <div>
              <span style="font-weight: 600;">${labels[sc.feature] || sc.feature}</span>
              <span class="scenario-delta" style="margin-left: 6px;">+${delta.toFixed(1)} pts</span>
            </div>
            <button type="button" class="btn-apply-scenario" data-feature="${esc(sc.feature)}">
              Apply
            </button>
          `;
          scenariosList.appendChild(item);
        });

        // Attach apply click handlers
        scenariosList.querySelectorAll('.btn-apply-scenario').forEach(btn => {
          btn.addEventListener('click', () => {
            const feat = btn.dataset.feature;
            if (feat === 'attendance_percentage' && sAtt) {
              sAtt.value = Math.min(100, parseFloat(sAtt.value) + 5);
            } else if (feat === 'study_hours_per_week' && sStu) {
              sStu.value = Math.min(40, parseFloat(sStu.value) + 5);
            } else if (feat === 'previous_exam_score' && sExm) {
              sExm.value = Math.min(100, parseFloat(sExm.value) + 5);
            } else if (feat === 'assignment_score' && sAsg) {
              sAsg.value = Math.min(100, parseFloat(sAsg.value) + 5);
            } else if (feat === 'internal_assessment_score' && sInt) {
              sInt.value = Math.min(100, parseFloat(sInt.value) + 5);
            }
            updateBadges();
            triggerSimulation();
          });
        });
      }

      // 7. Recommendations
      if (recsList && b.recommendations) {
        recsList.innerHTML = '';
        b.recommendations.slice(0, 3).forEach(r => {
          const li = document.createElement('li');
          li.textContent = r;
          li.style.marginBottom = '4px';
          recsList.appendChild(li);
        });
      }
    }

    // Initial simulation run
    updateBadges();
    runSimulation();
  }

  // =======================================================
  // INTERACTIVE THEME TOGGLE WITH VIEW TRANSITIONS RIPPLE
  // =======================================================
  function initThemeToggle() {
    const toggleBtn = document.getElementById('themeToggleBtn');
    if (!toggleBtn) return;

    // Sync button attributes with currently active data-theme
    const currentTheme = document.documentElement.getAttribute('data-theme') || 'light';
    toggleBtn.setAttribute('aria-checked', currentTheme === 'dark' ? 'true' : 'false');
    toggleBtn.setAttribute('title', currentTheme === 'dark' ? 'Switch to Light Theme' : 'Switch to Dark Theme');

    // React to OS-level preference changes if user hasn't chosen manually
    window.matchMedia('(prefers-color-scheme: dark)').addEventListener('change', (e) => {
      try {
        if (!localStorage.getItem('edupredict-theme')) {
          const next = e.matches ? 'dark' : 'light';
          document.documentElement.setAttribute('data-theme', next);
          document.documentElement.classList.toggle('dark', next === 'dark');
          document.documentElement.style.colorScheme = next;
          toggleBtn.setAttribute('aria-checked', next === 'dark' ? 'true' : 'false');
          toggleBtn.setAttribute('title', next === 'dark' ? 'Switch to Light Theme' : 'Switch to Dark Theme');
        }
      } catch (err) {}
    });
  }

  // =======================================================
  // LIVE WEBSITE ENHANCEMENTS: COUNTERS, TICKERS & TOOLTIPS
  // =======================================================
  function initCountUp() {
    const items = document.querySelectorAll('.stat-value[data-count]');
    if (!items.length) return;

    const observer = new IntersectionObserver((entries, obs) => {
      entries.forEach(entry => {
        if (!entry.isIntersecting) return;
        const el = entry.target;
        obs.unobserve(el);

        const target = parseFloat(el.dataset.count);
        if (isNaN(target)) return;

        const decimals = parseInt(
          el.dataset.decimals || (el.dataset.count.includes('.') ? el.dataset.count.split('.')[1].length : '0'),
          10
        );
        const suffix = el.dataset.suffix || '';
        const prefix = el.dataset.prefix || '';
        const duration = 1200;
        const startTime = performance.now();

        function step(now) {
          const progress = Math.min((now - startTime) / duration, 1);
          // Ease-out cubic
          const ease = 1 - Math.pow(1 - progress, 3);
          const current = target * ease;
          el.textContent = prefix + (decimals > 0 ? current.toFixed(decimals) : Math.round(current).toLocaleString()) + suffix;

          if (progress < 1) {
            requestAnimationFrame(step);
          } else {
            el.textContent = prefix + (decimals > 0 ? target.toFixed(decimals) : target.toLocaleString()) + suffix;
          }
        }
        requestAnimationFrame(step);
      });
    }, { threshold: 0.15 });

    items.forEach(el => observer.observe(el));
  }

  function initLiveTicker() {
    const tickers = document.querySelectorAll('.stream-ticker');
    if (!tickers.length) return;

    tickers.forEach(ticker => {
      const items = ticker.querySelectorAll('.ticker-item');
      if (items.length <= 1) return;
      let idx = 0;
      setInterval(() => {
        items[idx].classList.remove('active');
        idx = (idx + 1) % items.length;
        items[idx].classList.add('active');
      }, 4000);
    });
  }

  function initCardSpotlight() {
    const cards = document.querySelectorAll('.card, .stat-card, .feature');
    if (!cards.length) return;

    document.addEventListener('mousemove', (e) => {
      cards.forEach(card => {
        const rect = card.getBoundingClientRect();
        if (
          e.clientX >= rect.left - 80 &&
          e.clientX <= rect.right + 80 &&
          e.clientY >= rect.top - 80 &&
          e.clientY <= rect.bottom + 80
        ) {
          card.style.setProperty('--mouse-x', (e.clientX - rect.left) + 'px');
          card.style.setProperty('--mouse-y', (e.clientY - rect.top) + 'px');
        }
      });
    }, { passive: true });
  }

  function initChartTooltips() {
    let tooltip = document.querySelector('.chart-live-tooltip');
    if (!tooltip) {
      tooltip = document.createElement('div');
      tooltip.className = 'chart-live-tooltip';
      document.body.appendChild(tooltip);
    }

    document.querySelectorAll('.chart-point, .chart-bar').forEach(el => {
      el.addEventListener('mouseenter', (e) => {
        const val = el.getAttribute('data-value') || el.nextElementSibling?.textContent || '';
        tooltip.textContent = val ? `Value: ${val}` : 'Active Data Metric';
        tooltip.classList.add('visible');
      });

      el.addEventListener('mousemove', (e) => {
        tooltip.style.left = e.clientX + 'px';
        tooltip.style.top = (e.clientY - 12) + 'px';
      });

      el.addEventListener('mouseleave', () => {
        tooltip.classList.remove('visible');
      });
    });
  }

  // =======================================================
  // LIVE HERO CONSTELLATION PARTICLE NETWORK
  // =======================================================
  function initHeroConstellation() {
    const canvas = document.getElementById('heroCanvas');
    if (!canvas) return;

    const ctx = canvas.getContext('2d');
    if (!ctx) return;

    let width = 0;
    let height = 0;
    let dpr = window.devicePixelRatio || 1;
    let isVisible = true;
    let animationFrameId = null;

    let mouse = { x: null, y: null, radius: 140 };

    function resize() {
      const rect = canvas.getBoundingClientRect();
      width = rect.width;
      height = rect.height;
      dpr = window.devicePixelRatio || 1;
      canvas.width = Math.floor(width * dpr);
      canvas.height = Math.floor(height * dpr);
      ctx.setTransform(dpr, 0, 0, dpr, 0, 0);
    }

    resize();
    window.addEventListener('resize', () => {
      resize();
    }, { passive: true });

    const particleCount = Math.min(Math.max(Math.floor(width / 22), 26), 46);
    const particles = [];
    const colorTypes = ['cyan', 'iris', 'magenta', 'mint'];

    for (let i = 0; i < particleCount; i++) {
      particles.push({
        x: Math.random() * (width || 800),
        y: Math.random() * (height || 450),
        vx: (Math.random() - 0.5) * 0.65,
        vy: (Math.random() - 0.5) * 0.65,
        radius: Math.random() * 1.8 + 1.2,
        baseRadius: Math.random() * 1.8 + 1.2,
        pulseSpeed: Math.random() * 0.03 + 0.01,
        pulsePhase: Math.random() * Math.PI * 2,
        colorType: colorTypes[Math.floor(Math.random() * colorTypes.length)]
      });
    }

    const heroSection = canvas.closest('.hero') || canvas.parentElement;
    if (heroSection) {
      heroSection.addEventListener('mousemove', (e) => {
        const rect = canvas.getBoundingClientRect();
        mouse.x = e.clientX - rect.left;
        mouse.y = e.clientY - rect.top;
      }, { passive: true });

      heroSection.addEventListener('mouseleave', () => {
        mouse.x = null;
        mouse.y = null;
      });
    }

    if ('IntersectionObserver' in window && heroSection) {
      const observer = new IntersectionObserver((entries) => {
        entries.forEach(entry => {
          isVisible = entry.isIntersecting;
          if (isVisible && !animationFrameId) {
            loop();
          } else if (!isVisible && animationFrameId) {
            cancelAnimationFrame(animationFrameId);
            animationFrameId = null;
          }
        });
      }, { threshold: 0.05 });
      observer.observe(heroSection);
    }

    function loop() {
      if (!isVisible) return;
      animationFrameId = requestAnimationFrame(loop);

      ctx.clearRect(0, 0, width, height);

      const isDark = document.documentElement.getAttribute('data-theme') === 'dark';
      const colorMap = {
        cyan: isDark ? 'rgba(34, 211, 238,' : 'rgba(6, 182, 212,',
        iris: isDark ? 'rgba(129, 140, 248,' : 'rgba(99, 102, 241,',
        magenta: isDark ? 'rgba(244, 114, 182,' : 'rgba(217, 70, 239,',
        mint: isDark ? 'rgba(52, 211, 153,' : 'rgba(16, 185, 129,'
      };
      const lineBaseColor = isDark ? '129, 140, 248' : '99, 102, 241';
      const maxDist = 115;

      for (let i = 0; i < particles.length; i++) {
        const p = particles[i];

        p.x += p.vx;
        p.y += p.vy;

        if (p.x < 0) { p.x = 0; p.vx *= -1; }
        else if (p.x > width) { p.x = width; p.vx *= -1; }
        if (p.y < 0) { p.y = 0; p.vy *= -1; }
        else if (p.y > height) { p.y = height; p.vy *= -1; }

        if (mouse.x !== null && mouse.y !== null) {
          const dx = mouse.x - p.x;
          const dy = mouse.y - p.y;
          const dist = Math.sqrt(dx * dx + dy * dy);
          if (dist < mouse.radius && dist > 0.01) {
            const force = (1 - dist / mouse.radius) * 0.75;
            p.x += (dx / dist) * force;
            p.y += (dy / dist) * force;
          }
        }

        p.pulsePhase += p.pulseSpeed;
        const currentRadius = p.baseRadius + Math.sin(p.pulsePhase) * 0.6;

        ctx.beginPath();
        ctx.arc(p.x, p.y, Math.max(0.6, currentRadius), 0, Math.PI * 2);
        ctx.fillStyle = (colorMap[p.colorType] || colorMap.iris) + (isDark ? ' 0.9)' : ' 0.7)');
        ctx.fill();

        for (let j = i + 1; j < particles.length; j++) {
          const p2 = particles[j];
          const dx = p.x - p2.x;
          const dy = p.y - p2.y;
          const dist = Math.sqrt(dx * dx + dy * dy);

          if (dist < maxDist) {
            const alpha = (1 - dist / maxDist) * (isDark ? 0.32 : 0.18);
            ctx.beginPath();
            ctx.moveTo(p.x, p.y);
            ctx.lineTo(p2.x, p2.y);
            ctx.strokeStyle = `rgba(${lineBaseColor}, ${alpha})`;
            ctx.lineWidth = 1;
            ctx.stroke();
          }
        }

        if (mouse.x !== null && mouse.y !== null) {
          const dx = p.x - mouse.x;
          const dy = p.y - mouse.y;
          const dist = Math.sqrt(dx * dx + dy * dy);
          if (dist < mouse.radius) {
            const alpha = (1 - dist / mouse.radius) * (isDark ? 0.55 : 0.35);
            ctx.beginPath();
            ctx.moveTo(p.x, p.y);
            ctx.lineTo(mouse.x, mouse.y);
            ctx.strokeStyle = `rgba(${lineBaseColor}, ${alpha})`;
            ctx.lineWidth = 1.2;
            ctx.stroke();
          }
        }
      }
    }

    loop();
  }

  initWhatIfSimulator();
  initThemeToggle();
  initCountUp();
  initLiveTicker();
  initCardSpotlight();
  initChartTooltips();
  initHeroConstellation();
})();


