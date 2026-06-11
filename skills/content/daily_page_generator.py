#!/usr/bin/env python3
"""
Daily Content Page Generator
Generates a blog-style page with storytelling + executable actions.
Optimized for attention span (short sections, scannable).
"""
import json, os
from datetime import datetime
from pathlib import Path

PEDAGOGY_DIR = Path('/home/user/workspace/pedagogy')

def load_pedagogy():
    refs = {}
    for f in PEDAGOGY_DIR.glob('*.md'):
        with open(f) as fh:
            refs[f.stem] = fh.read()
    return refs

def generate_daily_page(topic, pain_point, exercise, day_number):
    """Generate a complete daily content page."""
    
    page = f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width,initial-scale=1.0">
<title>{topic} — Sessions with Toby</title>
<style>
body{{font-family:Inter,Arial,sans-serif;max-width:700px;margin:0 auto;padding:24px;color:#1a1a1a;line-height:1.6}}
h1{{color:#004B49;font-size:1.8rem;margin-bottom:0.5rem}}
h2{{color:#004B49;font-size:1.3rem;margin-top:2rem}}
.story{{background:#F0F9FF;border-left:4px solid #0EA5E9;padding:16px;margin:16px 0;border-radius:0 8px 8px 0}}
.action{{background:#FEF3C7;border-left:4px solid #F59E0B;padding:16px;margin:16px 0;border-radius:0 8px 8px 0}}
.step{{background:#F0FDF4;border-left:4px solid #22C55E;padding:12px;margin:8px 0;border-radius:0 8px 8px 0}}
.cta{{background:#004B49;color:#fff;padding:20px;text-align:center;border-radius:12px;margin:24px 0}}
.cta a{{color:#FFD700;text-decoration:none;font-weight:700}}
.timer{{font-size:0.85rem;color:#666;text-align:center;margin-top:8px}}
</style>
</head>
<body>

<h1>{topic}</h1>
<p style="color:#666;font-size:0.9rem">Day {day_number} · Sessions with Toby</p>

<div class="story">
<h2>🎭 The Story</h2>
<p>Sarah had been singing for 5 years. She could belt in the shower, hit most notes in her range, and even performed at a local open mic. But every time she tried to sing in front of others, her voice would crack on the high notes. She'd feel her throat tighten, her breath run out, and the embarrassment would wash over her.</p>
<p>"I thought I just wasn't talented enough," she told me during our first session. "Everyone else makes it look so easy."</p>
<p>Here's what I told Sarah: <strong>Your voice isn't broken. Your coordination is.</strong></p>
</div>

<h2>🔍 The Problem: {pain_point}</h2>
<p>This is the #1 issue I see with singers. It's not about talent. It's about coordination — specifically, how your vocal folds, breath, and resonance work together.</p>
<p>Most singers try to <em>push harder</em> when they hit a wall. But that's like pressing the gas pedal harder when your car won't go faster. The problem isn't power — it's the gear you're in.</p>

<div class="action">
<h2>⚡ The Fix: {exercise}</h2>
<p>Try this right now. It takes 2 minutes.</p>

<div class="step">
<strong>Step 1:</strong> Think of a sad movie moment. Feel the "sob" in your chest.
</div>
<div class="step">
<strong>Step 2:</strong> Say "Wah" (like a baby crying) on a comfortable pitch. Feel the cry-like quality.
</div>
<div class="step">
<strong>Step 3:</strong> Sing "Wah" on a 5-tone scale: 1-2-3-4-5-4-3-2-1
</div>
<div class="step">
<strong>Step 4:</strong> Notice how the high notes feel easier. That's your mix voice engaging.
</div>

<p class="timer">⏱️ Time: 2 minutes · Do this 3x daily for a week</p>
</div>

<h2>💡 Why This Works</h2>
<p>The "cry" coordination engages your mix voice — the registration that lets you sing high notes without straining. It's not about pushing. It's about <em>allowing</em>.</p>
<p>When you feel the "sob," your vocal folds thin out naturally, your larynx stays neutral, and your resonance shifts forward. That's the coordination that professional singers use instinctively.</p>

<div class="cta">
<h2>🚀 Ready to Transform Your Voice?</h2>
<p>Free content can only take you so far. If you want personalized feedback and a customized training plan, I have a few spots open this month.</p>
<p><a href="https://coachteesos.github.io/coachtoby-site/book.html">Book a Free Vocal Assessment →</a></p>
<p style="font-size:0.85rem;margin-top:12px">No pressure. Just a conversation about your voice and where you want to go.</p>
</div>

<hr style="margin:32px 0;border:1px solid #e2e8f0">
<p style="font-size:0.8rem;color:#666;text-align-center">Sessions with Toby · Vocal Coaching · <a href="https://coachteesos.github.io/coachtoby-site/">coachteesos.github.io/coachtoby-site</a></p>

</body>
</html>"""
    
    return page

def save_daily_page(topic, content):
    """Save the daily page to the site."""
    today = datetime.utcnow().strftime('%Y-%m-%d')
    safe_topic = topic.lower().replace(' ', '_')[:30]
    filename = f"{today}-{safe_topic}.html"
    
    output_dir = Path('/home/user/workspace/docs/daily-pages')
    output_dir.mkdir(exist_ok=True)
    
    filepath = output_dir / filename
    with open(filepath, 'w') as f:
        f.write(content)
    
    print(f"Page saved: {filepath}")
    return filepath

if __name__ == '__main__':
    # Test generate a page
    page = generate_daily_page(
        topic="Why Your Voice Cracks (And How to Fix It)",
        pain_point="Voice cracks and breaks in the passaggio",
        exercise="The 'Cry' Exercise",
        day_number=1,
    )
    filepath = save_daily_page("voice-cracks-fix", page)
    print(f"Generated: {filepath}")
