// ═══════════════════════════════════════════════════════════════════════════
// PITCH TRAINING ENGINE — Evidence-Based, Real-Time, Adaptive
// 
// Research Foundation:
// 1. Real-time visual feedback (Frontiers 2025, Scientific Reports 2025, JMIR 2025)
// 2. SOVTE exercises (Journal of Voice 2025 RCT, ScienceDirect 2024)
// 3. Auditory-visual combined feedback (Frontiers Psychology 2021)
// 4. TA/CT muscle coordination training (NCVS, NSF 2024)
// 5. Pitch discrimination via own-voice quality (IIAI 2024)
// 6. Passaggio/register transition training (Roubeau et al. 2008)
//
// Physiology measured in real-time:
// - F0 (fundamental) → pitch accuracy (cents)
// - H1-H2 ratio → fold closure quality
// - F1/F2 formants → vocal tract shaping
// - Spectral tilt → brightness/darkness
// - Jitter → vocal stability
// - RMS dynamics → loudness control
// - Passaggio point → TA/CT transition
//
// Training levels:
// BEGINNER: Pitch matching, single notes, SOVTE, visual feedback
// INTERMEDIATE: Interval training, register transitions, DAF, formant shaping
// ADVANCED: Passaggio mastery, dynamic control, spectral tuning, performance simulation
// ═══════════════════════════════════════════════════════════════════════════

