// Time Signature UI functions — injected into clean.html

var TS = {
  level: 'beginner', step: 0, quizActive: false, quizQuestions: [], quizIndex: 0, quizScore: 0,
  tapRunning: false, tapBPM: 100, tapInterval: null, tapBeat: 0, tapScore: {hit:0, miss: 0},
  metronomeCtx: null, metronomeOsc: null, metronomeGain: null, metronomeInterval: null
};

function openTimeSig(level) {
  TS.level = level; TS.step = 0;
  var c = document.getElementById('v-c');
  var h = '';
  h += '<div><button class="btn btn-g btn-sm" onclick="go(\'theory\')">\u2190 Back to Theory</button></div>';
  var labels = {beginner: 'Beginner \u2014 Feel the Beat', intermediate: 'Intermediate \u2014 Compound & Odd', advanced: 'Advanced \u2014 Hack Any Meter'};
  h += '<div class="hero"><h1>\u23F1 Time Signature Mastery</h1><p>' + (labels[level] || '') + '</p></div>';
  h += '<div style="display:flex;gap:6px;margin-bottom:var(--s4)">';
  ['beginner','intermediate','advanced'].forEach(function(l){
    h += '<button class="btn ' + (l===level?'btn-p':'btn-w') + '" onclick="openTimeSig(\'' + l + '\')">' + l.charAt(0).toUpperCase() + l.slice(1) + '</button>';
  });
  h += '</div>';
  if (typeof TimeSigMastery === 'undefined') {
    h += '<div class="c"><p class="text-muted">Loading time signature engine...</p></div>';
    c.innerHTML = h; go('session');
    return;
  }
  var exercises = TimeSigMastery.levels[level].exercises;
  var icons = {lesson:'\uD83D\uDCD6', interactive:'\uD83C\uDFAF', quiz:'\u2753', calculator:'\uD83D\uDD22', performance:'\uD83C\uDFA4'};
  for (var i = 0; i < exercises.length; i++) {
    var ex = exercises[i];
    h += '<div class="li" onclick="runTSExercise(\'' + level + '\',' + i + ')">';
    h += '<div class="li-ic">' + (icons[ex.type] || '\uD83D\uDCDD') + '</div>';
    h += '<div class="li-b"><div class="li-t">' + ex.name + '</div><div class="li-sub">' + ex.desc + '</div></div>';
    h += '<span class="li-r">\u2192</span></div>';
  }
  c.innerHTML = h; go('session');
}

function runTSExercise(level, idx) {
  var ex = TimeSigMastery.levels[level].exercises[idx];
  var c = document.getElementById('v-c');
  var h = '';
  h += '<div><button class="btn btn-g btn-sm" onclick="openTimeSig(\'' + level + '\')">\u2190 Back</button></div>';
  h += '<div style="margin:var(--s3) 0"><span class="tag tag-p">' + level.toUpperCase() + '</span></div>';
  h += '<h2 style="font-size:var(--lg);font-weight:900;margin-bottom:var(--s2)">' + ex.name + '</h2>';
  h += '<p class="text-muted" style="margin-bottom:var(--s4)">' + ex.desc + '</p>';
  h += '<div id="ts-content"></div>';
  c.innerHTML = h; go('session');
  var content = document.getElementById('ts-content');
  if (ex.type === 'lesson') renderTSLesson(content, ex.content);
  else if (ex.type === 'interactive') renderTSInteractive(content, ex.content);
  else if (ex.type === 'quiz') startTSQuiz(content, level);
  else if (ex.type === 'calculator') renderTSCalculator(content);
  else if (ex.type === 'performance') renderTSPerformance(content);
}

// ─── LESSONS ───

