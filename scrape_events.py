"""
scrape_events.py
----------------
Aggregates Tokyo gaming and pop-culture events from multiple sources:

  Direct scrapes (structured, rich data):
    - Tokyo Game Dungeon  (tokyogamedungeon.com)
    - Tokyo Game Show     (hardcoded — confirmed dates)
    - M2 ShotTriggers     (m2stg.com)

  RSS feeds (filtered to event-relevant articles, last 14 days):
    - Automaton           (automaton-media.com)
    - Game Watch          (game.watch.impress.co.jp)
    - 4Gamer              (4gamer.net)
    - Game*Spark          (gamespark.jp)
    - Google News JP      (4 targeted queries)

  一番くじ (separate section, own Google News query):
    - Filtered to gaming/anime franchises only

All non-French titles are auto-translated via Google Translate (free,
no API key — uses the deep-translator library).

Date window: today → last day of the month 4 months from now.
Events with no extractable date float to the bottom of the main list.
"""

import re
import sys
import requests
import xml.etree.ElementTree as ET
from bs4 import BeautifulSoup
from datetime import date, timedelta
from email.utils import parsedate_to_datetime

try:
    from deep_translator import GoogleTranslator
    _TRANSLATOR_OK = True
except ImportError:
    _TRANSLATOR_OK = False

# ── Constants ──────────────────────────────────────────────────────────────────

TODAY = date.today()

FR_MONTHS = {
    1: 'janvier',   2: 'février',  3: 'mars',     4: 'avril',
    5: 'mai',       6: 'juin',     7: 'juillet',   8: 'août',
    9: 'septembre', 10: 'octobre', 11: 'novembre', 12: 'décembre',
}
FR_WEEKDAYS = {
    0: 'lun.', 1: 'mar.', 2: 'mer.', 3: 'jeu.',
    4: 'ven.', 5: 'sam.', 6: 'dim.',
}

HEADERS = {'User-Agent': 'Mozilla/5.0 (compatible; PixelBentoRadar/1.0)'}

# Keywords that make an RSS article event-relevant
EVENT_KEYWORDS = [
    'イベント', '展示', '展覧会', 'ポップアップ', 'コラボ', '限定',
    '開催', 'フェス', '祭', '記念', 'ショップ', 'カフェ', 'くじ',
    '周年', 'リアル', 'グッズ', 'ストア', '展', 'フェア',
]

# 一番くじ franchises to exclude (off-niche)
KUJI_BLOCKLIST = [
    'ディズニー', 'Disney', 'スティッチ', 'Stitch', 'リロ',
    '日本代表', 'サッカー', 'GLAY', 'コアラ', '競馬', 'パチンコ',
    'プリキュア',  # borderline — remove if Thierry wants it
]


# ── Date window ────────────────────────────────────────────────────────────────

def _window_end():
    """Last day of the month that is 4 months from today."""
    m = TODAY.month + 4
    y = TODAY.year + (m - 1) // 12
    m = ((m - 1) % 12) + 1
    if m == 12:
        return date(y, 12, 31)
    return date(y, m + 1, 1) - timedelta(days=1)

WINDOW_END = _window_end()


def in_window(d):
    return d is not None and TODAY <= d <= WINDOW_END


# ── Helpers ────────────────────────────────────────────────────────────────────

def fmt_date(d):
    if d is None:
        return None
    return f"{FR_WEEKDAYS[d.weekday()]} {d.day} {FR_MONTHS[d.month]} {d.year}"


def translate(text):
    """Translate Japanese → French via Google Translate (free). Falls back to original."""
    if not _TRANSLATOR_OK or not text:
        return text
    try:
        result = GoogleTranslator(source='ja', target='fr').translate(text)
        return result if result else text
    except Exception:
        return text


