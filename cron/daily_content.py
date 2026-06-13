#!/usr/bin/env python3
"""
daily_content_generator.py
Generates a new daily vocal coaching article for sessions-with-toby-2026.html
Follows the existing content format: high-pain-point topic, story, exercise.
"""

import json
import os
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

# ── Config ──
SITE_DIR = Path(os.environ.get("SITE_DIR", os.path.expanduser("~/workspace/coachtoby-site")))
DAILY_DIR = SITE_DIR / "daily"
MAIN_PAGE = SITE_DIR / "sessions-with-toby-2026.html"
GIT_REPO = SITE_DIR

# ── High-Pain-Point Topics Pool (rotating) ──
TOPICS = [
    {
        "title": "Why Your Voice Cracks on High Notes (And the 2-Minute Fix)",
        "slug": "voice-cracks-high-notes",
        "pain": "Voice cracks and breaks on high notes",
        "bottleneck": "Laryngeal constriction and registration misalignment",
        "exercise": "The Cry Exercise",
        "exercise_desc": "Bypasses the 'trying harder' reflex by engaging the mix voice through emotional connection"
    },
    {
        "title": "Why You Run Out of Air Mid-Phrase (And How to Fix It)",
        "slug": "breath-mid-phrase",
        "pain": "Running out of breath while singing",
        "bottleneck": "Subglottic air pressure misalignment and inefficient breath support",
        "exercise": "The ZH Exercise",
        "exercise_desc": "Trains breath efficiency through controlled phonation"
    },
    {
        "title": "Why Your Voice Sounds Weak in the Morning (And How to Wake It Up)",
        "slug": "morning-voice-warmup",
        "pain": "Weak, froggy morning voice that won't cooperate",
        "bottleneck": "Vocal fold edema from overnight fluid redistribution",
        "exercise": "The Lip Trill Siren",
        "exercise_desc": "Gently re-engages vocal fold closure without strain"
    },
    {
        "title": "Why You Can't Hit That Note (Even Though You Know You Can)",
        "slug": "mental-block-singing",
        "pain": "Mental block preventing you from hitting notes you've hit before",
        "bottleneck": "Psychological tension creating physical constriction",
        "exercise": "The Silent Scream",
        "exercise_desc": "Releases laryngeal tension through subvocalization"
    },
    {
        "title": "Why Your Voice Tires After 10 Minutes of Singing",
        "slug": "vocal-fatigue",
        "pain": "Voice gets tired, hoarse, or weak after short singing sessions",
        "bottleneck": "Muscular tension compensating for poor breath support",
        "exercise": "The Humming Scale",
        "exercise_desc": "Builds efficient vocal fold closure with minimal effort"
    },
    {
        "title": "Why You Sound Different on Recording (And How to Fix It)",
        "slug": "recording-sounds-different",
        "pain": "Your voice sounds nothing like what you hear in your head",
        "bottleneck": "Bone conduction vs. air conduction perception gap",
        "exercise": "The Hand-Cup Test",
        "exercise_desc": "Trains you to hear yourself as others hear you"
    },
    {
        "title": "Why You Can't Sing Loudly Without Straining",
        "slug": "sing-loud-without-strain",
        "pain": "Loud singing always leads to strain and shouting",
        "bottleneck": "Pushing air pressure instead of resonance tuning",
        "exercise": "The NG Exercise",
        "exercise_desc": "Builds resonance without increasing subglottic pressure"
    },
    {
        "title": "Why Your Riffs and Runs Sound Sloppy (And How to Clean Them)",
        "slug": "runs-sloppy",
        "pain": "Riffs and runs lack precision and clarity",
        "bottleneck": "Poor coordination between pitch accuracy and rhythmic timing",
        "exercise": "The Staccato Scale",
        "exercise_desc": "Builds precision through isolated note articulation"
    },
    {
        "title": "Why You Freeze on Stage (And How to Own It)",
        "slug": "stage-fright-freeze",
        "pain": "Stage fright causes you to freeze, forget lyrics, or lose your voice",
        "bottleneck": "Fight-or-flight response hijacking vocal coordination",
        "exercise": "The Power Pose Warmup",
        "exercise_desc": "Resets nervous system before performance"
    },
    {
        "title": "Why Your Voice Doesn't Sound Like 'You' Anymore",
        "slug": "voice-identity",
        "pain": "Your voice doesn't feel like your own — sounds forced or fake",
        "bottleneck": "Over-technique suppressing natural vocal personality",
        "exercise": "The Speak-Sing Bridge",
        "exercise_desc": "Reconnects your natural speaking voice to your singing voice"
    },
    {
        "title": "Why You Can't Sing After Eating (And What to Do About It)",
        "slug": "singing-after-eating",
        "pain": "Voice feels heavy, restricted, or unreliable after meals",
        "bottleneck": "Laryngeal reflux and diaphragmatic restriction from full stomach",
        "exercise": "The Standing Scale",
        "exercise_desc": "Maintains vocal function despite physical restriction"
    },
    {
        "title": "Why Your Harmony Sounds Off (Even When You're on Pitch)",
        "slug": "harmony-off",
        "pain": "Harmonies sound dissonant even when each note is correct",
        "bottleneck": "Frequency interference patterns and overtone clashes",
        "exercise": "The Drone Harmony",
        "exercise_desc": "Trains your ear to lock into harmonic intervals"
    },
    {
        "title": "Why You Can't Sing Low Notes Anymore",
        "slug": "lost-low-notes",
        "pain": "Low notes have disappeared from your range",
        "bottleneck": "Chronic tension in the suprahyoid muscles pulling the larynx up",
        "exercise": "The Yawn-Sigh",
        "exercise_desc": "Releases suprahyoid tension to restore low range"
    },
    {
        "title": "Why Your Voice Breaks When You're Nervous",
        "slug": "nervous-voice-break",
        "pain": "Voice cracks, shakes, or breaks during high-pressure moments",
        "bottleneck": "Adrenaline causing irregular vocal fold vibration",
        "exercise": "The Breath Hold",
        "exercise_desc": "Stabilizes vocal fold vibration under stress"
    },
    {
        "title": "Why You Sound Good in the Shower but Bad Everywhere Else",
        "slug": "shower-singer",
        "pain": "Voice sounds great in the shower but terrible in normal environments",
        "bottleneck": "Acoustic feedback loop and psychological safety of private space",
        "exercise": "The Wall Sing",
        "exercise_desc": "Recreates shower acoustics in any environment"
    },
    {
        "title": "Why Your Voice Hurts After Singing (And How to Prevent It)",
        "slug": "voice-hurts-after-singing",
        "pain": "Throat pain, soreness, or fatigue after singing sessions",
        "bottleneck": "Muscular tension and vocal fold trauma from poor technique",
        "exercise": "The Silent Rest",
        "exercise_desc": "Proper vocal recovery protocol"
    },
    {
        "title": "Why You Can't Sing and Play Guitar at the Same Time",
        "slug": "sing-and-play",
        "pain": "Can't coordinate singing with instrument playing",
        "bottleneck": "Cognitive overload splitting attention between two motor tasks",
        "exercise": "The Strum-Hum",
        "exercise_desc": "Builds automaticity through progressive coordination"
    },
    {
        "title": "Why Your Voice Sounds Thin (And How to Add Power)",
        "slug": "thin-voice",
        "pain": "Voice lacks power, projection, and fullness",
        "bottleneck": "Insufficient vocal fold closure and resonance tuning",
        "exercise": "The Mum Exercise",
        "exercise_desc": "Builds vocal fold closure and forward resonance"
    },
    {
        "title": "Why You Can't Hold a Note for More Than 5 Seconds",
        "slug": "cant-hold-notes",
        "pain": "Notes die out quickly — can't sustain phrases",
        "bottleneck": "Air wastage from incomplete vocal fold closure",
        "exercise": "The Sustained Sss",
        "exercise_desc": "Trains efficient air management for sustained phonation"
    },
    {
        "title": "Why Your Voice Sounds Different on Video Calls",
        "slug": "video-call-voice",
        "pain": "Voice sounds flat, thin, or unnatural on Zoom/Teams calls",
        "bottleneck": "Audio compression and lack of room acoustics",
        "exercise": "The Close-Mic Technique",
        "exercise_desc": "Optimizes voice for digital transmission"
    },
    {
        "title": "Why You Can't Sing After a Cold (Even When You Feel Fine)",
        "slug": "singing-after-cold",
        "pain": "Voice doesn't fully recover after illness",
        "bottleneck": "Residual vocal fold edema and compensatory muscle tension",
        "exercise": "The Gentle Siren",
        "exercise_desc": "Safely re-engages full range after vocal illness"
    },
    {
        "title": "Why Your Voice Cracks When You're Tired",
        "slug": "tired-voice-cracks",
        "pain": "Voice becomes unreliable when fatigued",
        "bottleneck": "Reduced neuromuscular coordination under fatigue",
        "exercise": "The Energy Scale",
        "exercise_desc": "Maintains vocal coordination despite physical fatigue"
    },
    {
        "title": "Why You Can't Sing in Tune (Even Though You Think You Can)",
        "slug": "sing-in-tune",
        "pain": "Pitch accuracy issues — can't tell if you're on key",
        "bottleneck": "Poor auditory-motor feedback loop",
        "exercise": "The Drone Pitch",
        "exercise_desc": "Trains real-time pitch correction through reference tones"
    },
    {
        "title": "Why Your Voice Sounds Nasal (And How to Fix It)",
        "slug": "nasal-voice",
        "pain": "Voice has an unwanted nasal quality",
        "bottleneck": "Excessive nasality from improper velopharyngeal closure",
        "exercise": "The K-G Exercise",
        "exercise_desc": "Trains proper velopharyngeal closure for clear tone"
    },
    {
        "title": "Why You Can't Sing Loudly in Small Rooms",
        "slug": "loud-small-rooms",
        "pain": "Voice feels overwhelming or distorted in small spaces",
        "bottleneck": "Acoustic feedback causing compensatory tension",
        "exercise": "The Intimate Scale",
        "exercise_desc": "Adapts vocal projection to room acoustics"
    },
    {
        "title": "Why Your Voice Breaks When You Yawn and Sing",
        "slug": "yawn-sing-break",
        "pain": "Combining yawning with singing causes voice breaks",
        "bottleneck": "Conflicting laryngeal positions between yawn and phonation",
        "exercise": "The Half-Yawn",
        "exercise_desc": "Captures the benefits of yawning without the break"
    },
    {
        "title": "Why You Can't Sing After Drinking Water",
        "slug": "water-before-singing",
        "pain": "Voice feels worse immediately after drinking water",
        "bottleneck": "Water on vocal folds temporarily disrupting closure",
        "exercise": "The Hydration Protocol",
        "exercise_desc": "Proper hydration timing for optimal vocal function"
    },
    {
        "title": "Why Your Voice Sounds Good Alone but Bad in a Group",
        "slug": "solo-vs-group",
        "pain": "Voice blends poorly or gets lost in group singing",
        "bottleneck": "Lack of blend technique and volume matching",
        "exercise": "The Blend Drone",
        "exercise_desc": "Trains voice to match and blend with other voices"
    },
    {
        "title": "Why You Can't Sing the Way You Did 5 Years Ago",
        "slug": "lost-vocal-ability",
        "pain": "Voice has declined despite no obvious cause",
        "bottleneck": "Accumulated compensatory patterns replacing natural technique",
        "exercise": "The Reset Protocol",
        "exercise_desc": "Systematically identifies and removes compensatory patterns"
    }
]


