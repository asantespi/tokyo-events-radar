"""
format_email.py
---------------
Builds the HTML email for the Pixel Bento Tokyo Events Radar.

Layout:
  - Header (dark band — date window)
  - SUR LE RADAR: chronological event cards, undated items at bottom
  - 一番くじ: gaming/anime lottery prizes available at konbini
  - Footer

CSS note: email clients strip <style> blocks, so every style here
is written inline on the element itself.

Run standalone to preview:
  python3 format_email.py
Output: report.html — open in any browser.
"""

from datetime import date
from scrape_events import get_all_events, fmt_date, TODAY, WINDOW_END, FR_MONTHS


# ── Helpers ────────────────────────────────────────────────────────────────────

def esc(text):
    """Escape special HTML characters."""
    return (str(text or '')
            .replace('&', '&amp;')
            .replace('<', '&lt;')
            .replace('>', '&gt;')
            .replace('"', '&quot;'))


def fmt_window():
    return (f"{TODAY.day} {FR_MONTHS[TODAY.month]} "
            f"→ {WINDOW_END.day} {FR_MONTHS[WINDOW_END.month]} {WINDOW_END.year}")


# ── Event cards ────────────────────────────────────────────────────────────────

def structured_card(event):
    """
    Rich card for confirmed events with full detail (TGD, TGS).
    Shows a coloured source badge, date, location, price, and description.
    """
    source       = esc(event.get('source', ''))
    date_display = esc(event.get('date_display') or 'date à confirmer')
    title        = esc(event.get('title_fr') or event.get('title_ja', ''))
    location     = esc(event.get('location', ''))
    price        = esc(event.get('price', ''))
    description  = esc(event.get('description', ''))
    url          = event.get('url', '#')

    loc_row = (f'<tr><td style="padding:3px 0;">'
               f'<span style="font-family:Arial,sans-serif;font-size:13px;color:#555;">'
               f'📍 {location}</span></td></tr>') if location else ''

    price_row = (f'<tr><td style="padding:3px 0 8px;">'
                 f'<span style="font-family:Arial,sans-serif;font-size:13px;color:#555;">'
                 f'💴 {price}</span></td></tr>') if price else ''

    desc_row = (f'<tr><td style="padding:0 0 8px;">'
                f'<span style="font-family:Arial,sans-serif;font-size:13px;'
                f'color:#666;font-style:italic;">{description}</span>'
                f'</td></tr>') if description else ''

    return f"""
<tr>
  <td style="padding:0 0 24px;border-bottom:1px solid #e8e8e8;">
    <table width="100%" cellpadding="0" cellspacing="0" border="0">
      <tr><td style="padding:20px 0 6px;">
        <span style="font-family:Arial,sans-serif;font-size:10px;font-weight:bold;
                     color:#fff;background:#1a1a2e;padding:3px 8px;border-radius:3px;
                     letter-spacing:0.5px;text-transform:uppercase;">★ {source}</span>
        &nbsp;
        <span style="font-family:Arial,sans-serif;font-size:12px;color:#888;">
          📅 {date_display}
        </span>
      </td></tr>
      <tr><td style="padding:4px 0;">
        <span style="font-family:Georgia,serif;font-size:18px;
                     font-weight:bold;color:#111;line-height:1.3;">
          {title}
        </span>
      </td></tr>
      {loc_row}
      {price_row}
      {desc_row}
      <tr><td>
        <a href="{url}"
           style="font-family:Arial,sans-serif;font-size:12px;
                  color:#2a52be;text-decoration:none;">
          Voir le site →
        </a>
      </td></tr>
    </table>
  </td>
</tr>"""


def rss_card(event):
    """
    Compact card for RSS-sourced items.
    Date is shown if known; otherwise 'date à confirmer' in grey italic.
    """
    date_display = event.get('date_display')
    title        = esc(event.get('title_fr') or event.get('title_ja', ''))
    source       = esc(event.get('source', ''))
    url          = event.get('url', '#')
    no_date      = event.get('date') is None

    if no_date:
        date_html = ('<span style="font-family:Arial,sans-serif;font-size:12px;'
                     'color:#bbb;font-style:italic;">date à confirmer</span>')
    else:
        date_html = (f'<span style="font-family:Arial,sans-serif;font-size:12px;'
                     f'color:#666;">📅 {esc(date_display)}</span>')

    return f"""
<tr>
  <td style="padding:0 0 18px;border-bottom:1px solid #f0f0f0;">
    <table width="100%" cellpadding="0" cellspacing="0" border="0">
      <tr><td style="padding:14px 0 3px;">{date_html}</td></tr>
      <tr><td style="padding:0 0 4px;">
        <a href="{url}"
           style="font-family:Arial,sans-serif;font-size:14px;
                  font-weight:bold;color:#1a1a2e;text-decoration:none;
                  line-height:1.4;">
          {title}
        </a>
      </td></tr>
      <tr><td>
        <span style="font-family:Arial,sans-serif;font-size:11px;color:#bbb;">
          via {source}
        </span>
      </td></tr>
    </table>
  </td>
</tr>"""


def event_card(event):
    """Route to the right card template."""
    if event.get('is_structured'):
        return structured_card(event)
    return rss_card(event)