def extract_date(text):
    """
    Try to extract an event date from Japanese text.
    Recognises: YYYY年MM月DD日  and  MM月DD日 (assumes current/next year).
    Returns a date object or None.
    """
    # Full date: YYYY年MM月DD日
    m = re.search(r'(\d{4})年(\d{1,2})月(\d{1,2})日', text)
    if m:
        try:
            return date(int(m.group(1)), int(m.group(2)), int(m.group(3)))
        except ValueError:
            pass
    # Short date: MM月DD日
    m = re.search(r'(\d{1,2})月(\d{1,2})日', text)
    if m:
        try:
            d = date(TODAY.year, int(m.group(1)), int(m.group(2)))
            if d < TODAY:
                d = date(TODAY.year + 1, int(m.group(1)), int(m.group(2)))
            return d
        except ValueError:
            pass
    return None


def make_event(title_ja, url, source,
               date_obj=None, location='', price='', description='',
               is_structured=False, is_kuji=False, title_fr=None):
    """Return a normalised event dict."""
    return {
        'title_ja':     title_ja,
        'title_fr':     title_fr if title_fr is not None else translate(title_ja),
        'date':         date_obj,
        'date_display': fmt_date(date_obj),
        'location':     location,
        'price':        price,
        'description':  description,
        'source':       source,
        'url':          url,
        'is_structured': is_structured,
        'is_kuji':      is_kuji,
    }


# ── Direct scrapers ────────────────────────────────────────────────────────────

def get_tgd_events():
    """Scrape the Tokyo Game Dungeon schedule page."""
    events = []
    try:
        r = requests.get('https://tokyogamedungeon.com/', headers=HEADERS, timeout=15)
        r.raise_for_status()
        soup = BeautifulSoup(r.text, 'html.parser')

        # Find the schedule section by its h2 heading
        schedule_section = None
        for h2 in soup.find_all('h2'):
            if 'スケジュール' in h2.get_text():
                schedule_section = h2.find_parent()
                break

        if not schedule_section:
            print('[TGD] Schedule section not found — page structure may have changed.')
            return events

        for div in schedule_section.find_all('div'):
            h3s = div.find_all('h3')
            h5s = div.find_all('h5')
            if not h3s or len(h5s) < 2:
                continue

            title_ja = h3s[0].get_text(strip=True)
            texts    = [h.get_text(strip=True) for h in h5s]

            # One h5 has the date (contains 年), the other is the location
            date_text = next((t for t in texts if '年' in t), '')
            loc_text  = next((t for t in texts if t != date_text), '')

            event_date = extract_date(date_text)
            if event_date is None or not in_window(event_date):
                continue

            # Standardise location string for Tokyo venues
            if '浜松町' in loc_text or '東京' in loc_text:
                location = '東京産業貿易センター浜松町館 · JR/モノレール 浜松町駅 徒歩5分'
            else:
                location = loc_text

            # Price is only published for TGD 13 at time of writing
            price = '1 000 ¥ · 2 000 ¥ pass pro · Gratuit -18 ans' \
                    if event_date == date(2026, 8, 8) else ''

            events.append(make_event(
                title_ja=title_ja,
                title_fr=translate(title_ja),
                url='https://tokyogamedungeon.com/',
                source='Tokyo Game Dungeon',
                date_obj=event_date,
                location=location,
                price=price,
                is_structured=True,
            ))

    except Exception as e:
        print(f'[TGD] Error: {e}')
    return events


def get_tgs_event():
    """
    Return Tokyo Game Show 2026 as a hardcoded structured event.
    Dates confirmed: September 17–21, 2026, Makuhari Messe, Chiba.
    Update this function each year once new dates are announced.
    """
    tgs_start = date(2026, 9, 17)
    if not in_window(tgs_start):
        return []
    return [make_event(
        title_ja='東京ゲームショウ2026',
        title_fr='Tokyo Game Show 2026 — 30e anniversaire',
        url='https://tgs.cesa.or.jp/',
        source='Tokyo Game Show',
        date_obj=tgs_start,
        location='Makuhari Messe (幕張メッセ) · Halls 1–11 · JR 海浜幕張駅 徒歩5分',
        price='Tarifs grand public à confirmer · Jours pro : 17–18 sept.',
        description='5 jours pour la 1re fois · grand public : 19–21 sept. · ~300 000 visiteurs attendus',
        is_structured=True,
    )]


