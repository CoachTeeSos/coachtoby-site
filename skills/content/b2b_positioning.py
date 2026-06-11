#!/usr/bin/env python3
"""
B2B Positioning Engine - Vocal Coaching Client Acquisition
Scrapes pain points, identifies high-value locations, generates email campaigns.
"""
import json, os, re, requests
from datetime import datetime
from pathlib import Path

VAULT_DIR = Path('/home/user/workspace/vault')
SKILLS_DIR = Path('/home/user/workspace/skills/content')
EXA_KEY = os.environ.get('EXA_API_KEY', 'd52adec4-68c6-4fb5-b0cd-0392f84919a4')

# ── PAIN POINT RESEARCH ─────────────────────────────────────────────────────

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
        {'city': 'San Francisco', 'state': 'CA', 'income_percentile': 97, 'music_scene': 'strong'},
        {'city': 'Nashville', 'state': 'TN', 'income_percentile': 78, 'music_scene': 'elite'},
        {'city': 'Austin', 'state': 'TX', 'income_percentile': 82, 'music_scene': 'strong'},
        {'city': 'Chicago', 'state': 'IL', 'income_percentile': 85, 'music_scene': 'strong'},
        {'city': 'Boston', 'state': 'MA', 'income_percentile': 90, 'music_scene': 'strong'},
        {'city': 'Seattle', 'state': 'WA', 'income_percentile': 88, 'music_scene': 'moderate'},
        {'city': 'Miami', 'state': 'FL', 'income_percentile': 80, 'music_scene': 'strong'},
        {'city': 'Atlanta', 'state': 'GA', 'income_percentile': 83, 'music_scene': 'strong'},
    ],
    'International': [
        {'city': 'London', 'country': 'UK', 'income_percentile': 90, 'music_scene': 'elite'},
        {'city': 'Toronto', 'country': 'Canada', 'income_percentile': 85, 'music_scene': 'strong'},
        {'city': 'Sydney', 'country': 'Australia', 'income_percentile': 88, 'music_scene': 'strong'},
        {'city': 'Dubai', 'country': 'UAE', 'income_percentile': 95, 'music_scene': 'growing'},
        {'city': 'Singapore', 'country': 'Singapore', 'income_percentile': 92, 'music_scene': 'growing'},
        {'city': 'Lagos', 'country': 'Nigeria', 'income_percentile': 75, 'music_scene': 'strong'},
        {'city': 'Mumbai', 'country': 'India', 'income_percentile': 70, 'music_scene': 'strong'},
        {'city': 'Berlin', 'country': 'Germany', 'income_percentile': 85, 'music_scene': 'elite'},
    ],
}

def search_pain_points(query, limit=5):
    """Search for pain point content using exa."""
    try:
        r = requests.post(
            'https://api.exa.ai/search',
            headers={'Authorization': 'Bearer ' + EXA_KEY, 'Content-Type': 'application/json'},
            json={'query': query, 'numResults': limit, 'useAutoprompt': True},
            timeout=15,
        )
        return r.json().get('results', [])
    except:
        return []

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

if __name__ == '__main__':
    targets = get_high_value_targets()
    print("=== HIGH-VALUE TARGETS ===")
    for t in targets[:10]:
        print(f"  {t['city']}, {t.get('state', t.get('country', ''))} — score: {t['score']} | scene: {t['music_scene']}")
