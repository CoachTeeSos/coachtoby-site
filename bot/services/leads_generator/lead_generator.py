"""
services/lead_generator.py — Autonomous lead generation for Sessions with Toby.
Searches social platforms daily, finds people looking for vocal/life coaching,
qualifies them, and saves to Airtable. Sends daily summary to admin via Telegram.
"""
import os
import logging
import json
import re
import requests
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)

# ── CONFIG ──
AIRTABLE_PAT = os.getenv("AIRTABLE_PAT", "")
AIRTABLE_BASE_ID = os.getenv("AIRTABLE_BASE_ID", "app3N2MFPvfDSuYxk")
AIRTABLE_LEADS_TABLE = "Leads"
BOT_TOKEN = os.getenv("BOT2_TOKEN", "")  # For sending summaries to admin
ADMIN_TG_ID = os.getenv("ADMIN_TG_ID", "1688731002")

# Search keywords that signal someone needs vocal/life coaching
VOACAL_KEYWORDS = [
    "need vocal coach", "looking for singing lessons", "vocal training",
    "can't sing properly", "voice coach", "singing teacher",
    "help with my voice", "vocal lessons", "learn to sing",
    "voice training", "singing coach", "online vocal coach",
    "vocal coach needed", "voice lessons", "how to sing better",
    "vocal technique", "singing technique", "vocal range",
    "can't hit high notes", "breath control singing",
    "vocal cords hurt", "strain when singing", "pitch problems",
]

LIFE_COACHING_KEYWORDS = [
    "life coach", "need direction", "feeling stuck", "need guidance",
    "life advice", "feeling lost", "need purpose", "confidence issues",
    "self improvement", "mentorship needed", "need motivation",
    "young professional guidance", "career direction",
    "feeling confused about life", "need someone to talk to",
]

# Platforms to search
PLATFORMS = {
    "twitter": True,
    "reddit": True,
    "youtube": True,
}


def run_lead_generation(airtable, bot) -> None:
    """Main entry point — called by cron job daily."""
    logger.info("🔍 Starting autonomous lead generation run")

    all_leads = []

    # 1. Search Twitter/X
    try:
        twitter_leads = search_twitter()
        all_leads.extend(twitter_leads)
        logger.info(f"Twitter: {len(twitter_leads)} leads found")
    except Exception as e:
        logger.error(f"Twitter search failed: {e}")

    # 2. Search Reddit
    try:
        reddit_leads = search_reddit()
        all_leads.extend(reddit_leads)
        logger.info(f"Reddit: {len(reddit_leads)} leads found")
    except Exception as e:
        logger.error(f"Reddit search failed: {e}")

    # 3. Search YouTube comments
    try:
        youtube_leads = search_youtube_comments()
        all_leads.extend(youtube_leads)
        logger.info(f"YouTube: {len(youtube_leads)} leads found")
    except Exception as e:
        logger.error(f"YouTube search failed: {e}")

    # 4. Deduplicate and save to Airtable
    if all_leads:
        saved = save_leads_to_airtable(airtable, all_leads)
        logger.info(f"Saved {saved} new leads to Airtable")
    else:
        saved = 0
        logger.info("No new leads found this run")

    # 5. Send daily summary to admin via Telegram
    try:
        send_daily_summary(bot, all_leads, saved)
    except Exception as e:
        logger.error(f"Failed to send summary: {e}")


def search_twitter() -> list:
    """Search Twitter/X for people looking for coaching."""
    leads = []
    
    # Use Twitter search API (free tier)
    # Search for recent tweets containing our keywords
    for keyword in VOACAL_KEYWORDS[:5]:  # Limit to avoid rate limits
        try:
            url = "https://api.twitter.com/2/tweets/search/recent"
            headers = {"Authorization": f"Bearer {get_twitter_bearer_token()}"}
            params = {
                "query": f"{keyword} -is:retweet lang:en",
                "max_results": 10,
                "tweet.fields": "author_id,created_at,geo,public_metrics",
                "expansions": "author_id",
                "user.fields": "username,location,description"
            }
            
            r = requests.get(url, headers=headers, params=params, timeout=10)
            if r.status_code != 200:
                continue
            
            data = r.json()
            tweets = data.get("data", [])
            users = {u["id"]: u for u in data.get("includes", {}).get("users", [])}
            
            for tweet in tweets:
                author = users.get(tweet.get("author_id", ""), {})
                text = tweet.get("text", "")
                
                # Quality filter: genuine need, not promotional
                if is_genuine_lead(text):
                    leads.append({
                        "platform": "Twitter",
                        "name": author.get("name", "Unknown"),
                        "username": author.get("username", ""),
                        "location": author.get("location", ""),
                        "content": text[:300],
                        "url": f"https://twitter.com/{author.get('username', '')}/status/{tweet.get('id', '')}",
                        "keyword_matched": keyword,
                        "quality_score": score_lead(text),
                        "type": "vocal" if any(k in text.lower() for k in VOACAL_KEYWORDS) else "life",
                        "date_found": datetime.utcnow().isoformat(),
                    })
        except Exception as e:
            logger.debug(f"Twitter search error for '{keyword}': {e}")
            continue
    
    return leads


