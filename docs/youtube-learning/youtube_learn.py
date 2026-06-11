#!/usr/bin/env python3
"""
YouTube Learning System.
Extract transcripts from YouTube videos and organize by topic.
Usage: python3 youtube_learn.py <url> [topic]
"""
import sys, os, json, re, subprocess
from pathlib import Path
from datetime import datetime

KNOWLEDGE_DIR = Path('/home/user/workspace/docs/youtube-learning/knowledge')
KNOWLEDGE_DIR.mkdir(parents=True, exist_ok=True)

INDEX_FILE = KNOWLEDGE_DIR / 'index.json'

def load_index():
    if INDEX_FILE.exists():
        with open(INDEX_FILE) as f:
            return json.load(f)
    return {'topics': {}, 'videos': []}

def save_index(index):
    with open(INDEX_FILE, 'w') as f:
        json.dump(index, f, indent=2, ensure_ascii=False)

def extract_transcript(url):
    """Extract YouTube transcript using yt-dlp."""
    try:
        result = subprocess.run(
            ['yt-dlp', '--write-auto-sub', '--sub-lang', 'en', '--skip-download',
             '--convert-subs', 'srt', '-o', '/tmp/yt_learn', url],
            capture_output=True, text=True, timeout=60
        )
        # Find the subtitle file
        import glob
        files = glob.glob('/tmp/yt_learn*.srt') + glob.glob('/tmp/yt_learn*.vtt')
        if not files:
            return None, "No subtitles found"
        
        # Read and parse the subtitle file
        with open(files[0], 'r') as f:
            content = f.read()
        
        # Parse VTT/SRT to clean text
        text = parse_subtitles(content)
        
        # Get video info
        info_result = subprocess.run(
            ['yt-dlp', '--dump-json', '--no-download', url],
            capture_output=True, text=True, timeout=30
        )
        info = json.loads(info_result.stdout) if info_result.stdout else {}
        
        # Cleanup temp files
        for f in files:
            os.remove(f)
        
        return {
            'title': info.get('title', 'Unknown'),
            'url': url,
            'duration': info.get('duration_string', 'Unknown'),
            'channel': info.get('channel', 'Unknown'),
            'transcript': text,
            'transcript_length': len(text),
            'extracted_at': datetime.utcnow().isoformat(),
        }, None
        
    except Exception as e:
        return None, str(e)

def parse_subtitles(content):
    """Parse VTT/SRT to clean text."""
    import re
    # Remove VTT header
    content = re.sub(r'WEBVTT.*?\n\n', '', content, flags=re.DOTALL)
    # Remove timestamps
    content = re.sub(r'\d{2}:\d{2}:\d{2}\.\d{3} --> \d{2}:\d{2}:\d{2}\.\d{3}.*\n', '', content)
    # Remove sequence numbers
    content = re.sub(r'^\d+\s*$', '', content, flags=re.MULTILINE)
    # Remove HTML tags
    content = re.sub(r'<[^>]+>', '', content)
    # Remove duplicate lines (common in auto-generated subs)
    lines = content.split('\n')
    seen = set()
    unique_lines = []
    for line in lines:
        line = line.strip()
        if line and line not in seen and len(line) > 3:
            unique_lines.append(line)
            seen.add(line)
    return '\n'.join(unique_lines)

def save_to_topic(video_data, topic):
    """Save video transcript to topic folder."""
    topic_dir = KNOWLEDGE_DIR / topic.lower().replace(' ', '_')
    topic_dir.mkdir(exist_ok=True)
    
    # Save transcript
    safe_title = re.sub(r'[^\w\s-]', '', video_data['title'])[:50]
    filename = f"{safe_title}_{datetime.utcnow().strftime('%Y%m%d')}.txt"
    filepath = topic_dir / filename
    
    with open(filepath, 'w') as f:
        f.write(f"# {video_data['title']}\n")
        f.write(f"URL: {video_data['url']}\n")
        f.write(f"Channel: {video_data['channel']}\n")
        f.write(f"Duration: {video_data['duration']}\n")
        f.write(f"Extracted: {video_data['extracted_at']}\n")
        f.write(f"\n---\n\n")
        f.write(video_data['transcript'])
    
    # Update index
    index = load_index()
    if topic not in index['topics']:
        index['topics'][topic] = []
    index['topics'][topic].append({
        'title': video_data['title'],
        'url': video_data['url'],
        'file': str(filepath),
        'extracted_at': video_data['extracted_at'],
    })
    index['videos'].append({
        'title': video_data['title'],
        'url': video_data['url'],
        'topic': topic,
        'file': str(filepath),
    })
    save_index(index)
    
    return filepath

def list_topics():
    """List all topics and their videos."""
    index = load_index()
    if not index['topics']:
        print("No topics yet. Add a YouTube link to get started.")
        return
    
    print("=== Knowledge Base ===")
    for topic, videos in sorted(index['topics'].items()):
        print(f"\n{topic.upper()} ({len(videos)} videos)")
        for v in videos:
            print(f"  - {v['title'][:60]}")

def search_knowledge(query):
    """Search across all transcripts."""
    index = load_index()
    results = []
    query_lower = query.lower()
    
    for video in index.get('videos', []):
        filepath = Path(video['file'])
        if filepath.exists():
            with open(filepath) as f:
                content = f.read()
            if query_lower in content.lower():
                # Find context around match
                idx = content.lower().find(query_lower)
                start = max(0, idx - 100)
                end = min(len(content), idx + 200)
                snippet = content[start:end].replace('\n', ' ')
                results.append({
                    'title': video['title'],
                    'topic': video['topic'],
                    'snippet': snippet,
                })
    
    return results

if __name__ == '__main__':
    if len(sys.argv) < 2:
        print("Usage:")
        print("  python3 youtube_learn.py <url> [topic]  — Extract and save")
        print("  python3 youtube_learn.py --list           — List all topics")
        print("  python3 youtube_learn.py --search <query> — Search knowledge")
        sys.exit(0)
    
    if sys.argv[1] == '--list':
        list_topics()
    elif sys.argv[1] == '--search' and len(sys.argv) > 2:
        query = ' '.join(sys.argv[2:])
        results = search_knowledge(query)
        print(f"Search results for '{query}':")
        for r in results:
            print(f"\n  [{r['topic']}] {r['title']}")
            print(f"  ...{r['snippet']}...")
    else:
        url = sys.argv[1]
        topic = sys.argv[2] if len(sys.argv) > 2 else 'general'
        
        print(f"Extracting transcript from: {url}")
        print(f"Topic: {topic}")
        
        video_data, error = extract_transcript(url)
        if error:
            print(f"Error: {error}")
            sys.exit(1)
        
        print(f"Title: {video_data['title']}")
        print(f"Channel: {video_data['channel']}")
        print(f"Duration: {video_data['duration']}")
        print(f"Transcript length: {video_data['transcript_length']} chars")
        
        filepath = save_to_topic(video_data, topic)
        print(f"\nSaved to: {filepath}")
        print(f"Topic: {topic}")