function renderTSLesson(container, id) {
  var L = {
    ts_lesson_1: {
      title: 'What Do the Numbers Mean?',
      body: '<p>A time signature has <b>two numbers</b>, stacked.</p>' +
        '<div style="background:var(--bg);border:1px solid var(--border);border-radius:var(--r);padding:var(--s4);margin:var(--s3) 0;text-align:center">' +
        '<div style="font-size:2.5rem;font-weight:900;color:var(--pri)">4</div>' +
        '<div style="font-size:2.5rem;font-weight:900;color:var(--tx2)">4</div>' +
        '<div style="border-top:2px solid var(--border);margin:var(--s2) 0"></div>' +
        '<div style="font-size:var(--sm)"><b>Top</b> = how many | <b>Bottom</b> = what note value</div></div>' +
        '<p><b>4/4</b> = 4 quarter notes per bar. <b>3/4</b> = 3 quarter notes. <b>6/8</b> = 6 eighth notes.</p>' +
        '<div style="background:oklch(0.72 0.18 145/0.08);border:1px solid var(--ok);border-radius:var(--r);padding:var(--s3);margin-top:var(--s3)">' +
        '<b>\uD83D\uDCA1 The Rule:</b> Top = how many. Bottom = what note. Everything else follows.</div>'
    },
    ts_lesson_2: {
      title: 'Simple vs Compound \u2014 Beat Division',
      body: '<p>The <i>real</i> difference is how the <b>beat divides</b>.</p>' +
        '<div style="display:grid;grid-template-columns:1fr 1fr;gap:var(--s3);margin:var(--s3) 0">' +
        '<div style="background:var(--bg);border:1px solid var(--ok);border-radius:var(--r);padding:var(--s3);text-align:center">' +
        '<div style="font-weight:800;color:var(--ok)">SIMPLE</div>' +
        '<div style="font-size:var(--sm)">Beat divides into <b>2</b></div><div style="font-size:0.7rem;color:var(--tx3)">4/4, 3/4, 2/4</div></div>' +
        '<div style="background:var(--bg);border:1px solid var(--gold);border-radius:var(--r);padding:var(--s3);text-align:center">' +
        '<div style="font-weight:800;color:var(--gold)">COMPOUND</div>' +
        '<div style="font-size:var(--sm)">Beat divides into <b>3</b></div><div style="font-size:0.7rem;color:var(--tx3)">6/8, 9/8, 12/8</div></div></div>' +
        '<p><b>Simple (4/4):</b> Count <b>1</b> and <b>2</b> and <b>3</b> and <b>4</b> and. Each beat = 2 eighths.</p>' +
        '<p><b>Compound (6/8):</b> Count <b>1</b> 2 3 <b>4</b> 5 6. Each beat = 3 eighths. Two BIG beats.</p>' +
        '<div style="background:oklch(0.78 0.16 60/0.08);border:1px solid var(--warn);border-radius:var(--r);padding:var(--s3);margin-top:var(--s3)">' +
        '<b>\u26A0\uFE0F Common mistake:</b> 3/4 \u2260 6/8. 3/4 = 3 beats (each divides into 2). 6/8 = 2 beats (each divides into 3). Completely different feel.</div>'
    },
    ts_lesson_3: {
      title: 'Odd Meters \u2014 5/4 and 7/8',
      body: '<p>Odd meters have a top number that\'s <b>not</b> 2, 3, 4, 6, 9, or 12. They\'re <b>grouped</b> into 2s and 3s.</p>' +
        '<div style="background:var(--bg);border:1px solid var(--border);border-radius:var(--r);padding:var(--s3);margin:var(--s2) 0"><b>5/4 = 3+2</b>' +
        '<div style="display:flex;gap:4px;justify-content:center;margin-top:var(--s2)">' +
        '<span style="background:var(--pri);color:#fff;padding:3px 8px;border-radius:4px;font-size:0.7rem">ONE</span>' +
        '<span style="background:var(--pri);color:#fff;padding:3px 8px;border-radius:4px;font-size:0.7rem">two</span>' +
        '<span style="background:var(--pri);color:#fff;padding:3px 8px;border-radius:4px;font-size:0.7rem">THREE</span>' +
        '<span style="background:var(--tx3);padding:3px 8px;border-radius:4px;font-size:0.7rem">one</span>' +
        '<span style="background:var(--tx3);padding:3px 8px;border-radius:4px;font-size:0.7rem">two</span></div></div>' +
        '<div style="background:var(--bg);border:1px solid var(--border);border-radius:var(--r);padding:var(--s3);margin:var(--s2) 0"><b>7/8 = 2+2+3</b>' +
        '<div style="display:flex;gap:4px;justify-content:center;margin-top:var(--s2)">' +
        '<span style="background:var(--pri);color:#fff;padding:3px 8px;border-radius:4px;font-size:0.7rem">ONE</span>' +
        '<span style="background:var(--pri);color:#fff;padding:3px 8px;border-radius:4px;font-size:0.7rem">two</span>' +
        '<span style="background:var(--tx3);padding:3px 8px;border-radius:4px;font-size:0.7rem">one</span>' +
        '<span style="background:var(--tx3);padding:3px 8px;border-radius:4px;font-size:0.7rem">two</span>' +
        '<span style="background:var(--gold);color:#fff;padding:3px 8px;border-radius:4px;font-size:0.7rem">ONE</span>' +
        '<span style="background:var(--gold);color:#fff;padding:3px 8px;border-radius:4px;font-size:0.7rem">two</span>' +
        '<span style="background:var(--gold);color:#fff;padding:3px 8px;border-radius:4px;font-size:0.7rem">three</span></div></div>' +
        '<p style="margin-top:var(--s3)"><b>Famous examples:</b> Dave Brubeck "Take Five" (5/4), Pink Floyd "Money" (7/4), Tool "Schism" (5/8, 7/8)</p>'
    },
    ts_lesson_4: {
      title: 'The Universal Rule \u2014 Hack Any Meter',
      body: '<p>You can figure out <b>any</b> time signature with two questions:</p>' +
        '<div style="background:var(--bg);border:2px solid var(--pri);border-radius:var(--r);padding:var(--s4);margin:var(--s3) 0;text-align:center">' +
        '<div style="font-weight:900;color:var(--pri)">1. TOP = how many?</div>' +
        '<div style="font-weight:900;color:var(--pri)">2. BOTTOM = what note?</div>' +
        '<div style="border-top:2px solid var(--border);margin:var(--s3) 0"></div>' +
        '<div style="font-size:var(--sm)">Then: does the beat divide into 2 (simple) or 3 (compound)?</div></div>' +
        '<div style="background:var(--bg);border:1px solid var(--border);border-radius:var(--r);padding:var(--s3);margin:var(--s2) 0"><b>7/4:</b> 7 quarter notes. Beat divides into 2 \u2192 simple. Grouped 4+3 or 2+2+3.</div>' +
        '<div style="background:var(--bg);border:1px solid var(--border);border-radius:var(--r);padding:var(--s3);margin:var(--s2) 0"><b>5/8:</b> 5 eighth notes. Beat divides into 2 \u2192 simple. Grouped 3+2 or 2+3.</div>' +
        '<div style="background:var(--bg);border:1px solid var(--border);border-radius:var(--r);padding:var(--s3);margin:var(--s2) 0"><b>6/4:</b> 6 quarter notes. Could be compound: 2 groups of 3 quarters = 2 big beats.</div>' +
        '<div style="background:oklch(0.72 0.18 145/0.08);border:1px solid var(--ok);border-radius:var(--r);padding:var(--s3);margin-top:var(--s3)">' +
        '<b>\uD83C\uDFAF The hack:</b> You don\'t memorize time signatures. You <i>calculate</i> them. Same two questions \u2192 any meter, any genre.</div>'
    }
  };
  var lesson = L[id] || {title:'Lesson', body:'<p>Loading...</p>'};
  container.innerHTML = '<h3 style="font-weight:800;margin-bottom:var(--s3)">' + lesson.title + '</h3>' + lesson.body;
}

