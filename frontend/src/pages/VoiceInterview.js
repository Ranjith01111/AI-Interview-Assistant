/* Voice Interview — HR Call FINAL
   SIMPLE TTS: No cancel(), no async chains, no external APIs.
   Just speechSynthesis.speak() directly on user gesture.
*/
import { renderNavbar } from '../components/Navbar.js';
import { Toast } from '../components/Toast.js';
import { navigate } from '../main.js';

const QS = [
  { p:"Self-Intro", q:"Tell me about yourself and your professional background.", ex:["name","experience","skills","education","role"], m:"I'm [Name], a [role] with [X] years in [field]. I studied at [university]. Currently at [company]. My core skills are [skills]." },
  { p:"Recent Role", q:"What did you do in your last job? What was your biggest accomplishment?", ex:["title","company","responsibility","achievement","impact"], m:"As [title] at [company], I [responsibility]. My biggest win was [achievement]. I worked with [team] to deliver [outcome]." },
  { p:"Why This Field", q:"Why did you choose this career? What excites you about it?", ex:["passion","reason","interest","motivation","drive"], m:"I chose [field] because [reason]. What excites me is [aspect]. I find fulfillment in [activity]." },
  { p:"Problem Solving", q:"Tell me about a tough problem you solved. Walk me through your approach.", ex:["problem","approach","steps","solution","result"], m:"I faced [problem]. I [step 1], then [step 2]. The result was [outcome]. I learned [lesson]." },
  { p:"Working with People", q:"How do you handle disagreements with colleagues?", ex:["conflict","communication","resolution","empathy","outcome"], m:"I [approach]. For example, [situation]. I listened, shared my view, and we agreed on [solution]." },
  { p:"Future Plans", q:"What do you want to achieve in the next two years?", ex:["goal","plan","growth","target","ambition"], m:"I want to [goal]. I'm working toward it by [action]. My vision is to [aspiration]." },
  { p:"Pressure", q:"How do you perform under tight deadlines?", ex:["deadline","pressure","prioritization","action","delivery"], m:"Under pressure, I [strategy]. When [situation], I [action] and delivered [result] on time." },
  { p:"Your Value", q:"Why should a company hire you?", ex:["strength","unique","value","differentiator"], m:"I bring [unique combo]. I've proven I can [achievement]. I'm ready to [value]." },
];

