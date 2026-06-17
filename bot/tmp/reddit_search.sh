#!/bin/bash
# Reddit lead search script for Coach Toby
UA="User-Agent: SessionsWithToby-LeadGen/1.0"
OUTFILE="$HOME/.hermes/coachtoby-site/bot/tmp/reddit_posts.jsonl"
> "$OUTFILE"

SUBREDDITS=("singing" "vocaltraining" "SingingLessons" "musicians" "WeAreTheMusicMakers")
KEYWORDS=("need+vocal+coach" "looking+for+singing+lessons" "help+with+my+voice" "voice+coach" "vocal+training" "learn+to+sing" "voice+lessons" "can't+sing")

for sub in "${SUBREDDITS[@]}"; do
  for kw in "${KEYWORDS[@]}"; do
    result=$(curl -s "https://www.reddit.com/r/${sub}/search.json?q=${kw}&sort=new&t=week&limit=10&restrict_sr=on" -H "$UA" 2>/dev/null)
    if [ -n "$result" ]; then
      echo "$result" | python3 -c "
import sys, json
try:
    d = json.load(sys.stdin)
    posts = d.get('data',{}).get('children',[])
    for p in posts:
        pd = p.get('data',{})
        title = (pd.get('title','') or '').strip()
        text = (pd.get('selftext','') or '').strip()
        full = (title + '. ' + text).strip()
        if len(full) < 60:
            continue
        lower = full.lower()
        skip = ['promo','promotion','check out my','subscribe to my','free download','crowdfund','my new single','my album','just released']
        if any(w in lower for w in skip):
            continue
        obj = {
            'id': pd.get('id',''),
            'author': pd.get('author','unknown'),
            'subreddit': '$sub',
            'keyword': '$kw',
            'title': title[:200],
            'text': text[:400],
            'full_text': full[:500],
            'url': 'https://www.reddit.com' + (pd.get('permalink','') or ''),
            'score': pd.get('score',0),
            'num_comments': pd.get('num_comments',0),
            'created_utc': pd.get('created_utc',0)
        }
        print(json.dumps(obj))
except:
    pass
" 2>/dev/null >> "$OUTFILE"
    fi
    sleep 1
  done
done

echo "Search complete. Results in $OUTFILE"
wc -l "$OUTFILE"
