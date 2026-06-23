// ═══════════════════════════════════════════════════════════════════════════
// TIME SIGNATURE MASTERY — Interactive Learning Module
//
// Research Foundation:
// - "Out of the Rhythm Maze" (Teaching Music, Jan 2025): Contextual learning
//   beats abstract rule-memorization for time signatures
// - Magic of Music Ed (2025): Interactive Google Slides approach — students
//   manipulate beats visually, not just read numbers
// - Open Music Theory: Compound meters express divisions, not beats — the top
//   number is divisions per measure, bottom is the note value of each division
// - Humanities LibreTexts: Simple vs compound is about beat DIVISION (2 vs 3),
//   not beat COUNT
// - Beth's Music Classroom: Games-based meter practice accelerates recognition
//
// Pedagogical approach:
// 1. RULES: Understand what the numbers MEAN (not just memorize)
// 2. CALCULATE: Given a time signature, compute beats, divisions, bar length
// 3. IDENTIFY: Hear/see a rhythm → determine the time signature
// 4. APPLY: Sing/play IN the time signature with real-time feedback
// 5. HACK: Know the rules so well you can use ANY time signature intentionally
// ═══════════════════════════════════════════════════════════════════════════

var TimeSigMastery = {
  
  // ─── KNOWLEDGE MODEL ───
  // What a student needs to know about ANY time signature:
  //
  // TOP NUMBER = how many of the bottom note value fit in one bar
  // BOTTOM NOTE = what note value gets one count (4 = quarter, 8 = eighth, etc.)
  //
  // SIMPLE meter: beat divides into 2 (top number = beats per bar)
  //   4/4 = 4 quarter-note beats, each divides into 2 eighths
  //   3/4 = 3 quarter-note beats, each divides into 2 eighths
  //   2/4 = 2 quarter-note beats, each divides into 2 eighths
  //
  // COMPOUND meter: beat divides into 3 (top number = divisions per bar)
  //   6/8 = 6 eighth-note divisions = 2 dotted-quarter beats (each = 3 eighths)
  //   9/8 = 9 eighth-note divisions = 3 dotted-quarter beats
  //   12/8 = 12 eighth-note divisions = 4 dotted-quarter beats
  //
  // The HACK: Once you know the rules, you can figure out ANY time signature.
  //   5/4? 5 quarter-note beats. Simple. Each beat divides into 2.
  //   7/8? 7 eighth-note divisions. Compound feel. Grouped as 2+2+3 or 3+2+2.
  //   6/4? 6 quarter-note divisions. Could be compound (2 groups of 3 quarters).
  
  levels: {
    beginner: {
      title: 'Beginner — Feel the Beat',
      description: 'Learn what time signatures mean. Feel the difference between 4/4, 3/4, and 2/4.',
      exercises: [
        {id: 'ts_b1', name: 'What Do the Numbers Mean?', type: 'lesson',
         content: 'ts_lesson_1'},
        {id: 'ts_b2', name: 'Tap 4/4', type: 'interactive',
         content: 'ts_tap_44'},
        {id: 'ts_b3', name: 'Tap 3/4', type: 'interactive',
         content: 'ts_tap_34'},
        {id: 'ts_b4', name: 'Which Time Signature?', type: 'quiz',
         content: 'ts_quiz_listen'},
        {id: 'ts_b5', name: 'Calculate the Bar', type: 'calculator',
         content: 'ts_calc_simple'}
      ]
    },
    intermediate: {
      title: 'Intermediate — Compound & Odd',
      description: 'Master 6/8, 9/8, 5/4, 7/8. Understand the difference between simple and compound.',
      exercises: [
        {id: 'ts_i1', name: 'Simple vs Compound', type: 'lesson',
         content: 'ts_lesson_2'},
        {id: 'ts_i2', name: 'Tap 6/8', type: 'interactive',
         content: 'ts_tap_68'},
        {id: 'ts_i3', name: 'Odd Meters: 5/4 and 7/8', type: 'lesson',
         content: 'ts_lesson_3'},
        {id: 'ts_i4', name: 'Calculate Any Time Signature', type: 'calculator',
         content: 'ts_calc_any'},
        {id: 'ts_i5', name: 'Identify by Ear', type: 'quiz',
         content: 'ts_quiz_ear_advanced'}
      ]
    },
    advanced: {
      title: 'Advanced — Hack Any Meter',
      description: 'Use any time signature intentionally. Compose and perform in odd and compound meters.',
      exercises: [
        {id: 'ts_a1', name: 'The Universal Rule', type: 'lesson',
         content: 'ts_lesson_4'},
        {id: 'ts_a2', name: 'Compose in 7/8', type: 'interactive',
         content: 'ts_compose_78'},
        {id: 'ts_a3', name: 'Switch Meters Mid-Phrase', type: 'interactive',
         content: 'ts_switch_meters'},
        {id: 'ts_a4', name: 'Real-Time Performance', type: 'performance',
         content: 'ts_performance'}
      ]
    }
  },
  
  // ─── CALCULATION ENGINE ───
  // Given any time signature, compute everything about it
  
  analyze: function(top, bottom) {
    var result = {
      top: top,
      bottom: bottom,
      display: top + '/' + bottom,
      bottomNoteName: this.noteName(bottom),
      isSimple: this.isSimple(top, bottom),
      isCompound: this.isCompound(top, bottom),
      isOdd: this.isOdd(top),
      beatsPerBar: 0,
      beatUnit: 0,
      divisionsPerBar: top,
      divisionNote: bottom,
      barDurationBeats: 0,
      barDurationSeconds: 0, // at given BPM
      grouping: [],
      feel: '',
      examples: []
    };
    
    if (result.isSimple) {
      // Simple: top = beats, bottom = beat unit
      result.beatsPerBar = top;
      result.beatUnit = bottom;
      result.divisionsPerBar = top * 2; // each beat divides into 2
      result.divisionNote = bottom * 2; // eighth if quarter beat
      result.grouping = this.simpleGrouping(top);
      result.feel = this.describeSimpleFeel(top, bottom);
    } else if (result.isCompound) {
      // Compound: top = divisions, bottom = division unit
      // Beat = dotted note (3 divisions)
      var beatCount = top / 3;
      result.beatsPerBar = beatCount;
      result.beatUnit = bottom * 2; // dotted version (3 eighths = dotted quarter)
      result.grouping = this.compoundGrouping(top, bottom);
      result.feel = this.describeCompoundFeel(top, bottom);
    } else {
      // Odd/irregular: mixed grouping
      result.beatsPerBar = top; // approximate
      result.beatUnit = bottom;
      result.grouping = this.oddGrouping(top, bottom);
      result.feel = this.describeOddFeel(top, bottom);
    }
    
    result.examples = this.getExamples(top, bottom);
    return result;
  },
  
  noteName: function(value) {
    var names = {1:'whole', 2:'half', 4:'quarter', 8:'eighth', 16:'sixteenth'};
    return names[value] || '1/' + value;
  },
  
  isSimple: function(top, bottom) {
    // Simple: top is 2, 3, or 4 (beats), beat divides into 2
    return (top === 2 || top === 3 || top === 4) && (bottom === 4 || bottom === 2);
  },
  
  isCompound: function(top, bottom) {
    // Compound: top is divisible by 3 (6, 9, 12), bottom is typically 8
    return top % 3 === 0 && top !== 3 && bottom === 8;
  },
  
  isOdd: function(top) {
    return top === 5 || top === 7 || top === 11;
  },
  
  simpleGrouping: function(top) {
    if (top === 4) return ['STRONG', 'weak', 'MEDIUM', 'weak'];
    if (top === 3) return ['STRONG', 'weak', 'weak'];
    if (top === 2) return ['STRONG', 'weak'];
    return Array(top).fill('beat');
  },
  
  compoundGrouping: function(top, bottom) {
    var beats = top / 3;
    var grouping = [];
    for (var b = 0; b < beats; b++) {
      grouping.push('STRONG');
      grouping.push('weak');
      grouping.push('weak');
    }
    return grouping;
  },
  
  oddGrouping: function(top, bottom) {
    // Common groupings for odd meters
    if (top === 5) return ['STRONG', 'weak', 'MEDIUM', 'weak', 'weak']; // 3+2
    if (top === 7) return ['STRONG', 'weak', 'MEDIUM', 'weak', 'weak', 'weak', 'weak']; // 3+2+2 or 2+2+3
    return Array(top).fill('beat');
  },
  
  describeSimpleFeel: function(top, bottom) {
    if (top === 4 && bottom === 4) return 'The most common meter. Steady, balanced. Walk, march, rock, pop.';
    if (top === 3 && bottom === 4) return 'Waltz feel. Circular, flowing. ONE-two-three, ONE-two-three.';
    if (top === 2 && bottom === 4) return 'March feel. Strong-weak, strong-weak. Fast and driving.';
    if (top === 4 && bottom === 2) return 'Cut time. Fast march. Two big beats per bar.';
    return top + ' beats per bar, ' + this.noteName(bottom) + ' note gets the beat.';
  },
  
  describeCompoundFeel: function(top, bottom) {
    var beats = top / 3;
    if (top === 6 && bottom === 8) return 'Two big beats. Each beat = 3 eighth notes. Rolling, lilting feel.';
    if (top === 9 && bottom === 8) return 'Three big beats. Each beat = 3 eighth notes. Extended waltz.';
    if (top === 12 && bottom === 8) return 'Four big beats. Each beat = 3 eighth notes. Slow, sweeping.';
    return beats + ' beats per bar, dotted ' + this.noteName(bottom*2) + ' gets the beat.';
  },
  
  describeOddFeel: function(top, bottom) {
    if (top === 5 && bottom === 4) return 'Five quarter-note beats. Grouped as 3+2 or 2+3. Unsettled, modern.';
    if (top === 7 && bottom === 8) return 'Seven eighth-note divisions. Grouped as 2+2+3 or 3+2+2. Complex, progressive.';
    if (top === 5 && bottom === 8) return 'Five eighth-note divisions. Asymmetric, folk-influenced.';
    return top + ' ' + this.noteName(bottom) + ' notes per bar. Asymmetric feel.';
  },
  
  getExamples: function(top, bottom) {
    var examples = {
      '4/4': ['Most pop, rock, hip-hop', 'Beatles — "Let It Be"', 'Stevie Wonder — "Superstition"'],
      '3/4': ['Waltzes', 'Beatles — "Man in the Life"', 'Taylor Swift — "Anti-Hero" (verses)'],
      '2/4': ['Marches', 'Polka', 'Fast country'],
      '6/8': ['Irish jigs', 'Beatles — "We Can Work It Out"', 'Toto — "Africa"'],
      '9/8': ['Compound waltz', 'Dave Brubeck — "Blue Rondo"'],
      '12/8': ['Blues shuffle', 'Slow ballads', 'Beatles — "Norwegian Wood"'],
      '5/4': ['Dave Brubeck — "Take Five"', 'Mission Impossible theme', 'Radiohead — "15 Step"'],
      '7/8': ['Pink Floyd — "Money" (7/4)', 'Tool — "Schism"', 'Balkan folk music'],
      '5/8': ['Balkan folk', 'Radiohead — "Pyramid Song" sections']
    };
    return examples[top + '/' + bottom] || ['Explore music in this meter!'];
  },
  
  // ─── INTERACTIVE TAP ENGINE ───
  // Real-time tap detection for rhythm practice
  
  tapSession: null,
  
  startTapSession: function(timeSig, bpm) {
    var analysis = this.analyze(timeSig.top, timeSig.bottom);
    this.tapSession = {
      timeSig: timeSig,
      analysis: analysis,
      bpm: bpm || 120,
      beatDuration: 60 / (bpm || 120) * 1000, // ms per beat
      taps: [], // {timestamp, expectedBeat, deviation}
      startTime: Date.now(),
      currentBeat: 0,
      isRunning: true,
      score: {onTime: 0, early: 0, late: 0, missed: 0}
    };
    return this.tapSession;
  },
  
  recordTap: function() {
    if (!this.tapSession || !this.tapSession.isRunning) return null;
    
    var now = Date.now();
    var elapsed = now - this.tapSession.startTime;
    var beatDur = this.tapSession.beatDuration;
    var currentBeat = elapsed / beatDur;
    var nearestBeat = Math.round(currentBeat);
    var deviation = (currentBeat - nearestBeat) * beatDur; // ms off
    
    var tap = {
      timestamp: now,
      elapsed: elapsed,
      currentBeat: currentBeat,
      nearestBeat: nearestBeat,
      deviation: deviation,
      absDeviation: Math.abs(deviation)
    };
    
    this.tapSession.taps.push(tap);
    this.tapSession.currentBeat = currentBeat;
    
    // Score
    if (tap.absDeviation < 50) this.tapSession.score.onTime++;
    else if (deviation < 0) this.tapSession.score.early++;
    else this.tapSession.score.late++;
    
    return tap;
  },
  
  getTapFeedback: function(tap) {
    if (!tap) return {text: 'Tap the beat!', color: 'var(--tx3)', icon: '👆'};
    
    var dev = tap.absDeviation;
    if (dev < 30) return {text: 'Perfect! 🎯', color: 'var(--ok)', icon: '✓'};
    if (dev < 60) return {text: tap.deviation < 0 ? 'Slightly early' : 'Slightly late', color: 'var(--gold)', icon: '~'};
    if (dev < 100) return {text: tap.deviation < 0 ? 'Too early ↑' : 'Too late ↓', color: 'var(--warn)', icon: '↑'};
    return {text: tap.deviation < 0 ? 'Way too early!' : 'Way too late!', color: 'var(--err)', icon: '✗'};
  },
  
  getTapSummary: function() {
    if (!this.tapSession) return null;
    var s = this.tapSession;
    var total = s.taps.length;
    if (total === 0) return null;
    
    var avgDev = s.taps.reduce(function(sum,t){return sum+t.absDeviation;},0) / total;
    var consistency = Math.max(0, 100 - avgDev / 2);
    
    return {
      totalTaps: total,
      onTime: s.score.onTime,
      early: s.score.early,
      late: s.score.late,
      avgDeviation: Math.round(avgDev),
      consistency: Math.round(consistency),
      bpm: s.bpm,
      timeSig: s.timeSig.display
    };
  },
  
  // ─── QUIZ ENGINE ───
  
  generateQuiz: function(level, count) {
    var questions = [];
    var pool = this.getQuizPool(level);
    
    for (var i = 0; i < Math.min(count || 5, pool.length); i++) {
      var q = pool[Math.floor(Math.random() * pool.length)];
      questions.push(this.formatQuestion(q, level));
    }
    return questions;
  },
  
  getQuizPool: function(level) {
    if (level === 'beginner') {
      return [
        {type: 'identify', ts: {top:4, bottom:4}, question: 'What is the most common time signature in pop music?'},
        {type: 'identify', ts: {top:3, bottom:4}, question: 'A waltz is written in which time signature?'},
        {type: 'calculate', ts: {top:4, bottom:4}, question: 'In 4/4, how many quarter notes fit in one bar?'},
        {type: 'calculate', ts: {top:3, bottom:4}, question: 'In 3/4, how many quarter notes fit in one bar?'},
        {type: 'feel', ts: {top:4, bottom:4}, question: 'Which meter feels like a march: strong-weak-strong-weak?'},
        {type: 'feel', ts: {top:3, bottom:4}, question: 'Which meter feels like a waltz: ONE-two-three?'},
        {type: 'bottom', ts: {top:4, bottom:4}, question: 'In 4/4, what note value gets one beat?'},
        {type: 'bottom', ts: {top:6, bottom:8}, question: 'In 6/8, what note value is each division?'}
      ];
    } else if (level === 'intermediate') {
      return [
        {type: 'compound', ts: {top:6, bottom:8}, question: 'In 6/8, how many BEATS are there per bar? (Hint: each beat = 3 eighth notes)'},
        {type: 'compound', ts: {top:9, bottom:8}, question: 'In 9/8, how many beats per bar?'},
        {type: 'compare', ts: {top:3, bottom:4}, question: 'Is 3/4 the same as 6/8? Why or why not?'},
        {type: 'calculate', ts: {top:6, bottom:8}, question: 'In 6/8, one beat = how many eighth notes?'},
        {type: 'identify', ts: {top:5, bottom:4}, question: 'What makes 5/4 different from 4/4?'},
        {type: 'feel', ts: {top:6, bottom:8}, question: 'Does 6/8 feel like 2 big beats or 6 small beats?'}
      ];
    } else {
      return [
        {type: 'universal', ts: {top:7, bottom:8}, question: 'In 7/8, what are the common beat groupings?'},
        {type: 'universal', ts: {top:5, bottom:4}, question: 'In 5/4, how would you group the beats?'},
        {type: 'compose', ts: {top:7, bottom:8}, question: 'Write a 2-bar rhythm in 7/8 using quarter and eighth notes.'},
        {type: 'analyze', ts: {top:12, bottom:8}, question: '12/8 is compound. How many beats? What note value is the beat?'},
        {type: 'hack', ts: {top:4, bottom:4}, question: 'If you change 4/4 to 4/8, what changes?'},
        {type: 'hack', ts: {top:3, bottom:4}, question: 'If you change 3/4 to 3/8, what changes?'}
      ];
    }
  },
  
  formatQuestion: function(q, level) {
    var analysis = this.analyze(q.ts.top, q.ts.bottom);
    
    if (q.type === 'identify') {
      var options = this.generateOptions(q.ts, 'identify');
      return {
        question: q.question,
        type: 'multiple_choice',
        options: options,
        correct: analysis.display,
        explanation: analysis.display + ': ' + analysis.feel
      };
    } else if (q.type === 'calculate') {
      return {
        question: q.question,
        type: 'number',
        correct: q.ts.top,
        explanation: 'The top number (' + q.ts.top + ') tells you how many ' + analysis.bottomNoteName + ' notes fit in one bar.'
      };
    } else if (q.type === 'compound') {
      var beats = q.ts.top / 3;
      return {
        question: q.question,
        type: 'number',
        correct: beats,
        explanation: 'In compound meter, the top number counts DIVISIONS. Each beat = 3 divisions. So ' + q.ts.top + ' ÷ 3 = ' + beats + ' beats.'
      };
    } else if (q.type === 'feel') {
      return {
        question: q.question,
        type: 'multiple_choice',
        options: ['4/4', '3/4', '6/8', '2/4'],
        correct: analysis.display,
        explanation: analysis.feel
      };
    } else if (q.type === 'compare') {
      return {
        question: q.question,
        type: 'multiple_choice',
        options: [
          'Yes — both have 6 as the top number',
          'No — 3/4 has 3 quarter-note beats, 6/8 has 2 dotted-quarter beats',
          'Yes — both are in 3/4 time',
          'No — 3/4 is compound, 6/8 is simple'
        ],
        correct: 'No — 3/4 has 3 quarter-note beats, 6/8 has 2 dotted-quarter beats',
        explanation: '3/4 is SIMPLE: 3 beats, each divides into 2. 6/8 is COMPOUND: 2 beats, each divides into 3. They FEEL completely different.'
      };
    } else if (q.type === 'universal') {
      return {
        question: q.question,
        type: 'multiple_choice',
        options: q.ts.top === 7 ? ['2+2+3 or 3+2+2', '3+3+1', '2+5', '7 equal beats'] : ['3+2 or 2+3', '5 equal beats', '2+2+1', '4+1'],
        correct: q.ts.top === 7 ? '2+2+3 or 3+2+2' : '3+2 or 2+3',
        explanation: 'Odd meters are grouped into combinations of 2s and 3s. ' + q.ts.top + ' = ' + (q.ts.top === 7 ? '2+2+3 or 3+2+2' : '3+2 or 2+3') + '.'
      };
    } else if (q.type === 'hack') {
      return {
        question: q.question,
        type: 'multiple_choice',
        options: [
          'The tempo doubles',
          'The beat unit changes — same number of counts, but each count is a different note value',
          'Nothing — they are the same',
          'The number of beats changes'
        ],
        correct: 'The beat unit changes — same number of counts, but each count is a different note value',
        explanation: 'The bottom number tells you WHAT NOTE VALUE gets the count. Changing it changes the speed and feel, not the number of counts.'
      };
    }
    
    return {question: q.question, type: 'text', correct: '', explanation: ''};
  },
  
  generateOptions: function(correctTs, type) {
    var all = [
      {top:4, bottom:4}, {top:3, bottom:4}, {top:2, bottom:4},
      {top:6, bottom:8}, {top:9, bottom:8}, {top:12, bottom:8},
      {top:5, bottom:4}, {top:7, bottom:8}, {top:4, bottom:2}
    ];
    
    var options = [correctTs.display || (correctTs.top + '/' + correctTs.bottom)];
    var attempts = 0;
    while (options.length < 4 && attempts < 20) {
      var candidate = all[Math.floor(Math.random() * all.length)];
      var label = candidate.top + '/' + candidate.bottom;
      if (options.indexOf(label) === -1) options.push(label);
      attempts++;
    }
    
    // Shuffle
    for (var i = options.length - 1; i > 0; i--) {
      var j = Math.floor(Math.random() * (i + 1));
      var temp = options[i]; options[i] = options[j]; options[j] = temp;
    }
    
    return options;
  }
};
