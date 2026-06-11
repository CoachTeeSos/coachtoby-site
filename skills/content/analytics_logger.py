#!/usr/bin/env python3
"""
Analytics Logger - Client Feedback & Campaign Metrics
Appends qualitative and quantitative data to vault/metrics.json
"""
import json, os
from datetime import datetime
from pathlib import Path

VAULT_DIR = Path('/home/user/workspace/vault')
METRICS_FILE = VAULT_DIR / 'metrics.json'

def load_metrics():
    if METRICS_FILE.exists():
        with open(METRICS_FILE) as f:
            return json.load(f)
    return {
        'campaigns': [],
        'emails_sent': [],
        'responses': [],
        'conversions': [],
        'feedback': [],
        'pain_points_discovered': [],
        'locations_targeted': [],
    }

def save_metrics(data):
    with open(METRICS_FILE, 'w') as f:
        json.dump(data, f, indent=2, default=str)

def log_campaign(name, location, emails_sent, responses=0, conversions=0):
    """Log a campaign run."""
    metrics = load_metrics()
    metrics['campaigns'].append({
        'name': name,
        'location': location,
        'emails_sent': emails_sent,
        'responses': responses,
        'conversions': conversions,
        'timestamp': datetime.utcnow().isoformat(),
    })
    save_metrics(metrics)
    print(f"Campaign logged: {name} ({location}) — {emails_sent} sent, {responses} responses, {conversions} conversions")

def log_email_sent(recipient, subject, campaign, status='sent'):
    """Log individual email send."""
    metrics = load_metrics()
    metrics['emails_sent'].append({
        'recipient': recipient,
        'subject': subject,
        'campaign': campaign,
        'status': status,
        'timestamp': datetime.utcnow().isoformat(),
    })
    save_metrics(metrics)

def log_response(recipient, campaign, response_type, content=''):
    """Log a response from a prospect."""
    metrics = load_metrics()
    metrics['responses'].append({
        'recipient': recipient,
        'campaign': campaign,
        'type': response_type,  # 'interested', 'not_interested', 'question', 'booking'
        'content': content,
        'timestamp': datetime.utcnow().isoformat(),
    })
    save_metrics(metrics)

def log_conversion(recipient, campaign, package, value):
    """Log a conversion (sale)."""
    metrics = load_metrics()
    metrics['conversions'].append({
        'recipient': recipient,
        'campaign': campaign,
        'package': package,
        'value': value,
        'timestamp': datetime.utcnow().isoformat(),
    })
    save_metrics(metrics)

def log_feedback(source, content, category='general'):
    """Log qualitative feedback."""
    metrics = load_metrics()
    metrics['feedback'].append({
        'source': source,
        'content': content,
        'category': category,
        'timestamp': datetime.utcnow().isoformat(),
    })
    save_metrics(metrics)

def log_pain_point(pain_point, source='', frequency=1):
    """Log a discovered pain point."""
    metrics = load_metrics()
    # Check if already exists
    for pp in metrics['pain_points_discovered']:
        if pp['point'] == pain_point:
            pp['frequency'] += frequency
            pp['last_seen'] = datetime.utcnow().isoformat()
            save_metrics(metrics)
            return
    metrics['pain_points_discovered'].append({
        'point': pain_point,
        'source': source,
        'frequency': frequency,
        'first_seen': datetime.utcnow().isoformat(),
        'last_seen': datetime.utcnow().isoformat(),
    })
    save_metrics(metrics)

def get_dashboard():
    """Get a summary dashboard of all metrics."""
    metrics = load_metrics()
    
    total_emails = len(metrics['emails_sent'])
    total_responses = len(metrics['responses'])
    total_conversions = len(metrics['conversions'])
    response_rate = (total_responses / total_emails * 100) if total_emails > 0 else 0
    conversion_rate = (total_conversions / total_responses * 100) if total_responses > 0 else 0
    
    return {
        'total_campaigns': len(metrics['campaigns']),
        'total_emails_sent': total_emails,
        'total_responses': total_responses,
        'total_conversions': total_conversions,
        'response_rate': round(response_rate, 2),
        'conversion_rate': round(conversion_rate, 2),
        'top_pain_points': sorted(metrics['pain_points_discovered'], key=lambda x: x['frequency'], reverse=True)[:5],
        'locations_targeted': len(metrics['locations_targeted']),
    }

def print_dashboard():
    """Print a formatted dashboard."""
    dash = get_dashboard()
    print("=== CAMPAIGN DASHBOARD ===")
    print(f"  Campaigns: {dash['total_campaigns']}")
    print(f"  Emails sent: {dash['total_emails_sent']}")
    print(f"  Responses: {dash['total_responses']} ({dash['response_rate']}%)")
    print(f"  Conversions: {dash['total_conversions']} ({dash['conversion_rate']}%)")
    print(f"  Locations: {dash['locations_targeted']}")
    print()
    print("  Top pain points:")
    for pp in dash['top_pain_points']:
        print(f"    - {pp['point'][:60]} (freq: {pp['frequency']})")

if __name__ == '__main__':
    print_dashboard()
