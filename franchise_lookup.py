"""
franchise_lookup.py
-------------------
Resolves official French (preferred) or English franchise names for titles
not already in franchise_names.py.

How it works
------------
1. Check franchise_names.py  — hardcoded, highest trust.
2. Check franchise_cache.json — results from previous Wikipedia lookups.
3. Call the Japanese Wikipedia API to get interlanguage links:
     ja.wikipedia.org/w/api.php?action=query&titles=<title>
                               &prop=langlinks&lllang=fr|en
   The French interlanguage title is the official French name.
   The English interlanguage title is the official English name.
4. Cache the result (hit or miss) so Wikipedia is only called once
   per unknown franchise across all future runs.

Returns (official_name_or_None, matched_ja_key_or_None).
"""

import json
import os
import requests

from franchise_names import FRANCHISE_NAMES, get_official_name

# Cache file lives next to this script in the repo
_CACHE_FILE = os.path.join(os.path.dirname(__file__), 'franchise_cache.json')
_HEADERS     = {'User-Agent': 'Mozilla/5.0 (compatible; PixelBentoRadar/1.0)'}

# Sentinel stored in cache when Wikipedia found nothing, to avoid re-querying
_MISS = '__MISS__'


# ── Cache I/O ──────────────────────────────────────────────────────────────────

def _load_cache() -> dict:
    if os.path.exists(_CACHE_FILE):
        try:
            with open(_CACHE_FILE, encoding='utf-8') as f:
                return json.load(f)
        except Exception:
            pass
    return {}


def _save_cache(cache: dict) -> None:
    try:
        with open(_CACHE_FILE, 'w', encoding='utf-8') as f:
            json.dump(cache, f, ensure_ascii=False, indent=2)
    except Exception as e:
        print(f'[franchise_cache] Could not save cache: {e}')


# ── Wikipedia lookup ───────────────────────────────────────────────────────────

def _wikipedia_lookup(title_ja: str) -> tuple[str | None, str | None]:
    """
    Query Japanese Wikipedia for `title_ja` and return (fr_title, en_title).
    Either may be None if the interlanguage link doesn't exist.
    Returns (None, None) on network error or if the page isn't found.
    """
    try:
        r = requests.get(
            'https://ja.wikipedia.org/w/api.php',
            params={
                'action':    'query',
                'titles':    title_ja,
                'prop':      'langlinks',
                'lllang':    'fr|en',
                'lllimit':   '10',
                'format':    'json',
                'redirects': '1',
            },
            headers=_HEADERS,
            timeout=10,
        )
        r.raise_for_status()
        data  = r.json()
        pages = data.get('query', {}).get('pages', {})

        for page_id, page in pages.items():
            if page_id == '-1':
                return None, None   # page not found

            langlinks = page.get('langlinks', [])
            fr = next((l['*'] for l in langlinks if l.get('lang') == 'fr'), None)
            en = next((l['*'] for l in langlinks if l.get('lang') == 'en'), None)
            return fr, en

    except Exception as e:
        print(f'[franchise_lookup] Wikipedia error for "{title_ja}": {e}')

    return None, None


# ── Public API ─────────────────────────────────────────────────────────────────

def get_official_name_with_cache(text: str) -> tuple[str | None, str | None]:
    """
    Find the official French/English name for any franchise mentioned in `text`.

    Returns (official_name, matched_ja_key) so the caller can replace exactly
    the right substring. Both values are None if no franchise is found.

    Lookup order:
      1. franchise_names.py (hardcoded)
      2. franchise_cache.json (cached Wikipedia hits)
      3. Wikipedia API (live, then cached)
    """

    # ── Step 1: hardcoded table ────────────────────────────────────────────────
    official = get_official_name(text)
    if official:
        # Find the matched key so the caller can replace the exact substring
        for ja_name in sorted(FRANCHISE_NAMES.keys(), key=len, reverse=True):
            if ja_name in text:
                return official, ja_name
        return official, None

    # ── Step 2 + 3: cache then Wikipedia ──────────────────────────────────────
    # We don't know which part of `text` is the franchise name, so we try
    # progressively shorter substrings (the full title, then without leading
    # bracket content, etc.).  In practice, article titles from RSS feeds
    # usually start with the franchise name, so we try the first "word group"
    # (up to the first bracket, colon, or 「) as the candidate.

    import re
    candidates = []

    # Candidate 1: everything before the first structural delimiter
    m = re.match(r'^([^「』【〔\[（(：:。、！？\s]{3,})', text)
    if m:
        candidates.append(m.group(1))

    # Candidate 2: full text (might be just a franchise name for kuji titles)
    if text not in candidates:
        candidates.append(text)

    cache = _load_cache()
    cache_dirty = False

    for candidate in candidates:
        # Check cache first
        if candidate in cache:
            cached_val = cache[candidate]
            if cached_val == _MISS:
                continue    # confirmed miss — skip Wikipedia
            return cached_val, candidate

        # Not in cache — call Wikipedia
        print(f'[franchise_lookup] Wikipedia lookup: "{candidate}"')
        fr, en = _wikipedia_lookup(candidate)
        official = fr or en   # prefer French

        if official:
            cache[candidate] = official
            cache_dirty = True
            if cache_dirty:
                _save_cache(cache)
            return official, candidate
        else:
            # Store miss so we don't re-query
            cache[candidate] = _MISS
            cache_dirty = True

    if cache_dirty:
        _save_cache(cache)

    return None, None