def kuji_card(event):
    """Compact card for 一番くじ entries."""
    date_display = event.get('date_display') or 'date à confirmer'
    title        = esc(event.get('title_fr') or event.get('title_ja', ''))
    source       = esc(event.get('source', ''))
    url          = event.get('url', '#')

    return f"""
<tr>
  <td style="padding:0 0 14px;border-bottom:1px solid #f5f5f5;">
    <table width="100%" cellpadding="0" cellspacing="0" border="0">
      <tr><td style="padding:10px 0 2px;">
        <span style="font-family:Arial,sans-serif;font-size:12px;color:#777;">
          📅 {esc(date_display)}
        </span>
      </td></tr>
      <tr><td style="padding:0 0 3px;">
        <a href="{url}"
           style="font-family:Arial,sans-serif;font-size:13px;
                  color:#1a1a2e;text-decoration:none;line-height:1.4;">
          {title}
        </a>
      </td></tr>
      <tr><td>
        <span style="font-family:Arial,sans-serif;font-size:11px;color:#bbb;">
          via {source}
        </span>
      </td></tr>
    </table>
  </td>
</tr>"""


def empty_row(message):
    return (f'<tr><td style="padding:20px 0;font-family:Arial,sans-serif;'
            f'font-size:14px;color:#bbb;font-style:italic;">{message}</td></tr>')


# ── Full document ──────────────────────────────────────────────────────────────

def build_html(main_events, kuji_events):
    """Assemble the complete HTML email."""
    window_str  = fmt_window()
    gen_str     = f"{TODAY.day} {FR_MONTHS[TODAY.month]} {TODAY.year}"

    main_rows = ''.join(event_card(e) for e in main_events) \
                if main_events else empty_row('Aucun événement trouvé cette semaine.')

    kuji_rows = ''.join(kuji_card(e) for e in kuji_events) \
                if kuji_events else empty_row('Aucun tirage trouvé cette semaine.')

    return f"""<!DOCTYPE html>
<html lang="fr">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width,initial-scale=1.0">
  <title>Pixel Bento — Radar Tokyo · {gen_str}</title>
</head>
<body style="margin:0;padding:0;background-color:#f0f0eb;font-family:Arial,sans-serif;">

  <table width="100%" cellpadding="0" cellspacing="0" border="0"
         style="background:#f0f0eb;padding:32px 16px;">
    <tr><td align="center">

      <!-- Email card — max 640px -->
      <table width="640" cellpadding="0" cellspacing="0" border="0"
             style="max-width:640px;width:100%;background:#fff;border-radius:4px;">

        <!-- ── Header ── -->
        <tr>
          <td style="background:#1a1a2e;padding:32px 44px 28px;border-radius:4px 4px 0 0;">
            <p style="margin:0 0 5px;font-size:11px;color:#7080b0;
                      letter-spacing:1.5px;text-transform:uppercase;">
              Pixel Bento
            </p>
            <h1 style="margin:0;font-family:Georgia,serif;font-size:26px;
                       color:#fff;font-weight:normal;line-height:1.2;">
              🎮 Radar Tokyo
            </h1>
            <p style="margin:8px 0 0;font-size:13px;color:#a0aacb;">
              {window_str}
            </p>
          </td>
        </tr>

        <!-- ── SUR LE RADAR ── -->
        <tr>
          <td style="padding:0 44px 16px;">
            <table width="100%" cellpadding="0" cellspacing="0" border="0">
              <tr>
                <td style="padding:28px 0 10px;">
                  <h2 style="margin:0;font-family:Georgia,serif;font-size:17px;
                             color:#1a1a2e;font-weight:normal;letter-spacing:1px;
                             text-transform:uppercase;border-bottom:2px solid #1a1a2e;
                             padding-bottom:6px;">
                    Sur le radar
                  </h2>
                </td>
              </tr>
              {main_rows}
            </table>
          </td>
        </tr>

        <!-- ── 一番くじ ── -->
        <tr>
          <td style="padding:0 44px 16px;background:#fafafa;
                     border-top:3px solid #eee;">
            <table width="100%" cellpadding="0" cellspacing="0" border="0">
              <tr>
                <td style="padding:24px 0 6px;">
                  <h2 style="margin:0;font-family:Georgia,serif;font-size:17px;
                             color:#1a1a2e;font-weight:normal;letter-spacing:1px;
                             border-bottom:2px solid #1a1a2e;padding-bottom:6px;">
                    一番くじ
                  </h2>
                  <p style="margin:4px 0 0;font-size:11px;color:#aaa;">
                    Tirages disponibles en konbini et boutiques Animate
                  </p>
                </td>
              </tr>
              {kuji_rows}
            </table>
          </td>
        </tr>

        <!-- ── Footer ── -->
        <tr>
          <td style="padding:16px 44px 28px;border-top:1px solid #eee;">
            <p style="margin:0;font-size:11px;color:#ccc;line-height:1.7;">
              Sources : Tokyo Game Dungeon · Tokyo Game Show · M2 ShotTriggers ·
              Automaton · Game Watch · 4Gamer · Game*Spark · Google News JP<br>
              Généré le {gen_str}
            </p>
          </td>
        </tr>

      </table>
      <!-- /Email card -->

    </td></tr>
  </table>

</body>
</html>"""


# ── Standalone preview ─────────────────────────────────────────────────────────

if __name__ == '__main__':
    print('Récupération des événements…')
    main_events, kuji_events = get_all_events()
    print(f'Construction de l\'email ({len(main_events)} événements, {len(kuji_events)} くじ)…')
    html = build_html(main_events, kuji_events)
    with open('report.html', 'w', encoding='utf-8') as f:
        f.write(html)
    print('Sauvegardé : report.html — ouvrir dans un navigateur pour prévisualiser.')
