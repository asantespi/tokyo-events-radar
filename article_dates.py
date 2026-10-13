"""
article_dates.py
----------------
Finds the event date of a news article by reading the article itself.

Google News RSS headlines rarely contain the event date, so for items that
come out of the headline parser undated we:

  1. Resolve the Google News redirect link to the publisher's real URL
     (Google no longer serves a plain HTTP redirect — the link has to be
     decoded through the same internal endpoint news.google.com uses).
  2. Download the article and extract its text.
  3. Look for dates that sit next to event wording (開催, 会期, 開幕, 発売 ...)
     and keep the first one that falls inside the radar's date window.

Everything here is best-effort: any failure returns None, and the caller
simply leaves the event undated.
"""

import json
import re
import time
from datetime import date, timedelta
from urllib.parse import quote

import requests
from bs4 import BeautifulSoup

_HEADERS = {
    'User-Agent': ('Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 '
                   '(KHTML, like Gecko) Chrome/124.0 Safari/537.36'),
    'Accept-Language': 'ja,fr;q=0.8,en;q=0.5',
}
_TIMEOUT = 15
_MAX_BYTES = 2_000_000
_MAX_TEXT_CHARS = 6000          # event details are always near the top

# Words that mark a sentence as describing when something happens.
_EVENT_WORDS = (
    '開催', '会期', '開催期間', '期間', '開幕', '開店', '開業', 'オープン', 'OPEN',
    '日時', '日程', '開場', '開演', '発売', '販売', '展示', '開始', '実施',
    '登場', 'スタート', 'START', 'から', '〜', '～',
)

_WD = '日月火水木金土祝'

# One date token. Groups: year-or-None, month, day
_DATE_RE = re.compile(
    r'(?:(\d{4})\s*年\s*)?(\d{1,2})\s*月\s*(\d{1,2})\s*日'          # 2026年12月5日 / 12月5日
    r'|(\d{4})[./](\d{1,2})[./](\d{1,2})'                           # 2026.12.05
    r'|(?<![\d/.])(\d{1,2})/(\d{1,2})\s*[（(][' + _WD + r'][）)]'   # 12/5(土)
)

_RANGE_SEP_RE = re.compile(r'^\s*(?:[（(][^）)]{1,6}[）)])?\s*[〜～~\-–—ー]\s*')


# ── Google News link resolution ────────────────────────────────────────────────

def resolve_google_news_url(link):
    """Return the publisher URL behind a news.google.com/rss/articles/... link."""
    try:
        if '/articles/' not in link:
            return link
        gid = link.split('/articles/')[1].split('?')[0]
        r = requests.get(f'https://news.google.com/rss/articles/{gid}',
                         headers=_HEADERS, timeout=_TIMEOUT)
        node = BeautifulSoup(r.text, 'html.parser').select_one('c-wiz > div[jscontroller]')
        if not node:
            return None
        sig, ts = node.get('data-n-a-sg'), node.get('data-n-a-ts')
        if not sig or not ts:
            return None
        inner = json.dumps([
            'garturlreq',
            [['X', 'X', ['X', 'X'], None, None, 1, 1, 'US:en', None, 1, None, None,
              None, None, None, 0, 1], 'X', 'X', 1, [1, 1, 1], 1, 1, None, 0, 0, None, 0],
            gid, int(ts), sig,
        ])
        body = 'f.req=' + quote(json.dumps([[['Fbv4je', inner]]]))
        r2 = requests.post(
            'https://news.google.com/_/DotsSplashUi/data/batchexecute',
            data=body,
            headers={**_HEADERS,
                     'Content-Type': 'application/x-www-form-urlencoded;charset=UTF-8'},
            timeout=_TIMEOUT,
        )
        payload = json.loads(r2.text.split('\n\n')[1])
        url = json.loads(payload[0][2])[1]
        return url if isinstance(url, str) and url.startswith('http') else None
    except Exception as e:
        print(f'[article_dates] could not resolve Google News link: {e}')
        return None


# ── Article download ───────────────────────────────────────────────────────────

