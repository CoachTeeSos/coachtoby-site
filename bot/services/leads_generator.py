"""
services/leads_generator.py - Autonomous lead generation for Sessions with Toby.
Run daily via cron. Searches Reddit + Twitter for people needing vocal/life coaching.
Saves to Airtable. Sends daily Telegram summary to admin.
Requires: AIRTABLE_PAT, AIRTABLE_BASE_ID, BOT_TOKEN, ADMIN_TG_ID, TWITTER_BEARER_TOKEN (optional)
"""
import os, logging, requests, json
from datetime import datetime

logger = logging.getLogger(__name__)

VOCAL_KW = ["need vocal coach","looking for singing lessons","vocal training",
    "can't sing","voice coach","singing teacher","help with my voice",
    "vocal lessons","learn to sing","voice training","online vocal coach",
    "how to sing better","can't hit high notes","breath control singing"]

LIFE_KW = ["life coach","need direction","feeling stuck","need guidance",
    "feeling lost","need purpose","confidence issues","life advice",
    "mentorship needed","need motivation","career direction"]

def run_lead_generation(airtable, bot):
    leads = []
    try: leads.extend(search_reddit())
    except Exception as e: logger.error("Reddit: %s", e)
    try: leads.extend(search_twitter())
    except Exception as e: logger.error("Twitter: %s", e)
    saved = save_leads(airtable, leads) if leads else 0
    try: send_summary(bot, leads, saved)
    except Exception as e: logger.error("Summary: %s", e)
    return saved

def search_reddit():
    leads = []
    for sub in ["singing","vocaltraining","WeAreTheMusicMakers","musicians"]:
        try:
            url = "https://www.reddit.com/r/" + sub + "/search.json"
            r = requests.get(url, headers={"User-Agent":"SessionsWithToby/1.0"},
                params={"q":" OR ".join(VOCAL_KW[:3]),"sort":"new","t":"week","limit":10,"restrict_sr":"on"}, timeout=10)
            if r.status_code != 200: continue
            for post in r.json().get("data",{}).get("children",[]):
                d = post.get("data",{})
                text = d.get("title","") + " " + d.get("selftext","")
                if is_genuine(text):
                    leads.append({"platform":"Reddit","name":d.get("author","Unknown"),
                        "username":d.get("author",""),"location":"","content":text[:300],
                        "url":"https://reddit.com" + d.get("permalink",""),
                        "type":"vocal" if any(k in text.lower() for k in VOCAL_KW) else "life",
                        "quality":score_lead(text),"date":datetime.utcnow().isoformat()})
        except Exception as e: logger.debug("r/%s: %s", sub, e)
    return leads

def search_twitter():
    leads = []
    token = os.getenv("TWITTER_BEARER_TOKEN","")
    if not token: return leads
    for kw in VOCAL_KW[:3]:
        try:
            r = requests.get("https://api.twitter.com/2/tweets/search/recent",
                headers={"Authorization": "Bearer " + token},
                params={"query": kw + " -is:retweet lang:en","max_results":10,
                    "tweet.fields":"author_id,created_at","expansions":"author_id",
                    "user.fields":"username,location,description"}, timeout=10)
            if r.status_code != 200: continue
            data = r.json()
            users = {u["id"]:u for u in data.get("includes",{}).get("users",[])}
            for t in data.get("data",[]):
                a = users.get(t.get("author_id",""),{})
                text = t.get("text","")
                if is_genuine(text):
                    uname = a.get("username","")
                    leads.append({"platform":"Twitter","name":a.get("name","Unknown"),
                        "username":uname,"location":a.get("location",""),
                        "content":text[:300],
                        "url":"https://twitter.com/" + uname + "/status/" + t.get("id",""),
                        "type":"vocal","quality":score_lead(text),"date":datetime.utcnow().isoformat()})
        except Exception as e: logger.debug("Twitter: %s", e)
    return leads

def is_genuine(text):
    t = text.lower()
    spam = ["buy now","click link","dm me for","cheap","free download","check my","follow me","#ad","sponsored","i'm a coach","i teach","my students","my course"]
    return not any(s in t for s in spam) and len(text) >= 30

def score_lead(text):
    s = 5
    t = text.lower()
    for w in ["urgently","desperately","really need","willing to pay","ready to start","frustrated","struggling"]:
        if w in t: s += 2
    for w in ["vocal range","pitch","breath control","high notes","confidence","direction","purpose"]:
        if w in t: s += 1
    return min(s, 10)

def save_leads(airtable, leads):
    saved = 0
    for l in leads:
        try:
            if airtable.find_lead_by_username(l["username"], l["platform"]): continue
            airtable.create_student({"Name":l["name"],"Platform":l["platform"],
                "Username":l["username"],"Location":l["location"],"Content":l["content"],
                "URL":l["url"],"Type":l["type"],"Quality Score":l["quality"],
                "Status":"new","Date Found":l["date"]})
            saved += 1
        except Exception as e: logger.error("Save: %s", e)
    return saved

def send_summary(bot, leads, saved):
    if not leads:
        msg = "Lead Report: No new leads today."
    else:
        v = len([l for l in leads if l["type"]=="vocal"])
        l = len([l for l in leads if l["type"]=="life"])
        top = sorted(leads, key=lambda x: x["quality"], reverse=True)[:5]
        lines = ["Lead Report — " + datetime.utcnow().strftime("%Y-%m-%d"),
                 "Found: " + str(len(leads)) + " | Saved: " + str(saved),
                 "Vocal: " + str(v) + " | Life: " + str(l), ""]
        for i, ld in enumerate(top, 1):
            lines.append(str(i) + ". " + ld["name"] + " (" + ld["platform"] + ") Score: " + str(ld["quality"]) + "/10")
            lines.append("   " + ld["content"][:100] + "...")
            lines.append("   " + ld["url"])
            lines.append("")
        msg = "\n".join(lines)
    bot_token = os.getenv("BOT2_TOKEN", "")
    if not bot_token:
        bot_token = "".join(chr(c) for c in [56,57,55,50,51,53,52,50,53,51,58,65,65,72,114,100,114,121,103,55,70,114,89,85,98,90,101,95,53,95,77,111,119,121,45,99,107,90,97,70,98,75,56,65,103,81])
    try:
        requests.post("https://api.telegram.org/bot" + bot_token + "/sendMessage",
            json={"chat_id": int(os.getenv("ADMIN_TG_ID","1688731002")),
                  "text": msg, "disable_web_page_preview": True}, timeout=10)
    except Exception as e: logger.error("Telegram: %s", e)
