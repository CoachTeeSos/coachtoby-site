#!/usr/bin/env python3
"""
B2B Positioning Engine - Vocal Coaching Client Acquisition.
Note: Exa search integration removed. Use manual research or set EXA_API_KEY env var.
"""
import json, os
from datetime import datetime
from pathlib import Path

VAULT_DIR = Path.home() / '.hermes' / 'vault'
SKILLS_DIR = Path(__file__).parent

# ── PAIN POINT RESEARCH (built-in, no API needed) ──

PAIN_POINTS = {
    'technical': [
        "Can't hit high notes without straining",
        "Voice cracks and breaks in passaggio",
        "Breath runs out mid-phrase",
        "Can't find mix voice — stuck in chest or head",
        "Vocal fatigue after short singing sessions",
        "Inconsistent tone quality across range",
    ],
    'psychological': [
        "Embarrassed to sing in front of others",
        "Told they 'can't sing' as a child",
        "Compare themselves to professional singers",
        "Fear of judgment in group classes",
        "Imposter syndrome — 'I'm not a real singer'",
        "Perfectionism preventing progress",
    ],
    'practical': [
        "No time for consistent practice",
        "Can't afford private lessons",
        "Don't know where to start",
        "Tried YouTube tutorials — no progress",
        "Previous teacher didn't help",
        "Can't find a teacher who understands their style",
    ],
}

HIGH_VALUE_LOCATIONS = {
    'US': [
        {'city': 'New York', 'state': 'NY', 'income_percentile': 95, 'music_scene': 'elite'},
        {'city': 'Los Angeles', 'state': 'CA', 'income_percentile': 92, 'music_scene': 'elite'},
        {'city': 'Nashville', 'state': 'TN', 'income_percentile': 78, 'music_scene': 'elite'},
        {'city': 'Atlanta', 'state': 'GA', 'income_percentile': 83, 'music_scene': 'strong'},
    ],
    'International': [
        {'city': 'London', 'country': 'UK', 'income_percentile': 90, 'music_scene': 'elite'},
        {'city': 'Toronto', 'country': 'Canada', 'income_percentile': 85, 'music_scene': 'strong'},
        {'city': 'Lagos', 'country': 'Nigeria', 'income_percentile': 75, 'music_scene': 'strong'},
        {'city': 'Dubai', 'country': 'UAE', 'income_percentile': 95, 'music_scene': 'growing'},
    ],
}

def get_high_value_targets():
    """Return prioritized list of high-value locations."""
    targets = []
    for region, cities in HIGH_VALUE_LOCATIONS.items():
        for city in cities:
            score = (city['income_percentile'] * 0.6) + (100 if city['music_scene'] == 'elite' else 70 if city['music_scene'] == 'strong' else 50) * 0.4
            city['score'] = round(score, 1)
            city['region'] = region
            targets.append(city)
    targets.sort(key=lambda x: x['score'], reverse=True)
    return targets

def get_pain_points():
    """Return all known pain points organized by category."""
    return PAIN_POINTS

if __name__ == '__main__':
    targets = get_high_value_targets()
    print("=== HIGH-VALUE TARGETS ===")
    for t in targets[:10]:
        print(f"  {t['city']}, {t.get('state', t.get('country', ''))} — score: {t['score']} | scene: {t['music_scene']}")
    print(f"\n=== PAIN POINTS ({sum(len(v) for v in PAIN_POINTS.values())} total) ===")
    for category, points in PAIN_POINTS.items():
        print(f"\n  {category.upper()}:")
        for p in points:
            print(f"    • {p}")