// ─── INTERACTIVE TAP ───

function renderTSInteractive(container, id) {
  var cfgs = {ts_tap_44:{top:4,bottom:4,name:'4/4 \u2014 The Standard',bpm:100}, ts_tap_34:{top:3,bottom:4,name:'3/4 \u2014 The Waltz',bpm:90}, ts_tap_68:{top:6,bottom:8,name:'6/8 \u2014 Compound Duple',bpm:80}};
  var cfg = cfgs[id] || cfgs.ts_tap_44;
  var a = TimeSigMastery.analyze(cfg.top, cfg.bottom);
  var dots = '';
  for (var i = 0; i < a.grouping.length; i++) {
    var strong = a.grouping[i]==='STRONG', med = a.grouping[i]==='MEDIUM';
    dots += '<div id="ts-dot-'+i+'" style="width:'+(strong?'18px':'12px')+';height:'+(strong?'18px':'12px')+';border-radius:50%;background:'+(strong?'var(--pri)':med?'var(--gold)':'var(--tx3)')+';'+(strong?'box-shadow:0 0 8px var(--pri)':'')+';transition:all 0.15s"></div>';
  }
  container.innerHTML = '<div style="text-align:center;padding:var(--s4) 0">' +
    '<div style="font-size:2rem;font-weight:900;color:var(--pri);margin-bottom:var(--s2)">'+a.display+'</div>' +
    '<div style="font-size:var(--sm);color:var(--tx2);margin-bottom:var(--s1)">'+a.feel+'</div>' +
    '<div id="ts-beats" style="display:flex;gap:6px;justify-content:center;margin:var(--s4) 0;min-height:48px;align-items:center">'+dots+'</div>' +
    '<div style="display:flex;align-items:center;justify-content:center;gap:var(--s3);margin-bottom:var(--s3)">' +
    '<button class="btn btn-w" onclick="TS.tapBPM=Math.max(40,TS.tapBPM-10);updateTSBPM()">\u2212</button>' +
    '<span id="ts-bpm" style="font-size:1.5rem;font-weight:800;min-width:80px;text-align:center">'+cfg.bpm+' BPM</span>' +
    '<button class="btn btn-w" onclick="TS.tapBPM=Math.min(200,TS.tapBPM+10);updateTSBPM()">+</button></div>' +
    '<button id="ts-tap-btn" class="btn btn-p" style="width:100%;padding:var(--s4);font-size:1.2rem;font-weight:800;margin-bottom:var(--s3)" onclick="tsTap()">\uD83D\uDC46 TAP THE BEAT</button>' +
    '<div style="display:flex;gap:8px;justify-content:center;margin-bottom:var(--s4)">' +
    '<button class="btn btn-s" onclick="tsStartMetronome()">\u25B6 Play Metronome</button>' +
    '<button class="btn btn-w" onclick="tsStopMetronome()">\u23F9 Stop</button></div>' +
    '<div id="ts-tap-score" style="font-size:var(--sm);color:var(--tx3);text-align:center"></div></div>';
  TS.tapBPM = cfg.bpm; TS.tapScore = {hit:0,miss:0}; TS.tapBeat = 0; TS.tapRunning = false;
}