def get_next_topic():
    """Get the next topic based on day-of-year rotation."""
    day_of_year = datetime.now().timetuple().tm_yday
    return day_of_year % len(TOPICS)


def generate_daily_page(topic, date_str):
    """Generate a full daily content page following the existing format."""
    day_num = datetime.now().timetuple().tm_yday
    slug = topic['slug']
    
    html = f'''<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width,initial-scale=1.0">
<title>{topic['title']} — Sessions with Toby</title>
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@400;600;700;800&display=swap" rel="stylesheet">
<style>
:root {{
    --bg-canvas: #0D0E12;
    --bg-surface: #161820;
    --border-subtle: #242838;
    --text-primary: #F4F5F7;
    --text-secondary: #9FA6B5;
    --brand-accent: #E4B34F;
    --brand-kinetic: #00E5A3;
    --font-display: 'Plus Jakarta Sans', 'Inter', system-ui, sans-serif;
    --font-body: 'Inter', system-ui, sans-serif;
}}
*{{box-sizing:border-box;margin:0;padding:0}}
body{{background-color:var(--bg-canvas);color:var(--text-primary);font-family:var(--font-body);letter-spacing:-0.01em;line-height:1.6}}
h1,h2,h3{{font-family:var(--font-display);font-weight:700;letter-spacing:-0.03em;color:var(--text-primary)}}
.wrap{{max-width:700px;margin:0 auto}}
.date-bar{{background:var(--bg-surface);padding:12px 32px;text-align:center;color:var(--text-secondary);font-size:0.8rem;border-bottom:1px solid var(--border-subtle)}}
.hero{{background:linear-gradient(135deg,var(--bg-canvas) 0%,#1a1a2e 100%);padding:56px 32px;text-align:center;border-bottom:2px solid var(--brand-accent)}}
.hero .trust{{font-size:0.75rem;color:var(--text-secondary);margin-bottom:24px;letter-spacing:2px;text-transform:uppercase;font-family:var(--font-body)}}
.hero .trust span{{color:var(--brand-accent);font-weight:600}}
.hero h1{{font-size:2.6rem;margin-bottom:16px;line-height:1.15}}
.hero h1 span{{color:var(--brand-accent)}}
.hero .sub{{font-size:1.05rem;color:var(--text-secondary);max-width:560px;margin:0 auto 28px;line-height:1.7}}
.cta-btn{{display:inline-block;background:var(--brand-accent);color:var(--bg-canvas);padding:18px 44px;border-radius:8px;font-size:1.05rem;font-weight:700;text-decoration:none;border:none;cursor:pointer;transition:transform 0.2s cubic-bezier(0.16,1,0.3,1),box-shadow 0.2s ease;font-family:var(--font-display);box-shadow:0 4px 14px rgba(228,179,79,0.15)}}
.cta-btn:hover{{transform:translateY(-2px);box-shadow:0 6px 20px rgba(228,179,79,0.25)}}
.friction{{background:var(--bg-canvas);padding:48px 32px}}
.friction h2{{font-size:1.4rem;color:var(--brand-accent);margin-bottom:24px}}
.bottleneck{{display:flex;align-items:flex-start;gap:16px;margin-bottom:16px;padding:20px;background:var(--bg-surface);border-radius:12px;border:1px solid var(--border-subtle);border-left:3px solid var(--brand-accent);transition:border-color 0.2s ease}}
.bottleneck:hover{{border-color:var(--brand-accent)}}
.bottle-num{{color:var(--brand-accent);font-weight:800;font-size:1.1rem;min-width:28px;font-family:var(--font-display)}}
.bottle-text{{color:var(--text-secondary);font-size:0.95rem}}
.bottle-text strong{{color:var(--text-primary)}}
.pedagogy{{background:var(--bg-surface);padding:48px 32px}}
.pedagogy h2{{font-size:1.4rem;color:var(--text-primary);margin-bottom:8px}}
.pedagogy .subtitle{{color:var(--text-secondary);margin-bottom:28px;font-size:0.9rem}}
.grid{{display:grid;grid-template-columns:1fr 1fr;gap:16px}}
.premium-card{{background:var(--bg-canvas);border:1px solid var(--border-subtle);border-radius:12px;padding:24px;transition:transform 0.2s cubic-bezier(0.16,1,0.3,1),border-color 0.2s ease}}
.premium-card:hover{{border-color:var(--brand-accent);transform:translateY(-2px)}}
.premium-card h3{{color:var(--brand-accent);font-size:0.95rem;margin-bottom:10px}}
.premium-card p{{color:var(--text-secondary);font-size:0.85rem;line-height:1.6}}
.premium-card.software h3{{color:var(--brand-kinetic)}}
.premium-card.software:hover{{border-color:var(--brand-kinetic)}}
.transform{{background:var(--bg-canvas);padding:48px 32px}}
.transform h2{{font-size:1.4rem;color:var(--text-primary);margin-bottom:28px;text-align:center}}
.before-after{{display:grid;grid-template-columns:1fr 1fr;gap:16px;margin-bottom:24px}}
.ba-box{{padding:24px;border-radius:12px;text-align:center}}
.before{{background:var(--bg-surface);border:1px solid var(--border-subtle)}}
.after{{background:var(--bg-surface);border:1px solid var(--brand-kinetic)}}
.ba-box .label{{font-size:0.7rem;text-transform:uppercase;letter-spacing:2px;margin-bottom:12px;font-weight:600}}
.before .label{{color:var(--text-secondary)}}
.after .label{{color:var(--brand-kinetic)}}
.ba-box p{{color:var(--text-secondary);font-size:0.9rem;margin-bottom:8px}}
.ba-box.after p{{color:var(--text-primary)}}
.story-section{{background:linear-gradient(180deg,var(--bg-canvas),var(--bg-surface));padding:48px 32px}}
.story-section h2{{font-size:1.4rem;color:var(--brand-accent);margin-bottom:24px}}
.story-text{{color:var(--text-secondary);margin-bottom:16px;font-size:0.95rem}}
.story-text .hl{{color:var(--brand-accent);font-weight:700}}
.story-text .warn{{color:var(--text-primary);font-weight:700}}
.exercise{{background:var(--bg-canvas);border:1px solid var(--brand-accent);padding:28px;border-radius:12px;margin:28px 0}}
.exercise h3{{color:var(--brand-accent);font-size:1.05rem;margin-bottom:18px}}
.step{{display:flex;gap:14px;margin-bottom:14px;align-items:flex-start}}
.step-num{{background:var(--brand-accent);color:var(--bg-canvas);width:28px;height:28px;border-radius:50%;display:flex;align-items:center;justify-content:center;font-weight:800;font-size:0.8rem;min-width:28px;font-family:var(--font-display)}}
.step-text{{color:var(--text-secondary);font-size:0.9rem;padding-top:4px}}
.step-text strong{{color:var(--text-primary)}}
.timer{{text-align:center;color:var(--text-secondary);font-size:0.8rem;margin-top:16px}}
.friction-reducer{{background:var(--bg-surface);padding:48px 32px;text-align:center}}
.friction-reducer h2{{font-size:1.4rem;color:var(--text-primary);margin-bottom:12px}}
.guarantee{{background:var(--bg-canvas);border:1px solid var(--brand-kinetic);padding:16px 24px;border-radius:8px;margin:20px auto;display:inline-block}}
.guarantee span{{color:var(--brand-kinetic);font-weight:700}}
.friction-reducer p.description{{color:var(--text-secondary);font-size:0.9rem;margin-bottom:28px;max-width:480px;margin-left:auto;margin-right:auto}}
.form-wrap{{max-width:400px;margin:0 auto}}
.form-wrap input{{width:100%;padding:14px 16px;margin:6px 0;border:1px solid var(--border-subtle);border-radius:8px;font-size:0.95rem;background:var(--bg-canvas);color:var(--text-primary);font-family:var(--font-body);transition:border-color 0.2s ease}}
.form-wrap input::placeholder{{color:var(--text-secondary)}}
.form-wrap input:focus{{outline:none;border-color:var(--brand-accent)}}
.form-wrap button{{width:100%;padding:16px;background:var(--brand-accent);color:var(--bg-canvas);border:none;border-radius:8px;font-size:1.05rem;font-weight:700;cursor:pointer;margin-top:10px;font-family:var(--font-display);transition:transform 0.2s cubic-bezier(0.16,1,0.3,1),box-shadow 0.2s ease;box-shadow:0 4px 14px rgba(228,179,79,0.15)}}
.form-wrap button:hover{{transform:translateY(-2px);box-shadow:0 6px 20px rgba(228,179,79,0.25)}}
.form-note{{font-size:0.75rem;color:var(--text-secondary);margin-top:14px}}
.footer{{background:var(--bg-canvas);padding:32px;text-align:center;border-top:1px solid var(--border-subtle)}}
.footer p{{color:var(--text-secondary);font-size:0.8rem}}
.footer a{{color:var(--brand-accent);text-decoration:none}}
@media(max-width:600px){{.grid,.before-after{{grid-template-columns:1fr}}.hero h1{{font-size:2rem}}.hero{{padding:40px 20px}}.friction,.pedagogy,.transform,.story-section,.friction-reducer{{padding:36px 20px}}}}
</style>
</head>
<body>

<div class="date-bar">{date_str} · Day {day_num} of 365</div>

<!-- HERO -->
<div class="hero">
<div class="trust"><span>PROVEN VOCAL SCIENCE</span> // 50+ STUDENTS COACHED</div>
<h1>{topic['title']}</h1>
<p class="sub">The definitive hardware-software vocal blueprint for elite vocalists, performers, and public speakers. Break through physical bottlenecks and secure predictable, structural vocal stability within 30 days.</p>
<a href="#training" class="cta-btn">Start Your Daily Training →</a>
</div>

<!-- BIOLOGICAL FRICTION -->
<div class="friction">
<h2>Physiological Bottlenecks Restricting Your True Vocal Range</h2>
<div class="bottleneck">
<div class="bottle-num">01</div>
<div class="bottle-text"><strong>{topic['bottleneck'].split('—')[0].strip()}</strong> — {topic['bottleneck'].split('—')[1].strip() if '—' in topic['bottleneck'] else topic['bottleneck']}</div>
</div>
<div class="bottleneck">
<div class="bottle-num">02</div>
<div class="bottle-text"><strong>Compensatory tension patterns</strong> — Your body has developed workarounds that feel normal but are silently limiting your range and power.</div>
</div>
<div class="bottleneck">
<div class="bottle-num">03</div>
<div class="bottle-text"><strong>Auditory-motor disconnect</strong> — What you hear in your head doesn't match what's actually coming out. The gap between perception and output is where most singers get stuck.</div>
</div>
</div>

<!-- PEDAGOGY GRID -->
<div class="pedagogy">
<h2>The Hardware-Software Blueprint</h2>
<p class="subtitle">Every voice has two systems. Most teachers only address one.</p>
<div class="grid">
<div class="premium-card hardware">
<h3>HARDWARE (Physical)</h3>
<p>Breath support & appoggio. Vocal fold closure. Laryngeal positioning. Resonance tuning. Articulator shaping.</p>
<p style="margin-top:10px;font-size:0.8rem;color:var(--text-secondary)">The instrument itself — the physical mechanisms that produce sound.</p>
</div>
<div class="premium-card software">
<h3>SOFTWARE (Coordination)</h3>
<p>Registration blending (chest/mix/head). Dynamic control. Vowel modification. Style-specific coordination (belt, legit, mix).</p>
<p style="margin-top:10px;font-size:0.8rem;color:var(--text-secondary)">How you play the instrument — the patterns that make it sing.</p>
</div>
</div>
</div>

<!-- TRANSFORMATION -->
<div class="transform">
<h2>What Changes When Both Systems Work</h2>
<div class="before-after">
<div class="ba-box before">
<div class="label">BEFORE</div>
<p>{topic['pain']}</p>
<p>Compensating with tension</p>
<p>Unpredictable results</p>
<p>Fear of the next note</p>
</div>
<div class="ba-box after">
<div class="label">AFTER</div>
<p>Controlled, reliable technique</p>
<p>Efficient, effortless production</p>
<p>Predictable every time</p>
<p>Confidence on demand</p>
</div>
</div>
</div>

<!-- STORY + EXERCISE -->
<div class="story-section">
<h2>The Singer Who Couldn't {topic['pain'].split('(')[0].strip()}</h2>
<p class="story-text">They'd been struggling with this for <span class="hl">years</span>. YouTube tutorials. Different coaches. Breathing exercises that didn't translate to actual singing.</p>
<p class="story-text">The problem wasn't effort. It wasn't talent. It was <span class="warn">{topic['bottleneck'].split('—')[0].strip().lower()}</span> — a mechanical issue that no amount of "trying harder" could fix.</p>
<p class="story-text">Once they learned the right protocol — the one that addresses the actual bottleneck — everything changed. <span class="hl">Within 2 weeks</span>, they were hitting notes they'd never reached before. Without strain. Without fear.</p>

<div class="exercise">
<h3>{topic['exercise']} (2 minutes)</h3>
<p style="color:var(--text-secondary);font-size:0.85rem;margin-bottom:18px">{topic['exercise_desc']}</p>
<div class="step"><div class="step-num">1</div><div class="step-text"><strong>Find your starting note.</strong> Hum the lowest comfortable note in your range.</div></div>
<div class="step"><div class="step-num">2</div><div class="step-text"><strong>Apply the technique.</strong> {topic['exercise_desc']}. Focus on the sensation, not the sound.</div></div>
<div class="step"><div class="step-num">3</div><div class="step-text"><strong>Scale up slowly.</strong> Move up by half-steps. Stop before you feel tension.</div></div>
<div class="step"><div class="step-num">4</div><div class="step-text"><strong>Notice the shift.</strong> The breakthrough happens when you stop trying and start allowing.</div></div>
<div class="timer">2 minutes · Do this 3x daily for 1 week</div>
</div>
</div>

<!-- FRICTION REDUCER -->
<div class="friction-reducer" id="training">
<h2>Get a New Exercise Every Day</h2>
<div class="guarantee">✓ <span>Free 7-Day Vocal Training</span> — One targeted exercise delivered to your inbox daily.</div>
<p class="description">Enter your name and email. You'll get today's exercise immediately, plus a new one every day. Each one targets a specific bottleneck.</p>
<div class="form-wrap">
<a href="https://coachteesos.github.io/coachtoby-site/sessions-with-toby-2026.html" class="cta-btn" style="display:block;text-align:center;text-decoration:none">Read Today's Full Article →</a>
<p class="form-note">A 2-minute conversation about your voice. I'll send you exercises tailored to your exact struggle.</p>
</div>
</div>

<!-- FOOTER -->
<div class="footer">
<p>Sessions with Toby · Vocal Coaching · <a href="https://coachteesos.github.io/coachtoby-site/">coachteesos.github.io/coachtoby-site</a></p>
</div>

<script>
document.getElementById('date').textContent = new Date().toLocaleDateString('en-US',{{weekday:'long',year:'numeric',month:'long',day:'numeric'}});
</script>
</body>
</html>'''
    return html