def fetch_article_text(url):
    """Return the visible text of an article (meta description first), or ''."""
    try:
        r = requests.get(url, headers=_HEADERS, timeout=_TIMEOUT, stream=True)
        if r.status_code != 200:
            return ''
        raw = b''
        for chunk in r.iter_content(65536):
            raw += chunk
            if len(raw) > _MAX_BYTES:
                break
        enc = r.encoding if r.encoding and r.encoding.lower() != 'iso-8859-1' else None
        soup = BeautifulSoup(raw, 'html.parser', from_encoding=enc)

        parts = []
        for sel in ('meta[property="og:description"]', 'meta[name="description"]'):
            tag = soup.select_one(sel)
            if tag and tag.get('content'):
                parts.append(tag['content'])

        for t in soup(['script', 'style', 'nav', 'footer', 'header', 'aside', 'form', 'noscript']):
            t.decompose()
        scope = soup.find('article') or soup.find('main') or soup.body or soup
        parts.append(scope.get_text(' ', strip=True))
        return re.sub(r'\s+', ' ', ' '.join(parts))[:_MAX_TEXT_CHARS]
    except Exception as e:
        print(f'[article_dates] could not fetch {url[:60]}: {e}')
        return ''


# ── Date extraction ────────────────────────────────────────────────────────────

def _to_date(m, base):
    """Build a date from a _DATE_RE match. `base` is the article's reference date."""
    try:
        if m.group(2):                                   # 年?月日
            y, mo, d = m.group(1), int(m.group(2)), int(m.group(3))
        elif m.group(5):                                 # 2026.12.05
            y, mo, d = m.group(4), int(m.group(5)), int(m.group(6))
        else:                                            # 12/5(土)
            y, mo, d = None, int(m.group(7)), int(m.group(8))
        if y:
            return date(int(y), mo, d)
        out = date(base.year, mo, d)
        if out < base - timedelta(days=60):              # e.g. article in Dec about "1月5日"
            out = date(base.year + 1, mo, d)
        return out
    except ValueError:
        return None


def find_event_date(text, today, window_end, pub_date=None):
    """
    Return the most plausible event start date in `text`, or None.

    Only dates in a sentence containing event wording are considered, and a
    range that has already started ("10月1日〜12月27日" read in November) is
    treated as ongoing and ignored rather than reported as its end date.
    """
    if not text:
        return None
    base = pub_date or today
    sentences = re.split(r'[。！？!?\n]|(?<=\))\s{2,}', text)

    candidates = []
    for sent in sentences:
        if not any(w in sent for w in _EVENT_WORDS):
            continue
        matches = list(_DATE_RE.finditer(sent))
        i = 0
        while i < len(matches):
            start = _to_date(matches[i], base)
            end = None
            # Range: "<date>(曜)〜<date>"
            if i + 1 < len(matches):
                between = sent[matches[i].end():matches[i + 1].start()]
                if _RANGE_SEP_RE.match(between) and len(between) <= 12:
                    end = _to_date(matches[i + 1], start or base)
                    i += 1
            i += 1
            if start is None:
                continue
            if end and start < today:
                continue                     # already running — skip
            # A bare date equal to the publication day is almost always the
            # byline timestamp, not the event.
            if pub_date and start == pub_date and not end:
                continue
            # Pages often print today's date in a header or "latest news" strip,
            # so today itself is never trusted — only dates strictly ahead.
            if today < start <= window_end:
                candidates.append(start)

    return min(candidates) if candidates else None


# ── Public API ─────────────────────────────────────────────────────────────────

def date_from_article(link, today, window_end, pub_date=None):
    """Resolve `link` (Google News or direct), read the article, find the date."""
    url = resolve_google_news_url(link) if 'news.google.com' in link else link
    if not url:
        return None
    return find_event_date(fetch_article_text(url), today, window_end, pub_date)


def enrich_undated(events, today, window_end, delay=0.4):
    """
    Fill in `date` / `date_display` for Google News events that lack one, by
    reading the article. Mutates and returns `events`.

    `fmt_date` is imported lazily from scrape_events to avoid a circular import.
    """
    from scrape_events import fmt_date

    todo = [e for e in events if not e['date'] and e['source'] == 'Google News']
    print(f'· Reading {len(todo)} undated articles for dates...')

    found = 0
    for e in todo:
        # "…が本日（9/30）発売" — a release-day report. The (M/D) is a date that
        # has already passed, and the article body would only yield some
        # unrelated later date, so leave these undated (and thus dropped).
        if '本日' in e['title_ja'] or re.search(r'[（(]\d{1,2}/\d{1,2}[）)]', e['title_ja']):
            continue
        d = date_from_article(e['url'], today, window_end, e.get('pub_date'))
        if d:
            e['date'] = d
            e['date_display'] = fmt_date(d)
            found += 1
        time.sleep(delay)
    print(f'  → {found}/{len(todo)} dated from article body')
    return events