def get_m2_events():
    """
    Scrape M2 ShotTriggers news section for events.
    M2 uses a YYYY.MM.DD date format in their news list.
    """
    events = []
    try:
        r = requests.get('https://m2stg.com/', headers=HEADERS, timeout=15)
        r.raise_for_status()
        soup = BeautifulSoup(r.text, 'html.parser')

        for el in soup.find_all(['li', 'p', 'div']):
            text = el.get_text(separator=' ', strip=True)

            # M2 news items start with YYYY.MM.DD
            dm = re.match(r'(\d{4})\.(\d{2})\.(\d{2})\s+(.*)', text)
            if not dm:
                continue

            try:
                event_date = date(int(dm.group(1)), int(dm.group(2)), int(dm.group(3)))
            except ValueError:
                continue

            title_ja = dm.group(4).strip()
            if not title_ja:
                continue

            # Only include event-related items
            if not any(kw in title_ja for kw in EVENT_KEYWORDS):
                continue

            # Only future events within window
            if not in_window(event_date):
                continue

            # Grab the link if there is one
            a = el.find('a', href=True)
            url = a['href'] if a else 'https://m2stg.com/'
            if url.startswith('/'):
                url = 'https://m2stg.com' + url

            events.append(make_event(
                title_ja=title_ja,
                url=url,
                source='M2 ShotTriggers',
                date_obj=event_date,
            ))

    except Exception as e:
        print(f'[M2] Error: {e}')
    return events


# ── RSS parser ─────────────────────────────────────────────────────────────────

def _parse_rss_item_date(item):
    """
    Try to extract a publication date from an RSS/RDF item.
    Handles pubDate (RSS 2.0) and dc:date (RSS 1.0/RDF).
    """
    # RSS 2.0
    el = item.find('pubDate')
    if el is not None and el.text:
        try:
            return parsedate_to_datetime(el.text.strip()).date()
        except Exception:
            pass
    # RSS 1.0 / Dublin Core
    el = item.find('{http://purl.org/dc/elements/1.1/}date')
    if el is not None and el.text:
        try:
            # dc:date is ISO 8601: 2026-06-04T10:00:00+09:00
            return date.fromisoformat(el.text.strip()[:10])
        except Exception:
            pass
    return None


def get_rss_events(feed_url, source_name, event_keywords_only=True, is_kuji=False):
    """
    Fetch an RSS or RDF feed and return relevant items published in the last 14 days.

    - event_keywords_only: when True, skip articles that don't mention events.
      Set to False only for very niche sources where all content is relevant.
    - is_kuji: route items into the 一番くじ section and apply the kuji blocklist.
    """
    events = []
    cutoff = TODAY - timedelta(days=14)

    try:
        r = requests.get(feed_url, headers=HEADERS, timeout=15)
        r.raise_for_status()

        root = ET.fromstring(r.content)

        # Both RSS 2.0 (<rss><channel><item>) and RDF (<rdf:RDF><item>) use <item>
        items = root.findall('.//item')

        for item in items:
            def tag(name, default=''):
                el = item.find(name)
                return el.text.strip() if el is not None and el.text else default

            title_ja = tag('title')
            # RDF items use rdf:about attribute; RSS 2.0 uses <link>
            link_el = item.find('link')
            if link_el is not None and link_el.text:
                url = link_el.text.strip()
            else:
                url = item.get('{http://www.w3.org/1999/02/22-rdf-syntax-ns#}about', '')

            if not title_ja or not url:
                continue

            # Check publication date
            pub_date = _parse_rss_item_date(item)
            if pub_date and pub_date < cutoff:
                continue  # too old

            # 一番くじ: apply niche blocklist
            if is_kuji and any(kw in title_ja for kw in KUJI_BLOCKLIST):
                continue

            # General feeds: skip non-event articles
            if event_keywords_only and not is_kuji:
                if not any(kw in title_ja for kw in EVENT_KEYWORDS):
                    continue

            # Try to extract an event date from the title text
            event_date = extract_date(title_ja)
            if event_date and not in_window(event_date):
                continue

            events.append(make_event(
                title_ja=title_ja,
                url=url,
                source=source_name,
                date_obj=event_date,
                is_kuji=is_kuji,
            ))

    except Exception as e:
        print(f'[RSS:{source_name}] Error: {e}')

    return events


