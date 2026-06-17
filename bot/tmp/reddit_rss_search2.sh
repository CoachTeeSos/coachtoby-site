#!/bin/bash
# Extended Reddit lead search - Round 2 for Coach Toby
UA="Mozilla/5.0 (X11; Linux x86_64; rv:109.0) Gecko/20100101 Firefox/115.0"
OUTFILE="$HOME/.hermes/coachtoby-site/bot/tmp/reddit_posts2.jsonl"
> "$OUTFILE"

# Life coaching and self-improvement subreddits
SUBREDDITS=("selfimprovement" "getdisciplined" "decidingtobebetter" "motivation" "socialskills" "anxiety" "mentalhealth")
KEYWORDS=("life+coach" "need+help+with+my+life" "feeling+stuck" "need+guidance" "personal+growth" "confidence+help" "anxiety+help" "need+motivation")

for sub in "${SUBREDDITS[@]}"; do
  for kw in "${KEYWORDS[@]}"; do
    result=$(curl -s "https://www.reddit.com/r/${sub}/search.rss?q=${kw}&sort=new&t=week&limit=10&restrict_sr=1" \
      -H "User-Agent: $UA" \
      -H "Accept: application/rss+xml,application/xml,text/xml,*/*" 2>/dev/null)
    
    if [ -n "$result" ] && echo "$result" | grep -q "<entry>"; then
      echo "$result" | python3 -c "
import sys, re, html, json

content = sys.stdin.read()
entries = re.findall(r'<entry>(.*?)</entry>', content, re.DOTALL)
for entry in entries:
    author = re.search(r'<name>/u/(.*?)</name>', entry)
    author = author.group(1) if author else 'unknown'
    
    title = re.search(r'<title>(.*?)</title>', entry, re.DOTALL)
    title = html.unescape(title.group(1).strip()) if title else ''
    
    summary = re.search(r'<summary>(.*?)</summary>', entry, re.DOTALL)
    if not summary:
        summary = re.search(r'<content[^>]*>(.*?)</content>', entry, re.DOTALL)
    
    text = ''
    if summary:
        text = summary.group(1)
        text = re.sub(r'<[^>]+>', ' ', text)
        text = html.unescape(text).strip()
    
    link = re.search(r'<link[^>]*href=\"([^\"]+)\"', entry)
    url = link.group(1) if link else ''
    
    id_match = re.search(r'/comments/([a-z0-9]+)/', url)
    pid = id_match.group(1) if id_match else ''
    
    full = (title + '. ' + text).strip()
    if len(full) < 60:
        continue
    
    lower = full.lower()
    skip = ['promo','promotion','check out my','subscribe to my','free download',
            'crowdfund','my new single','my album','just released','gig tonight',
            'streaming now','new video','youtube channel','patreon','onlyfans',
            'check out my blog','my website','affiliate','sponsored']
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

echo "=== Round 2 complete ==="
wc -l "$OUTFILE"