var PitchTraining = {
  
  // ─── STATE ───
  level: 'beginner', // beginner | intermediate | advanced
  session: null,
  engine: null,
  targetNote: null,
  targetFreq: null,
  history: [], // {timestamp, freq, cents, h1h2, f1, f2, rms, jitter}
  scores: {attempts: 0, inTune: 0, streak: 0, bestStreak: 0},
  
  // ─── REFERENCE DATA ───
  // Note frequencies (A4 = 440Hz)
  noteNames: ['C','C#','D','D#','E','F','F#','G','G#','A','A#','B'],
  
  // Training exercises by level — evidence-based
  exercises: {
    beginner: [
      {
        id: 'b1', name: 'Single Note Match',
        desc: 'Match a target note. Hold 3 seconds. Visual feedback guides you.',
        method: 'visual_feedback',
        research: 'Real-time visual feedback significantly improves pitch accuracy vs auditory-only training (Frontiers 2025, Scientific Reports 2025)',
        measure: ['f0_accuracy', 'cents_deviation'],
        successCriteria: {cents: 15, holdMs: 2000}
      },
      {
        id: 'b2', name: 'SOVTE Lip Trill',
        desc: 'Buzz your lips while sliding up and down. Builds fold closure coordination.',
        method: 'sovte',
        research: 'SOVTE increases reactive inertance, improving fold closure efficiency (Journal of Voice 2025 RCT)',
        measure: ['h1h2_ratio', 'spectral_tilt', 'stability'],
        successCriteria: {jitter: 0.02, h1h2Range: 5}
      },
      {
        id: 'b3', name: '5-Note Scale',
        desc: 'Sing Do-Re-Mi-Fa-Sol. Each note must be in tune before moving on.',
        method: 'visual_feedback',
        research: 'Pitch discrimination via own-voice quality develops internal reference (IIAI 2024)',
        measure: ['f0_accuracy', 'interval_consistency'],
        successCriteria: {cents: 20, notesInTune: 4}
      },
      {
        id: 'b4', name: 'Vowel Clarity',
        desc: 'Sing "ah" on one note. Watch your formants. Keep F1/F2 stable.',
        method: 'formant_feedback',
        research: 'Formant stability indicates consistent vocal tract shaping (Sundberg 1987)',
        measure: ['f1_stability', 'f2_stability', 'f0_accuracy'],
        successCriteria: {f1SD: 30, f2SD: 50, cents: 25}
      }
    ],
    intermediate: [
      {
        id: 'i1', name: 'Interval Training',
        desc: 'Sing specific intervals (3rd, 5th, octave). Visual + auditory feedback.',
        method: 'auditory_visual',
        research: 'Combined auditory-visual feedback is stronger than either alone (Frontiers Psychology 2021)',
        measure: ['interval_accuracy', 'f0_accuracy'],
        successCriteria: {intervalCents: 20, notesInTune: 2}
      },
      {
        id: 'i2', name: 'Register Slide',
        desc: 'Slide from chest to head voice smoothly. Watch the transition zone.',
        method: 'register_transition',
        research: 'TA/CT muscle coordination must be trained separately then bridged (NCVS, NSF 2024)',
        measure: ['passaggio_smoothness', 'h1h2_transition', 'f0_continuity'],
        successCriteria: {breaks: 0, slideTime: 4000}
      },
      {
        id: 'i3', name: 'Delayed Feedback',
        desc: 'Sing with 200ms delayed auditory feedback. Forces internal pitch sense.',
        method: 'daf',
        research: 'DAF forces reliance on internal pitch reference, accelerating internalization (JMIR 2025)',
        measure: ['f0_accuracy', 'internalization_score'],
        successCriteria: {cents: 25, afterEffect: true}
      },
      {
        id: 'i4', name: 'Dynamic Control',
        desc: 'Sing one note: loud → soft → loud. Keep pitch steady through dynamics.',
        method: 'dynamic_control',
        research: 'Pitch stability under dynamic change indicates advanced laryngeal control (Titze 2000)',
        measure: ['f0_stability', 'rms_range', 'pitch_drift'],
        successCriteria: {f0Drift: 10, rmsRange: 15}
      }
    ],
    advanced: [
      {
        id: 'a1', name: 'Passaggio Mastery',
        desc: 'Sing through your passaggio zone. No breaks, no flipping. Pure mix.',
        method: 'passaggio',
        research: 'Passaggio negotiation requires vowel modification and TA/CT balance (Roubeau et al. 2008)',
        measure: ['passaggio_smoothness', 'h1h2_ratio', 'formant_tuning', 'f0_continuity'],
        successCriteria: {breaks: 0, h1h2Smooth: true, cents: 15}
      },
      {
        id: 'a2', name: 'Spectral Shaping',
        desc: 'Sing "ah" then "ee" on same note. Watch harmonics change. Control brightness.',
        method: 'spectral_tuning',
        research: 'Spectral tilt (H1-H2 ratio) determines perceived brightness (Titze 2000)',
        measure: ['spectral_tilt', 'h1h2_ratio', 'f2_frequency'],
        successCriteria: {tiltChange: 5, f2Shift: 200}
      },
      {
        id: 'a3', name: 'Performance Simulation',
        desc: 'Sing a phrase with full expression. Real-time scoring on pitch, dynamics, stability.',
        method: 'performance',
        research: 'Integrated feedback on multiple parameters simultaneously builds performance readiness (Frontiers 2025)',
        measure: ['f0_accuracy', 'dynamic_range', 'jitter', 'formant_stability', 'overall_score'],
        successCriteria: {overallPercent: 80}
      }
    ]
  },
  
  // ─── LEVEL ASSESSMENT ───
  assessLevel: function() {
    var h = this.history;
    if (h.length < 10) return 'beginner';
    
    var recent = h.slice(-20);
    var avgCents = recent.reduce(function(s,r){return s+Math.abs(r.cents);},0) / recent.length;
    var avgJitter = recent.reduce(function(s,r){return s+(r.jitter||0);},0) / recent.length;
    var inTuneRate = recent.filter(function(r){return Math.abs(r.cents)<15;}).length / recent.length;
    
    // Advanced: < 10 cents avg, < 1% jitter, > 80% in tune
    if (avgCents < 10 && avgJitter < 0.01 && inTuneRate > 0.8) return 'advanced';
    // Intermediate: < 20 cents avg, < 2% jitter, > 60% in tune
    if (avgCents < 20 && avgJitter < 0.02 && inTuneRate > 0.6) return 'intermediate';
    return 'beginner';
  },
  
  // ─── REAL-TIME ANALYSIS ───
  analyze: function(buffer, sampleRate, analyser) {
    // F0 via autocorrelation
    var freq = this.autocorrelate(buffer, sampleRate);
    if (freq < 50 || freq > 1200) return null;
    
    // RMS (loudness)
    var rms = 0;
    for (var i = 0; i < buffer.length; i++) rms += buffer[i] * buffer[i];
    rms = Math.sqrt(rms / buffer.length);
    
    // Jitter (cycle-to-cycle frequency variation)
    var jitter = this.measureJitter(buffer, sampleRate, freq);
    
    // Spectrum analysis
    var spectrum = new Float32Array(analyser.frequencyBinCount);
    analyser.getFloatFrequencyData(spectrum);
    
    // H1-H2 ratio (fold closure quality)
    var binWidth = sampleRate / analyser.fftSize;
    var h1Bin = Math.round(freq / binWidth);
    var h2Bin = Math.round(2 * freq / binWidth);
    var h1 = spectrum[h1Bin] || -100;
    var h2 = spectrum[h2Bin] || -100;
    var h1h2 = h1 - h2;
    
    // Formant estimation (F1, F2)
    var formants = this.estimateFormants(spectrum, binWidth);
    
    // Spectral tilt (brightness indicator)
    var tilt = this.spectralTilt(spectrum, binWidth, freq);
    
    // Cents deviation from target
    var cents = 0;
    if (this.targetFreq && this.targetFreq > 0) {
      cents = Math.round(1200 * Math.log2(freq / this.targetFreq));
    }
    
    return {
      freq: freq,
      cents: cents,
      rms: rms,
      jitter: jitter,
      h1h2: h1h2,
      f1: formants.f1,
      f2: formants.f2,
      tilt: tilt,
      timestamp: Date.now()
    };
  },
  
  autocorrelate: function(buf, sr) {
    var n = buf.length, rms = 0;
    for (var i = 0; i < n; i++) rms += buf[i] * buf[i];
    rms = Math.sqrt(rms / n);
    if (rms < 0.01) return -1;
    
    var maxOff = Math.floor(sr / 50);
    var minOff = Math.floor(sr / 500);
    var bestOff = -1, bestCor = -1;
    
    for (var off = minOff; off < maxOff; off++) {
      var cor = 0;
      for (var i = 0; i < n - off; i++) cor += Math.abs(buf[i] - buf[i + off]);
      cor = 1 - cor / (n - off);
      if (cor > bestCor) { bestCor = cor; bestOff = off; }
    }
    if (bestCor < 0.5) return -1;
    return sr / bestOff;
  },
  
  measureJitter: function(buf, sr, freq) {
    if (freq < 50) return 0;
    var period = Math.round(sr / freq);
    if (period < 2 || period > buf.length / 3) return 0;
    
    var periods = [];
    var threshold = 0.3;
    var lastCross = 0;
    var above = buf[0] > 0;
    
    for (var i = 1; i < buf.length; i++) {
      var nowAbove = buf[i] > threshold;
      if (nowAbove !== above && buf[i] > 0) {
        if (lastCross > 0) periods.push(i - lastCross);
        lastCross = i;
        above = nowAbove;
      }
    }
    
    if (periods.length < 3) return 0;
    var mean = periods.reduce(function(a,b){return a+b;},0) / periods.length;
    var variance = periods.reduce(function(s,p){return s+Math.pow(p-mean,2);},0) / periods.length;
    return Math.sqrt(variance) / mean; // Relative jitter
  },
  
  estimateFormants: function(spectrum, binWidth) {
    // F1: 200-900 Hz peak
    var f1Min = Math.floor(200/binWidth), f1Max = Math.floor(900/binWidth);
    var f1Peak = f1Min, f1Val = -999;
    for (var i = f1Min; i < f1Max; i++) { if (spectrum[i] > f1Val) { f1Val = spectrum[i]; f1Peak = i; }}
    
    // F2: 800-2800 Hz peak
    var f2Min = Math.floor(800/binWidth), f2Max = Math.floor(2800/binWidth);
    var f2Peak = f2Min, f2Val = -999;
    for (var i = f2Min; i < f2Max; i++) { if (spectrum[i] > f2Val) { f2Val = spectrum[i]; f2Peak = i; }}
    
    return { f1: f1Peak * binWidth, f2: f2Peak * binWidth };
  },
  
  spectralTilt: function(spectrum, binWidth, freq) {
    // Measure harmonic rolloff: compare H2 to H6
    var tilt = 0, count = 0;
    for (var h = 2; h <= 6; h++) {
      var bin = Math.round(h * freq / binWidth);
      if (bin < spectrum.length) {
        tilt += (spectrum[bin] || -100) - (spectrum[Math.round((h-1)*freq/binWidth)] || -100);
        count++;
      }
    }
    return count > 0 ? tilt / count : 0;
  },
  
  // ─── SCORING ───
  score: function(analysis) {
    if (!analysis) return null;
    
    var score = {
      pitch: 0, closure: 0, stability: 0, formants: 0, dynamics: 0,
      overall: 0, feedback: '', color: ''
    };
    
    // Pitch accuracy (0-100)
    var absCents = Math.abs(analysis.cents);
    if (absCents < 5) score.pitch = 100;
    else if (absCents < 10) score.pitch = 90;
    else if (absCents < 20) score.pitch = 70;
    else if (absCents < 35) score.pitch = 50;
    else score.pitch = Math.max(0, 100 - absCents);
    
    // Fold closure (H1-H2 ratio) — optimal range 8-14 dB
    var h1h2 = analysis.h1h2;
    if (h1h2 >= 6 && h1h2 <= 16) score.closure = 100;
    else if (h1h2 >= 3 && h1h2 <= 20) score.closure = 70;
    else score.closure = 40;
    
    // Stability (jitter) — < 1% excellent, < 2% good, < 4% fair
    var j = analysis.jitter;
    if (j < 0.01) score.stability = 100;
    else if (j < 0.02) score.stability = 80;
    else if (j < 0.04) score.stability = 60;
    else score.stability = Math.max(0, 100 - j * 1000);
    
    // Formant stability (if we have history)
    if (this.history.length > 5) {
      var recent = this.history.slice(-10);
      var f1SD = this.stdDev(recent.map(function(r){return r.f1;}));
      var f2SD = this.stdDev(recent.map(function(r){return r.f2;}));
      score.formants = Math.max(0, 100 - (f1SD/50 + f2SD/100) * 50);
    } else {
      score.formants = 70; // Default for new sessions
    }
    
    // Dynamics (RMS range)
    var rms = analysis.rms;
    if (rms > 0.05 && rms < 0.3) score.dynamics = 100;
    else if (rms > 0.02 && rms < 0.4) score.dynamics = 70;
    else score.dynamics = 50;
    
    // Overall weighted score
    score.overall = Math.round(
      score.pitch * 0.35 +
      score.closure * 0.20 +
      score.stability * 0.20 +
      score.formants * 0.15 +
      score.dynamics * 0.10
    );
    
    // Feedback
    if (score.overall >= 90) { score.feedback = '🌟 Excellent! Professional quality.'; score.color = 'var(--ok)'; }
    else if (score.overall >= 75) { score.feedback = '✓ Very good. Small refinements needed.'; score.color = 'var(--ok)'; }
    else if (score.overall >= 60) { score.feedback = '→ Getting there. Focus on consistency.'; score.color = 'var(--gold)'; }
    else if (score.overall >= 40) { score.feedback = '↑ Keep practicing. Use the visual feedback.'; score.color = 'var(--warn)'; }
    else { score.feedback = '⟳ Building foundation. Try the beginner exercises.'; score.color = 'var(--err)'; }
    
    return score;
  },
  
  stdDev: function(arr) {
    if (arr.length < 2) return 0;
    var mean = arr.reduce(function(a,b){return a+b;},0) / arr.length;
    return Math.sqrt(arr.reduce(function(s,v){return s+Math.pow(v-mean,2);},0) / arr.length);
  },
  
  // ─── SESSION MANAGEMENT ───
  startSession: function(exerciseId) {
    var exercises = this.exercises[this.level];
    this.session = exercises.find(function(e){return e.id===exerciseId;}) || exercises[0];
    this.history = [];
    this.scores = {attempts:0, inTune:0, streak:0, bestStreak:0};
    return this.session;
  },
  
  recordAnalysis: function(analysis) {
    if (!analysis) return;
    this.history.push(analysis);
    this.scores.attempts++;
    
    if (Math.abs(analysis.cents) < 15) {
      this.scores.inTune++;
      this.scores.streak++;
      if (this.scores.streak > this.scores.bestStreak) this.scores.bestStreak = this.scores.streak;
    } else {
      this.scores.streak = 0;
    }
    
    // Auto-level up check
    if (this.scores.attempts >= 20) {
      var newLevel = this.assessLevel();
      if (newLevel !== this.level) {
        this.level = newLevel;
        return {leveledUp: true, newLevel: newLevel};
      }
    }
    return {leveledUp: false};
  },
  
  getSessionSummary: function() {
    if (this.history.length === 0) return null;
    
    var avgCents = this.history.reduce(function(s,r){return s+Math.abs(r.cents);},0) / this.history.length;
    var avgJitter = this.history.reduce(function(s,r){return s+(r.jitter||0);},0) / this.history.length;
    var inTuneRate = this.scores.inTune / Math.max(1, this.scores.attempts);
    var avgH1H2 = this.history.reduce(function(s,r){return s+r.h1h2;},0) / this.history.length;
    
    return {
      attempts: this.scores.attempts,
      inTune: this.scores.inTune,
      accuracy: Math.round(inTuneRate * 100),
      avgCents: Math.round(avgCents),
      avgJitter: Math.round(avgJitter * 1000) / 10,
      avgH1H2: Math.round(avgH1H2),
      bestStreak: this.scores.bestStreak,
      level: this.level,
      recommendation: this.getRecommendation(avgCents, avgJitter, inTuneRate, avgH1H2)
    };
  },
  
  getRecommendation: function(avgCents, jitter, inTuneRate, h1h2) {
    var recs = [];
    
    if (avgCents > 25) recs.push('Focus on pitch matching — use the visual feedback to see how far off you are.');
    if (jitter > 0.03) recs.push('Work on stability — try SOVTE lip trills to improve fold closure consistency.');
    if (inTuneRate < 0.5) recs.push('Practice single note matching before moving to intervals.');
    if (h1h2 < 5) recs.push('Your voice sounds breathy — try humming to feel the buzz, then open to vowel.');
    if (h1h2 > 18) recs.push('Your voice sounds pressed — relax, use more air flow, less muscle tension.');
    
    if (recs.length === 0) recs.push('Great work! You\'re ready for the next level.');
    
    return recs;
  }
};