def main():
    today = datetime.now()
    date_str = today.strftime('%A, %B %d, %Y')
    slug_date = today.strftime('%Y-%m-%d')
    
    topic_idx = get_next_topic()
    topic = TOPICS[topic_idx]
    
    # Generate the daily page
    html_content = generate_daily_page(topic, date_str)
    
    # Write the daily page
    daily_filename = f"{slug_date}-{topic['slug']}.html"
    daily_path = DAILY_DIR / daily_filename
    daily_path.write_text(html_content)
    print(f"✅ Generated: {daily_path}")
    
    # Update the main sessions-with-toby page to link to this article
    update_main_page(topic, daily_filename, date_str)
    
    # Git commit and push
    git_commit_push(daily_filename, topic['title'])
    
    print(f"✅ Daily content published: {topic['title']}")


def update_main_page(topic, daily_filename, date_str):
    """Update the main sessions-with-toby-2026.html to feature today's article."""
    import re
    
    if not MAIN_PAGE.exists():
        print("⚠️ Main page not found, skipping update")
        return
    
    content = MAIN_PAGE.read_text()
    
    # Update the date bar — replace everything between <div class="date-bar"> and </div>
    content = re.sub(
        r'<div class="date-bar">.*?</div>',
        f'<div class="date-bar">{date_str} · Day {datetime.now().timetuple().tm_yday} of 365</div>',
        content,
        flags=re.DOTALL
    )
    
    # Update the hero title
    content = re.sub(
        r'<h1>.*?</h1>',
        f'<h1>{topic["title"]}</h1>',
        content,
        count=1
    )
    
    # Update the CTA link to point to today's article
    content = re.sub(
        r'href="daily/[^"]*"',
        f'href="daily/{daily_filename}"',
        content
    )
    
    MAIN_PAGE.write_text(content)
    print(f"✅ Updated main page: {MAIN_PAGE}")


def git_commit_push(filename, title):
    """Commit and push to GitHub."""
    os.chdir(GIT_REPO)
    subprocess.run(['git', 'add', '.'], capture_output=True)
    result = subprocess.run(
        ['git', 'commit', '-m', f'Daily content: {title}'],
        capture_output=True, text=True
    )
    if 'nothing to commit' in result.stdout:
        print("ℹ️ Nothing to commit")
        return
    push_result = subprocess.run(['git', 'push', 'origin', 'main'], capture_output=True, text=True)
    if push_result.returncode == 0:
        print("✅ Pushed to GitHub")
    else:
        print(f"⚠️ Push failed: {push_result.stderr}")


if __name__ == '__main__':
    main()
