#!/usr/bin/env python3
"""
Web search and extraction tools.
Uses free methods (Bing scraping, DuckDuckGo) — no API keys needed.
"""
import requests
from bs4 import BeautifulSoup
import html2text
import re


def search_web(query: str, limit: int = 5) -> list:
    """
    Search the web using Bing scraping (free, no API key).
    Returns list of {title, url, snippet}.
    """
    try:
        r = requests.get(
            'https://www.bing.com/search',
            params={'q': query, 'count': limit},
            headers={
                'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
                'Accept': 'text/html,application/xhtml+xml',
                'Accept-Language': 'en-US,en;q=0.9',
            },
            timeout=15,
        )
        soup = BeautifulSoup(r.text, 'html.parser')
        results = []
        for item in soup.find_all('li', class_='b_algo', limit=limit):
            a = item.find('a')
            if not a:
                continue
            title = a.get_text(strip=True)
            url = a.get('href', '')
            # Get snippet
            snippet_div = item.find('p') or item.find(class_='b_caption')
            snippet = snippet_div.get_text(strip=True) if snippet_div else ''
            if title and url:
                results.append({'title': title, 'url': url, 'snippet': snippet})
        return results
    except Exception as e:
        return [{'error': str(e)}]


def extract_page(url: str, max_chars: int = 5000) -> str:
    """
    Extract clean text content from a URL.
    Uses html2text for clean markdown output.
    """
    try:
        r = requests.get(
            url,
            headers={'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36'},
            timeout=15,
        )
        # Convert HTML to clean markdown
        h = html2text.HTML2Text()
        h.ignore_links = False
        h.ignore_images = True
        h.ignore_emphasis = False
        h.body_width = 0  # Don't wrap
        text = h.handle(r.text)
        # Clean up
        text = re.sub(r'\n{3,}', '\n\n', text)
        return text[:max_chars]
    except Exception as e:
        return 'Error: ' + str(e)


def search_and_extract(query: str, limit: int = 3) -> str:
    """Search and extract content from top results."""
    results = search_web(query, limit)
    if not results:
        return 'No results found.'
    if 'error' in results[0]:
        return 'Search error: ' + results[0]['error']

    output = []
    for i, r in enumerate(results, 1):
        output.append(f'### {i}. {r["title"]}')
        output.append(f'URL: {r["url"]}')
        if r.get('snippet'):
            output.append(f'Snippet: {r["snippet"]}')
        # Extract page content
        content = extract_page(r['url'], max_chars=2000)
        output.append(f'\n{content}\n')
        output.append('---')

    return '\n'.join(output)


if __name__ == '__main__':
    import sys
    if len(sys.argv) > 1:
        query = ' '.join(sys.argv[1:])
        print(f'Searching for: {query}\n')
        results = search_web(query, 5)
        for i, r in enumerate(results, 1):
            if 'error' in r:
                print('Error:', r['error'])
            else:
                print(f'{i}. {r["title"]}')
                print(f'   {r["url"]}')
                if r.get('snippet'):
                    print(f'   {r["snippet"][:100]}')
                print()