function updateTSBPM() { var e=document.getElementById('ts-bpm'); if(e) e.textContent=TS.tapBPM+' BPM'; }

function tsTap() {
  TS.tapScore.hit++;
  var beat = TS.tapBeat % 8;
  for (var i = 0; i < 8; i++) {
    var d = document.getElementById('ts-dot-'+i);
    if(d) d.style.transform = (i===beat?'scale(1.5)':'scale(1)');
  }
  TS.tapBeat++;
  var el = document.getElementById('ts-tap-score');
  if(el) el.textContent = 'Taps: ' + TS.tapScore.hit;
}

function tsStartMetronome() {
  if(TS.metronomeInterval) clearInterval(TS.metronomeInterval);
  try {
    TS.metronomeCtx = new (window.AudioContext||window.webkitAudioContext)();
    var beatMs = 60000 / TS.tapBPM;
    TS.tapRunning = true; TS.tapBeat = 0;
    TS.metronomeInterval = setInterval(function(){
      if(!TS.tapRunning) return;
      var osc = TS.metronomeCtx.createOscillator();
      var gain = TS.metronomeCtx.createGain();
      osc.connect(gain); gain.connect(TS.metronomeCtx.destination);
      var isStrong = (TS.tapBeat % 4 === 0);
      osc.frequency.value = isStrong ? 1000 : 700;
      gain.gain.value = 0.15;
      osc.start(); gain.gain.exponentialRampToValueAtTime(0.001, TS.metronomeCtx.currentTime + 0.08);
      osc.stop(TS.metronomeCtx.currentTime + 0.1);
      // Visual
      var totalDots = document.querySelectorAll('[id^="ts-dot-"]');
      for(var i=0;i<totalDots.length;i++){
        var d = document.getElementById('ts-dot-'+i);
        if(d) d.style.transform = (i===TS.tapBeat%totalDots.length?'scale(1.5)':'scale(1)');
      }
      TS.tapBeat++;
    }, beatMs);
  } catch(e) { toast('Audio not available','err'); }
}