def get_google_news_events(query, source_label, is_kuji=False):
    """Wrap get_rss_events for a Google News JP search query."""
    encoded = requests.utils.quote(query)
    url = f'https://news.google.com/rss/search?q={encoded}&hl=ja&gl=JP&ceid=JP:ja'
    # Google News is already query-filtered, so event_keywords_only=False for kuji,
    # True for general queries (catches edge cases in broad searches).
    return get_rss_events(url, source_label, event_keywords_only=not is_kuji, is_kuji=is_kuji)


# ── Deduplication ──────────────────────────────────────────────────────────────

def deduplicate(events):
    """Remove duplicates by URL (ignoring query params) and title prefix."""
    seen_urls   = set()
    seen_titles = set()
    out = []
    for e in events:
        url_key   = e['url'].split('?')[0].rstrip('/')
        title_key = e['title_ja'][:25].strip()
        if url_key in seen_urls or title_key in seen_titles:
            continue
        seen_urls.add(url_key)
        seen_titles.add(title_key)
        out.append(e)
    return out


# ── Main aggregator ────────────────────────────────────────────────────────────

def get_all_events():
    """
    Fetch from all sources and return two sorted lists:
      main_events  — radar items (dated asc, then undated)
      kuji_events  — 一番くじ items (dated asc, then TBA)
    """
    print(f'Fenêtre : {fmt_date(TODAY)} → {fmt_date(WINDOW_END)}')

    all_events = []

    print('· Tokyo Game Dungeon...')
    all_events += get_tgd_events()

    print('· Tokyo Game Show (hardcoded)...')
    all_events += get_tgs_event()

    print('· M2 ShotTriggers...')
    all_events += get_m2_events()

    print('· Automaton...')
    all_events += get_rss_events('https://automaton-media.com/feed/', 'Automaton')

    print('· Game Watch...')
    all_events += get_rss_events(
        'https://game.watch.impress.co.jp/data/rss/1.0/gmw/feed.rdf', 'Game Watch')

    print('· 4Gamer...')
    all_events += get_rss_events('https://www.4gamer.net/rss/rss.shtml', '4Gamer')

    print('· Game*Spark...')
    all_events += get_rss_events('https://www.gamespark.jp/rss/index.rdf', 'Game*Spark')

    print('· Google News — expositions...')
    all_events += get_google_news_events('東京 展覧会 ゲーム アニメ 2026', 'Google News')

    print('· Google News — pop-up stores...')
    all_events += get_google_news_events('アニメ ゲーム ポップアップ 東京 2026', 'Google News')

    print('· Google News — collabs...')
    all_events += get_google_news_events('ゲーム アニメ コラボ 限定 2026', 'Google News')

    print('· Google News — événements 同人...')
    all_events += get_google_news_events('同人 イベント 東京 2026', 'Google News')

    print('· Google News — 一番くじ...')
    kuji_raw = get_google_news_events('一番くじ 2026', 'Google News', is_kuji=True)

    # Deduplicate separately (kuji items were already flagged is_kuji=True)
    all_events  = deduplicate(all_events)
    kuji_events = deduplicate(kuji_raw)

    # Sort: dated events ascending, undated float to bottom
    dated   = sorted([e for e in all_events if e['date']], key=lambda e: e['date'])
    undated = [e for e in all_events if not e['date']]

    kuji_dated   = sorted([e for e in kuji_events if e['date']], key=lambda e: e['date'])
    kuji_undated = [e for e in kuji_events if not e['date']]

    main = dated + undated
    kuji = kuji_dated + kuji_undated

    print(f'\n✓ {len(main)} événements · {len(kuji)} tirages 一番くじ')
    return main, kuji