def search_reddit() -> list:
    """Search Reddit for people asking for vocal/life coaching help."""
    leads = []
    
    subreddits = ["singing", "vocaltraining", "WeAreTheMusicMakers", "musicians", "SingingLessons"]
    
    for subreddit in subreddits:
        try:
            # Use Reddit JSON API (no auth needed for read)
            url = f"https://www.reddit.com/r/{subreddit}/search.json"
            headers = {"User-Agent": "SessionsWithToby-LeadGen/1.0"}
            params = {
                "q": " OR ".join(VOACAL_KEYWORDS[:3]),
                "sort": "new",
                "t": "week",
                "limit": 10,
                "restrict_sr": "on"
            }
            
            r = requests.get(url, headers=headers, params=params, timeout=10)
            if r.status_code != 200:
                continue
            
            data = r.json()
            posts = data.get("data", {}).get("children", [])
            
            for post in posts:
                post_data = post.get("data", {})
                text = f"{post_data.get('title', '')} {post_data.get('selftext', '')}"
                
                if is_genuine_lead(text):
                    leads.append({
                        "platform": "Reddit",
                        "name": post_data.get("author", "Unknown"),
                        "username": post_data.get("author", ""),
                        "location": "",
                        "content": text[:300],
                        "url": f"https://reddit.com{post_data.get('permalink', '')}",
                        "keyword_matched": "reddit_search",
                        "quality_score": score_lead(text),
                        "type": "vocal" if any(k in text.lower() for k in VOACAL_KEYWORDS) else "life",
                        "date_found": datetime.utcnow().isoformat(),
                    })
        except Exception as e:
            logger.debug(f"Reddit search error for r/{subreddit}: {e}")
            continue
    
    return leads


def search_youtube_comments() -> list:
    """Search YouTube comments under popular vocal coaching videos."""
    leads = []
    
    # Popular YouTube video IDs for vocal coaching content
    VIDEO_IDS = [
        "dQw4w9WgXcQ",  # Replace with actual vocal coaching video IDs
    ]
    
    # Note: YouTube Data API v3 required for this
    # For now, return empty — can be extended with API key
    return leads


def is_genuine_lead(text: str) -> bool:
    """Filter out spam, promotional content, and irrelevant posts."""
    text_lower = text.lower()
    
    # Exclude if it's clearly promotional
    spam_signals = [
        "buy now", "click link", "dm me for", "cheap", "free download",
        "check my", "subscribe to my", "follow me", "promo", "advertisement",
        "#ad", "sponsored", "affiliate"
    ]
    if any(signal in text_lower for signal in spam_signals):
        return False
    
    # Exclude if too short (likely not a genuine request)
    if len(text) < 30:
        return False
    
    # Exclude if it's a question being asked by a coach (not a potential student)
    coach_signals = [
        "i'm a coach", "i teach", "my students", "my course",
        "i offer", "i provide", "my services"
    ]
    if any(signal in text_lower for signal in coach_signals):
        return False
    
    return True


def score_lead(text: str) -> int:
    """Score lead quality from 1-10 based on urgency and genuine need."""
    score = 5  # Base score
    text_lower = text.lower()
    
    # High urgency signals
    urgency = [
        "urgently", "desperately", "really need", "serious about",
        "willing to pay", "ready to start", "asap", "immediately",
        "frustrated", "struggling", "help me please"
    ]
    for signal in urgency:
        if signal in text_lower:
            score += 2
    
    # Specific need signals
    specific = [
        "vocal range", "pitch", "breath control", "high notes",
        "voice crack", "vocal strain", "confidence", "direction",
        "purpose", "career advice", "young professional"
    ]
    for signal in specific:
        if signal in text_lower:
            score += 1
    
    # Cap at 10
    return min(score, 10)


def get_twitter_bearer_token() -> str:
    """Get Twitter API bearer token from env."""
    return os.getenv("TWITTER_BEARER_TOKEN", "")


def save_leads_to_airtable(airtable, leads: list) -> int:
    """Save qualified leads to Airtable, avoiding duplicates."""
    saved = 0
    
    for lead in leads:
        try:
            # Check for duplicate (same username + platform)
            existing = airtable.find_lead_by_username(
                lead["username"], lead["platform"]
            )
            if existing:
                continue
            
            # Create record
            fields = {
                "Name": lead["name"],
                "Platform": lead["platform"],
                "Username": lead["username"],
                "Location": lead["location"],
                "Content": lead["content"],
                "URL": lead["url"],
                "Type": lead["type"],
                "Quality Score": lead["quality_score"],
                "Status": "new",
                "Date Found": lead["date_found"],
                "Keyword Matched": lead["keyword_matched"],
            }
            
            airtable.create_student(fields)
            saved += 1
        except Exception as e:
            logger.error(f"Failed to save lead: {e}")
    
    return saved


def send_daily_summary(bot, leads: list, saved: int) -> None:
    """Send daily lead summary to admin via Telegram."""
    if not leads:
        message = "🔍 Daily Lead Report: No new leads found today."
    else:
        vocal_leads = [l for l in leads if l["type"] == "vocal"]
        life_leads = [l for l in leads if l["type"] == "life"]
        
        message = (
            f"🔍 **Daily Lead Report** — {datetime.utcnow().strftime('%Y-%m-%d')}\n\n"
            f"Found: {len(leads)} total leads\n"
            f"Saved: {saved} new (deduplicated)\n"
            f"🎤 Vocal: {len(vocal_leads)} | 🧠 Life: {len(life_leads)}\n\n"
        )
        
        # Show top 5 leads by quality score
        top_leads = sorted(leads, key=lambda x: x["quality_score"], reverse=True)[:5]
        for i, lead in enumerate(top_leads, 1):
            message += (
                f"{i}. **{lead['name']}** ({lead['platform']}) "
                f"Score: {lead['quality_score']}/10\n"
                f"   {lead['content'][:100]}...\n"
                f"   {lead['url']}\n\n"
            )
    
    try:
        requests.post(
            f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage",
            json={
                "chat_id": int(ADMIN_TG_ID),
                "text": message,
                "parse_mode": "Markdown",
                "disable_web_page_preview": True
            },
            timeout=10
        )
    except Exception as e:
        logger.error(f"Failed to send Telegram summary: {e}")
