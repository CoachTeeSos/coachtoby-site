#!/bin/bash
# Reddit lead search via RSS for Coach Toby
UA="Mozilla/5.0 (X11; Linux x86_64; rv:109.0) Gecko/20100101 Firefox/115.0"
OUTFILE="$HOME/.hermes/coachtoby-site/bot/tmp/reddit_posts.jsonl"
> "$OUTFILE"

SUBREDDITS=("singing" "vocaltraining" "SingingLessons" "musicians" "WeAreTheMusicMakers")
KEYWORDS=("vocal+coach" "singing+lessons" "help+with+my+voice" "voice+coach" "voice+lessons" "learn+to+sing" "vocal+training" "need+singing+help")

for sub in "${SUBREDDITS[@]}"; do
  for kw in "${KEYWORDS[@]}"; do
    result=$(curl -s "https://www.reddit.com/r/${sub}/search.rss?q=${kw}&sort=new&t=week&limit=10&restrict_sr=1" \
      -H "User-Agent: $UA" \
      -H "Accept: application/rss+xml,application/xml,text/xml,*/*" 2>/dev/null)
    
    if [ -n "$result" ] && echo "$result" | grep -q "<entry>"; then
      # Parse RSS entries
      echo "$result" | python3 -c "
import sys, re, html, json

content = sys.stdin.read()

# Extract entries
entries = re.findall(r'<entry>(.*?)</entry>', content, re.DOTALL)
for entry in entries:
    author = re.search(r'<name>/u/(.*?)</name>', entry)
    author = author.group(1) if author else 'unknown'
    
    title = re.search(r'<title>(.*?)</title>', entry, re.DOTALL)
    title = html.unescape(title.group(1).strip()) if title else ''
    
    # Get the content
    summary = re.search(r'<summary>(.*?)</summary>', entry, re.DOTALL)
    if not summary:
        summary = re.search(r'<content[^>]*>(.*?)</content>', entry, re.DOTALL)
    
    text = ''
    if summary:
        text = summary.group(1)
        # Remove HTML tags
        text = re.sub(r'<[^>]+>', ' ', text)
        text = html.unescape(text).strip()
    
    link = re.search(r'<link[^>]*href=\"([^\"]+)\"', entry)
    url = link.group(1) if link else ''
    
    # Get link with .json for ID
    id_match = re.search(r'/comments/([a-z0-9]+)/', url)
    pid = id_match.group(1) if id_match else ''
    
    full = (title + '. ' + text).strip()
    if len(full) < 60:
        continue
    
    lower = full.lower()
    skip = ['promo','promotion','check out my','subscribe to my','free download',
            'crowdfund','my new single','my album','just released','gig tonight',
            'streaming now','new video','youtube channel','patreon','onlyfans']
    if any(w in lower for w in skip):
        continue
    
    obj = {
        'id': pid,
        'author': author,
        'subreddit': '$sub',
        'keyword': '$kw',
        'title': title[:200],
        'text': text[:500],
        'full_text': full[:600],
        'url': url,
        'source': 'Reddit'
    }
    print(json.dumps(obj))
" 2>/dev/null >> "$OUTFILE"
    fi
    
    sleep 1.5
  done
done

echo "=== Search complete ==="
wc -l "$OUTFILE"