export async function renderVoiceInterview(container) {
  container.innerHTML = '';
  renderNavbar(container);

  const main = document.createElement('div');
  main.className = 'app-main';
  main.innerHTML = `
    <div class="page-content" style="max-width:580px;margin:0 auto;padding-top:var(--spacing-lg)">
      <div class="card" style="padding:24px;text-align:center" id="cc">
        <div id="orb" style="margin:0 auto 12px;width:90px;height:90px;border-radius:50%;display:flex;align-items:center;justify-content:center;font-size:2.2rem;cursor:pointer;background:linear-gradient(135deg,var(--accent-gold),#ff8c00)">📞</div>
        <div id="st" style="font-size:1rem;font-weight:600;margin-bottom:3px">Tap to Start</div>
        <div id="sub" style="font-size:0.78rem;color:var(--text-muted);margin-bottom:12px">Make sure volume is up</div>

        <div id="hrbox" style="display:none;background:rgba(99,102,241,0.08);border-left:3px solid #6366f1;border-radius:0 8px 8px 0;padding:12px 14px;text-align:left;margin-bottom:10px">
          <div style="font-size:0.65rem;color:#8b5cf6;font-weight:700;margin-bottom:4px">🗣️ HR</div>
          <div id="hrtxt" style="font-size:0.92rem;line-height:1.5"></div>
        </div>

        <div id="youbox" style="display:none;background:rgba(16,185,129,0.06);border-left:3px solid #10b981;border-radius:0 8px 8px 0;padding:12px 14px;text-align:left;margin-bottom:10px">
          <div style="font-size:0.65rem;color:#10b981;font-weight:700;margin-bottom:4px">🎤 YOU</div>
          <div id="youtxt" style="font-size:0.88rem;color:var(--text-muted)">Listening...</div>
        </div>

        <div id="pbar" style="display:none;margin-top:10px">
          <div style="display:flex;justify-content:space-between;font-size:0.7rem;color:var(--text-muted);margin-bottom:3px"><span id="pl"></span><span id="pc"></span></div>
          <div class="progress-bar"><div class="progress-fill" id="pb" style="width:0%"></div></div>
        </div>
        <button id="endb" style="display:none;margin-top:10px;background:none;border:1px solid var(--accent-red);color:var(--accent-red);padding:5px 14px;border-radius:20px;cursor:pointer;font-size:0.72rem">End Call</button>
      </div>
      <div id="rpt" style="display:none;margin-top:20px"></div>
    </div>
  `;
  container.appendChild(main);

  let idx = 0, active = false, recog = null, transcript = '';
  let silT = null, noT = null, results = [], listening = false;

  const orb=main.querySelector('#orb'), st=main.querySelector('#st'), sub=main.querySelector('#sub');
  const hrbox=main.querySelector('#hrbox'), hrtxt=main.querySelector('#hrtxt');
  const youbox=main.querySelector('#youbox'), youtxt=main.querySelector('#youtxt');
  const pb=main.querySelector('#pb'), pl=main.querySelector('#pl'), pc=main.querySelector('#pc');
  const endb=main.querySelector('#endb');

  // ══════════════════════════════════════════════════════════════
  // TTS — Plays MP3 from YOUR backend (no CORS, no speechSynthesis)
  // ══════════════════════════════════════════════════════════════
  function hrSpeak(text, onDone) {
    const url = '/api/v1/tts/speak?text=' + encodeURIComponent(text);
    const audio = new Audio(url);
    audio.volume = 1.0;

    // HARD minimum: never call onDone before this time (ensures you can read + hear)
    const hardMin = Math.max(text.length * 60, 5000); // ~60ms per char, min 5s
    let audioFinished = false;
    let timerFinished = false;

    function checkDone() {
      if (audioFinished && timerFinished) {
        setTimeout(onDone, 1500); // 1.5s breathing room after both are done
      }
    }

    // Timer — won't fire before hardMin ms
    setTimeout(() => { timerFinished = true; checkDone(); }, hardMin);

    // Audio — play and wait for end
    audio.onended = () => { audioFinished = true; checkDone(); };
    audio.onerror = () => { audioFinished = true; checkDone(); };
    audio.play().catch(() => { audioFinished = true; checkDone(); });
  }

  // ══════════════════════════════════════════════════════════════
  // RECOGNITION
  // ══════════════════════════════════════════════════════════════
  function initRecog() {
    const SR = window.SpeechRecognition || window.webkitSpeechRecognition;
    if (!SR) { Toast.error('Need Chrome or Edge.'); return false; }
    recog = new SR();
    recog.continuous = true;
    recog.interimResults = true;
    recog.lang = 'en-US';
    recog.onresult = e => {
      if (!listening) return; // Ignore results during HR turn
      let t=''; for(let i=0;i<e.results.length;i++) t+=e.results[i][0].transcript;
      if (noT) { clearTimeout(noT); noT=null; }
      transcript = t;
      youtxt.textContent = t; youtxt.style.color='var(--text-primary)';
      if (silT) clearTimeout(silT);
      silT = setTimeout(finishAnswer, 3500);
    };
    recog.onerror = e => { if(e.error==='not-allowed') Toast.error('Allow mic access.'); };
    recog.onend = () => { if(active&&listening&&!silT) try{recog.start();}catch(e){} };
    return true;
  }

  function stopRec() {
    listening = false;
    if(silT){clearTimeout(silT);silT=null;}
    if(noT){clearTimeout(noT);noT=null;}
    try{recog?.stop();}catch(e){}
  }

  // ══════════════════════════════════════════════════════════════
  // FLOW
  // ══════════════════════════════════════════════════════════════
  orb.onclick = function() {
    if (active) return;

    // Init recognition
    if (!initRecog()) return;

    active = true;
    endb.style.display = ''; main.querySelector('#pbar').style.display = '';

    // FIRST speak — this is directly inside click handler (user gesture!)
    doHRTurn();
  };

  endb.onclick = function() { endCall(); };

  function doHRTurn() {
    if (idx >= QS.length) { endCall(); return; }
    const q = QS[idx];
    transcript = '';

    // UI: HR turn
    hrbox.style.display = ''; youbox.style.display = 'none';
    hrtxt.textContent = q.q;
    orb.style.background = 'linear-gradient(135deg,#6366f1,#8b5cf6)';
    orb.textContent = '🗣️';
    st.textContent = '🗣️ HR speaking...';
    sub.textContent = `Q${idx+1}/${QS.length} — ${q.p}`;
    pl.textContent = q.p; pc.textContent = `${idx+1}/${QS.length}`;
    pb.style.width = `${(idx/QS.length)*100}%`;

    // Speak question — when done, switch to your turn
    hrSpeak(q.q, () => {
      if (!active) return;
      // 1 second pause
      setTimeout(() => { if (active) doYourTurn(); }, 1000);
    });
  }

  function doYourTurn() {
    hrbox.style.display = 'none'; youbox.style.display = '';
    orb.style.background = 'linear-gradient(135deg,#10b981,#059669)';
    orb.textContent = '🎤';
    st.textContent = '🎤 Your turn — speak';
    sub.textContent = 'Listening...';
    youtxt.textContent = 'Listening...'; youtxt.style.color='var(--text-muted)';
    transcript = '';
    listening = true;

    try { recog.start(); } catch(e) {}

    // 12s no speech → skip
    noT = setTimeout(() => {
      if (!transcript.trim()) {
        stopRec();
        results.push({p:QS[idx].p, q:QS[idx].q, a:'', ev:null, ok:false});
        st.textContent = 'No response — next';
        idx++;
        setTimeout(doHRTurn, 1200);
      }
    }, 12000);
  }

  function finishAnswer() {
    stopRec();
    const a = transcript.trim();
    const q = QS[idx];
    if (!a) { results.push({p:q.p,q:q.q,a:'',ev:null,ok:false}); idx++; doHRTurn(); return; }

    const ev = evaluate(a, q);
    results.push({p:q.p, q:q.q, a, ev, ok:true});

    youbox.style.display='none';
    orb.style.background='linear-gradient(135deg,var(--accent-gold),#ff8c00)';
    orb.textContent='✓';
    st.textContent='✓ Recorded';
    sub.textContent='';

    idx++;
    pb.style.width=`${(idx/QS.length)*100}%`;
    if(idx>=QS.length) setTimeout(endCall, 1500);
    else setTimeout(doHRTurn, 2500);
  }

  function endCall() {
    active=false; stopRec();
    orb.textContent='✅'; orb.style.background='#1a1a2e'; orb.style.cursor='default';
    st.textContent='Call Ended'; sub.textContent='';
    endb.style.display='none'; hrbox.style.display='none'; youbox.style.display='none';
    buildReport();
  }

  // ══════════════════════════════════════════════════════════════
  // EVALUATE
  // ══════════════════════════════════════════════════════════════
  function evaluate(text, q) {
    const lo=text.toLowerCase(), ws=lo.split(/\s+/).filter(w=>w.length>1), wc=ws.length;
    const uniq=new Set(ws), sents=text.split(/[.!?]+/).filter(s=>s.trim().length>3), sc=Math.max(sents.length,1);

    const gR=[[/\b(he|she|it) don't\b/i,"Use 'doesn't'"],[/\bcould of\b|\bshould of\b/i,"Say 'could have'"],[/\bmore better\b/i,"Just say 'better'"],[/\bi seen\b/i,"Say 'I saw'"],[/\bwe was\b|\bthey was\b/i,"Use 'were'"]];
    const gI=gR.filter(([r])=>r.test(text)).map(([,m])=>m);
    const gram=Math.max(2,10-gI.length*2.5);

    const pro=["implement","optimize","collaborate","innovative","leverage","proficient","strategic","comprehensive","facilitate","initiative","analytical","demonstrate","contribute","significant","perspective","prioritize","efficiency","integrate","deliver","expertise"];
    const fil=["um","uh","like","you know","basically","actually","literally","sort of","kind of","i mean"];
    const con=["however","therefore","moreover","additionally","for example","for instance","in addition","as a result","specifically","furthermore","consequently","overall"];

    const pU=pro.filter(w=>lo.includes(w)), fC=fil.reduce((c,f)=>c+(lo.split(f).length-1),0), cU=con.filter(t=>lo.includes(t));
    let voc=Math.min(10,Math.round((uniq.size/Math.max(wc,1))*2.5+pU.length*2+cU.length*1.5+(wc>40?1.5:wc>25?.5:0)));
    let flu=Math.max(1,Math.min(10,10-Math.min(5,Math.round(fC*1.5))-(wc<10?4:wc<20?2:0)+(sc>=3?1:0)));

    const ex=q.ex||[];
    let hits=ex.filter(k=>k.split(/\s+/).some(p=>lo.includes(p))).length;
    let rel=ex.length?Math.min(10,Math.round((hits/ex.length)*8)+(wc>30?2:0)):5;

    const ov=Math.round((gram*.15+voc*.25+flu*.25+rel*.35)*10)/10;

    // Sentence feedback
    const sf=sents.slice(0,5).map(s=>{
      const sl=s.trim().toLowerCase(),sw=sl.split(/\s+/);
      let t;
      if(sw.length<4) t="Too short — add who/what/why.";
      else if(fil.some(f=>sl.includes(f))) t="Remove filler words.";
      else if(sw.length>25) t="Split into 2 sentences.";
      else if(pro.some(p=>sl.includes(p))||con.some(c=>sl.includes(c))) t="✓ Good.";
      else t="Add a professional word or connector.";
      return {s:s.trim().slice(0,70),t};
    });

    const sg=[];
    if(fC>1) sg.push(`${fC} fillers. Practice: 2-min talk daily, restart on every "um".`);
    if(wc<15) sg.push(`Only ${wc} words. Target 40+. Use: Point → Example → Result.`);
    else if(wc<25) sg.push(`${wc} words — add one example to strengthen.`);
    if(!pU.length&&wc>10) sg.push(`Upgrade: "did"→"implemented", "worked with"→"collaborated".`);
    if(!cU.length&&sc>=2) sg.push(`Use connectors: "For example", "As a result", "Specifically".`);
    if(rel<5) sg.push(`Missed: ${ex.filter(k=>!k.split(/\s+/).some(p=>lo.includes(p))).slice(0,3).join(', ')}.`);
    if(gI.length) sg.push(`Grammar: ${gI[0]}`);
    if(!sg.length) sg.push(`Strong! ${wc} words, relevant, well-structured.`);

    return {gram,voc,flu,rel,ov,wc,sc,fC,pU,cU,gI,sg:sg.slice(0,3),sf};
  }

  // ══════════════════════════════════════════════════════════════
  // REPORT
  // ══════════════════════════════════════════════════════════════
  function buildReport() {
    const rpt=main.querySelector('#rpt'); rpt.style.display='';
    const ok=results.filter(r=>r.ok), skip=results.filter(r=>!r.ok);

    if(!ok.length){
      rpt.innerHTML=`<div class="card" style="padding:24px;text-align:center"><h2>No responses</h2><p style="color:var(--text-muted)">Ensure mic is allowed.</p><br><button class="btn btn-primary" id="hb">← Home</button></div>`;
      rpt.querySelector('#hb').onclick=()=>navigate('/dashboard'); return;
    }

    const av=k=>+(ok.reduce((s,r)=>s+r.ev[k],0)/ok.length).toFixed(1);
    const ov=av('ov'),gr=av('gram'),vo=av('voc'),fl=av('flu'),re=av('rel');
    const tw=ok.reduce((s,r)=>s+r.ev.wc,0), tf=ok.reduce((s,r)=>s+r.ev.fC,0);
    const rat=ov>=8?'Excellent':ov>=6?'Good':ov>=4?'Average':'Needs Practice';
    const rc=ov>=8?'var(--accent-emerald)':ov>=6?'var(--accent-gold)':ov>=4?'var(--accent-amber)':'var(--accent-red)';

    const cards=results.map((r,i)=>{
      if(!r.ok) return `<div class="card" style="padding:10px;margin-bottom:8px;opacity:.5;border-left:3px solid var(--accent-red)"><span style="font-size:.75rem">Q${i+1}: ${r.p}</span><span style="float:right;color:var(--accent-red);font-size:.72rem;font-weight:600">SKIPPED</span></div>`;
      const e=r.ev, col=e.ov>=8?'var(--accent-emerald)':e.ov>=6?'var(--accent-gold)':e.ov>=4?'var(--accent-amber)':'var(--accent-red)';
      const sfHtml=(e.sf||[]).map(x=>`<div style="padding:3px 0;font-size:.72rem;border-bottom:1px dashed rgba(255,255,255,.05)"><div style="color:var(--text-secondary)">"${x.s}"</div><div style="color:${x.t.startsWith('✓')?'var(--accent-emerald)':'var(--accent-amber)'}">→ ${x.t}</div></div>`).join('');
      return `<div class="card" style="padding:12px;margin-bottom:8px;border-left:3px solid ${col}">
        <div style="display:flex;justify-content:space-between;margin-bottom:5px"><span style="font-size:.75rem;font-weight:600;color:var(--text-muted)">Q${i+1}: ${r.p}</span><span style="font-weight:700;color:${col}">${e.ov}/10</span></div>
        <div style="font-size:.78rem;background:var(--bg-tertiary);padding:7px;border-radius:5px;margin-bottom:7px;color:var(--text-secondary);font-style:italic">"${r.a.slice(0,180)}${r.a.length>180?'...':''}"</div>
        <div style="display:flex;gap:4px;flex-wrap:wrap;font-size:.6rem;margin-bottom:6px">
          <span style="padding:2px 4px;border-radius:3px;background:rgba(255,255,255,.05)">Gr:${e.gram}</span>
          <span style="padding:2px 4px;border-radius:3px;background:rgba(255,255,255,.05)">Vc:${e.voc}</span>
          <span style="padding:2px 4px;border-radius:3px;background:rgba(255,255,255,.05)">Fl:${e.flu}</span>
          <span style="padding:2px 4px;border-radius:3px;background:rgba(255,255,255,.05)">Rl:${e.rel}</span>
          <span style="padding:2px 4px;border-radius:3px;background:rgba(255,255,255,.05)">${e.wc}w</span>
        </div>
        ${e.sg.map(s=>`<div style="font-size:.76rem;padding:2px 0;color:var(--accent-amber)">⚡ ${s}</div>`).join('')}
        <details style="margin-top:6px"><summary style="font-size:.7rem;color:var(--accent-gold);cursor:pointer">📝 Sentence breakdown</summary><div style="margin-top:5px">${sfHtml}</div></details>
        <details style="margin-top:5px"><summary style="font-size:.7rem;color:var(--accent-gold);cursor:pointer">💡 Model answer</summary><div style="font-size:.76rem;color:var(--text-secondary);margin-top:5px;padding:7px;background:rgba(245,184,0,.04);border-radius:5px;line-height:1.5">${QS[i]?.m||''}</div></details>
      </div>`;
    }).join('');

    const tips=[];
    if(tf>3) tips.push("⏸️ <b>Fillers("+tf+"):</b> 2-min daily talk, restart on every um/like.");
    if(vo<6) tips.push("📚 <b>Vocabulary:</b> Learn 1 word/day: implement, collaborate, optimize. Use in sentences.");
    if(fl<7) tips.push("🗣️ <b>Fluency:</b> Read news aloud daily. No mid-sentence pauses.");
    if(re<6) tips.push("🎯 <b>Relevance:</b> Repeat the question mentally first. Cover each key point.");
    if(gr<7) tips.push("📝 <b>Grammar:</b> "+(ok[0]?.ev?.gI?.[0]||"Practice tense consistency."));
    if(tw/ok.length<25) tips.push("📏 <b>Length:</b> Avg "+(tw/ok.length|0)+"w. Target 40+. Point→Example→Result.");
    if(!tips.length) tips.push("✨ Strong skills! Practice weekly to maintain.");

    rpt.innerHTML=`
      <div class="card" style="padding:20px;text-align:center;margin-bottom:10px">
        <h2 style="margin-bottom:4px">📊 Communication Report</h2>
        <div style="font-size:2.4rem;font-weight:800;color:${rc};margin:6px 0">${ov}/10</div>
        <div style="font-weight:600;color:${rc};margin-bottom:6px">${rat}</div>
        <div style="display:flex;justify-content:center;gap:12px;font-size:.78rem">
          <span style="color:var(--accent-emerald)">✅ Answered: ${ok.length}</span>
          <span style="color:var(--accent-red)">⏭ Skipped: ${skip.length}</span>
        </div>
        <div style="font-size:.7rem;color:var(--text-muted);margin-top:4px">${tw} words • ${tf} fillers</div>
      </div>
      <div style="display:grid;grid-template-columns:1fr 1fr 1fr 1fr;gap:5px;margin-bottom:12px">
        <div class="card" style="padding:7px;text-align:center"><div style="font-size:.58rem;color:var(--text-muted)">Grammar</div><div style="font-weight:700">${gr}</div></div>
        <div class="card" style="padding:7px;text-align:center"><div style="font-size:.58rem;color:var(--text-muted)">Vocab</div><div style="font-weight:700">${vo}</div></div>
        <div class="card" style="padding:7px;text-align:center"><div style="font-size:.58rem;color:var(--text-muted)">Fluency</div><div style="font-weight:700">${fl}</div></div>
        <div class="card" style="padding:7px;text-align:center"><div style="font-size:.58rem;color:var(--text-muted)">Relevance</div><div style="font-weight:700">${re}</div></div>
      </div>
      <h3 style="font-size:.85rem;margin:10px 0 6px">📝 Per-Question</h3>
      ${cards}
      <div class="card" style="padding:16px;margin:12px 0">
        <h3 style="font-size:.85rem;margin-bottom:8px">🚀 Improvement Plan</h3>
        ${tips.map(t=>`<div style="padding:6px 0;border-bottom:1px solid var(--border);font-size:.8rem;line-height:1.5">${t}</div>`).join('')}
      </div>
      <div style="text-align:center;padding-bottom:30px"><button class="btn btn-primary btn-lg" id="hb">← Back to Home</button></div>`;
    rpt.querySelector('#hb').onclick=()=>navigate('/dashboard');
  }
}