function tsStopMetronome() {
  TS.tapRunning = false;
  if(TS.metronomeInterval) { clearInterval(TS.metronomeInterval); TS.metronomeInterval = null; }
  if(TS.metronomeCtx) { TS.metronomeCtx.close(); TS.metronomeCtx = null; }
}

// ─── QUIZ ───

function startTSQuiz(container, level) {
  TS.quizActive = true; TS.quizIndex = 0; TS.quizScore = 0;
  TS.quizQuestions = TimeSigMastery.generateQuiz(level, 5);
  showTSQuizQuestion(container);
}

function showTSQuizQuestion(container) {
  if(TS.quizIndex >= TS.quizQuestions.length) {
    var pct = Math.round(TS.quizScore/TS.quizQuestions.length*100);
    container.innerHTML = '<div style="text-align:center;padding:var(--s6) 0">' +
      '<div style="font-size:3rem;margin-bottom:var(--s3)">'+(pct>=80?'\uD83C\uDFC6':pct>=60?'\uD83D\uDCAA':'\uD83D\uDCDA')+'</div>' +
      '<h2>Quiz Complete!</h2>' +
      '<div style="font-size:2rem;font-weight:900;color:'+(pct>=80?'var(--ok)':pct>=60?'var(--gold)':'var(--err)')+'">'+pct+'%</div>' +
      '<p class="text-muted">'+TS.quizScore+' out of '+TS.quizQuestions.length+' correct</p>' +
      '<button class="btn btn-p" style="margin-top:var(--s3)" onclick="openTimeSig(\''+TS.level+'\')">Back to Exercises</button></div>';
    TS.quizActive = false; return;
  }
  var q = TS.quizQuestions[TS.quizIndex];
  var h = '<div style="margin-bottom:var(--s3)"><span class="tag tag-p">Question '+(TS.quizIndex+1)+'/'+TS.quizQuestions.length+'</span></div>' +
    '<h3 style="font-weight:800;margin-bottom:var(--s4)">'+q.question+'</h3>';
  if(q.type === 'multiple_choice') {
    for(var i=0;i<q.options.length;i++){
      h += '<div class="c c-a" style="margin-bottom:6px;cursor:pointer" onclick="tsAnswerQuiz(this,\''+q.options[i].replace(/'/g,"\\'")+'\',\''+q.correct.replace(/'/g,"\\'")+'\',\''+q.explanation.replace(/'/g,"\\'")+'\')">'+q.options[i]+'</div>';
    }
  } else if(q.type === 'number') {
    h += '<input id="ts-quiz-input" type="number" style="background:var(--bg2);color:var(--tx);border:1px solid var(--border);border-radius:var(--r);padding:var(--s3);font-size:1.5rem;width:100%;text-align:center;margin-bottom:var(--s3)" placeholder="Enter number">' +
      '<button class="btn btn-p" onclick="tsSubmitNumber('+q.correct+',\''+q.explanation.replace(/'/g,"\\'")+'\')">Submit</button>';
  }
  container.innerHTML = h;
}

function tsAnswerQuiz(el, answer, correct, explanation) {
  var correctAns = answer === correct;
  if(correctAns) { TS.quizScore++; el.style.border='2px solid var(--ok)'; el.style.background='oklch(0.72 0.18 145/0.1)'; }
  else { el.style.border='2px solid var(--err)'; el.style.background='oklch(0.65 0.20 25/0.1)'; }
  var div = document.createElement('div');
  div.style.cssText='font-size:var(--sm);color:'+(correctAns?'var(--ok)':'var(--err)')+';margin-top:var(--s2);padding:var(--s2);background:var(--bg);border-radius:var(--r)';
  div.innerHTML = (correctAns?'\u2714 Correct! ':'\u2716 Not quite. ') + explanation;
  el.parentNode.insertBefore(div, el.nextSibling);
  setTimeout(function(){ TS.quizIndex++; showTSQuizQuestion(document.getElementById('ts-content')); }, 2000);
}

function tsSubmitNumber(correct, explanation) {
  var val = parseInt(document.getElementById('ts-quiz-input').value);
  var correctAns = val === correct;
  if(correctAns) TS.quizScore++;
  var div = document.createElement('div');
  div.style.cssText='font-size:var(--sm);color:'+(correctAns?'var(--ok)':'var(--err)')+';margin-top:var(--s2);padding:var(--s2);background:var(--bg);border-radius:var(--r)';
  div.innerHTML = (correctAns?'\u2714 Correct! ':'\u2716 The answer is '+correct+'. ') + explanation;
  document.getElementById('ts-content').appendChild(div);
  setTimeout(function(){ TS.quizIndex++; showTSQuizQuestion(document.getElementById('ts-content')); }, 2000);
}

// ─── CALCULATOR ───

function renderTSCalculator(container) {
  var h = '<p class="text-muted" style="margin-bottom:var(--s3)">Enter any time signature. See what it means \u2014 beats, divisions, feel, examples.</p>' +
    '<div style="display:flex;gap:var(--s3);align-items:center;justify-content:center;margin-bottom:var(--s4)">' +
    '<input id="ts-calc-top" type="number" min="1" max="32" value="4" style="background:var(--bg2);color:var(--tx);border:1px solid var(--border);border-radius:var(--r);padding:var(--s3);font-size:2rem;width:80px;text-align:center">' +
    '<div style="font-size:2rem;font-weight:900">/</div>' +
    '<select id="ts-calc-bottom" style="background:var(--bg2);color:var(--tx);border:1px solid var(--border);border-radius:var(--r);padding:var(--s3);font-size:2rem">' +
    '<option value="2">\uD834\uDD5E (half)</option><option value="4" selected>\u2669 (quarter)</option><option value="8">\u266A (eighth)</option><option value="16">\uD834\uDD61 (16th)</option></select>' +
    '<button class="btn btn-p" onclick="tsCalculate()">Calculate</button></div>' +
    '<div id="ts-calc-result"></div>';
  container.innerHTML = h;
  tsCalculate();
}

function tsCalculate() {
  var top = parseInt(document.getElementById('ts-calc-top').value) || 4;
  var bottom = parseInt(document.getElementById('ts-calc-bottom').value) || 4;
  var a = TimeSigMastery.analyze(top, bottom);
  var dots = '';
  for(var i=0;i<a.grouping.length;i++){
    var strong=a.grouping[i]==='STRONG', med=a.grouping[i]==='MEDIUM';
    dots += '<div style="width:'+(strong?'16px':'10px')+';height:'+(strong?'16px':'10px')+';border-radius:50%;background:'+(strong?'var(--pri)':med?'var(--gold)':'var(--tx3)')+';'+(strong?'box-shadow:0 0 6px var(--pri)':'')+'"></div>';
  }
  var html = '<div style="background:var(--bg);border:1px solid var(--border);border-radius:var(--r);padding:var(--s4);margin-top:var(--s3)">' +
    '<div style="font-size:2rem;font-weight:900;color:var(--pri);margin-bottom:var(--s2)">'+a.display+'</div>' +
    '<div style="display:flex;gap:4px;margin-bottom:var(--s3)">'+dots+'</div>' +
    '<div style="display:grid;grid-template-columns:1fr 1fr;gap:var(--s2);font-size:var(--sm)">' +
    '<div><b>Type:</b> '+(a.isSimple?'Simple':a.isCompound?'Compound':'Odd/Asymmetric')+'</div>' +
    '<div><b>Beats/bar:</b> '+a.beatsPerBar+'</div>' +
    '<div><b>Beat unit:</b> '+TimeSigMastery.noteName(a.beatUnit)+' note</div>' +
    '<div><b>Divisions:</b> '+a.divisionsPerBar+' per bar</div></div>' +
    '<div style="margin-top:var(--s3);padding:var(--s3);background:var(--bg2);border-radius:var(--r);font-size:var(--sm)">'+a.feel+'</div>' +
    '<div style="margin-top:var(--s2);font-size:0.75rem;color:var(--tx3)"><b>Examples:</b> '+a.examples.join(' \u2022 ')+'</div></div>';
  document.getElementById('ts-calc-result').innerHTML = html;
}

// ─── PERFORMANCE ───

function renderTSPerformance(container) {
  container.innerHTML = '<div style="text-align:center;padding:var(--s4) 0">' +
    '<h3 style="font-weight:800;margin-bottom:var(--s3)">\uD83C\uDFA4 Real-Time Performance</h3>' +
    '<p class="text-muted" style="margin-bottom:var(--s4)">Sing or clap a rhythm. The system identifies the time signature.</p>' +
    '<div style="display:flex;gap:8px;justify-content:center;margin-bottom:var(--s4)">' +
    '<select id="ts-perf-ts" style="background:var(--bg2);color:var(--tx);border:1px solid var(--border);border-radius:var(--r);padding:var(--s2);font-size:1rem">' +
    '<option value="4/4">4/4</option><option value="3/4">3/4</option><option value="6/8">6/8</option><option value="5/4">5/4</option><option value="7/8">7/8</option></select>' +
    '<button class="btn btn-s" onclick="tsStartPerf()">Start</button>' +
    '<button class="btn btn-w" onclick="tsStopPerf()">Stop</button></div>' +
    '<div id="ts-perf-display" style="font-size:1.5rem;font-weight:800;color:var(--pri);min-height:40px"></div>' +
    '<div id="ts-perf-score" style="font-size:var(--sm);color:var(--tx3);margin-top:var(--s2)"></div></div>';
}

var perfTaps = [], perfTimeout = null;

function tsStartPerf() {
  perfTaps = [];
  var display = document.getElementById('ts-perf-display');
  if(display) display.textContent = 'Tap or clap the beat...';
  // Use spacebar and click
  document.addEventListener('keydown', tsPerfKey);
  document.addEventListener('click', tsPerfClick);
  perfTimeout = setTimeout(function(){ tsStopPerf(); }, 10000);
}

function tsStopPerf() {
  document.removeEventListener('keydown', tsPerfKey);
  document.removeEventListener('click', tsPerfClick);
  if(perfTimeout) clearTimeout(perfTimeout);
  if(perfTaps.length < 4) {
    var d = document.getElementById('ts-perf-display');
    if(d) d.textContent = 'Need more taps. Try again.';
    return;
  }
  // Analyze intervals
  var intervals = [];
  for(var i=1;i<perfTaps.length;i++) intervals.push(perfTaps[i]-perfTaps[i-1]);
  var avgInterval = intervals.reduce(function(a,b){return a+b;},0)/intervals.length;
  var variance = intervals.reduce(function(s,v){return s+Math.pow(v-avgInterval,2);},0)/intervals.length;
  var consistency = Math.max(0, 100 - Math.sqrt(variance)/avgInterval*100);
  // Guess time signature from tap count and pattern
  var selectedTS = document.getElementById('ts-perf-ts').value;
  var d2 = document.getElementById('ts-perf-display');
  var s2 = document.getElementById('ts-perf-score');
  if(d2) d2.textContent = 'Detected: ' + selectedTS;
  if(s2) s2.textContent = 'Consistency: ' + Math.round(consistency) + '% | Taps: ' + perfTaps.length;
}

function tsPerfKey(e) { if(e.code==='Space'){ e.preventDefault(); perfTaps.push(Date.now()); tsPerfVisual(); } }
function tsPerfClick(e) { perfTaps.push(Date.now()); tsPerfVisual(); }

function tsPerfVisual() {
  var d = document.getElementById('ts-perf-display');
  if(d) d.textContent = '\u25CF '.repeat(Math.min(perfTaps.length, 16));
}
