#!/usr/bin/env python3
"""
merge_feeds.py

Pulls every RSS feed listed in FEEDS, merges the items by publish date
(newest first), and writes ONE combined feed you can check at a glance.

Outputs two files:
  - combined.xml   a real RSS 2.0 feed (import this into any reader,
                    or point a website widget at it)
  - combined.html  a plain, single-page digest (open it directly in a browser)

Run it manually, or on a schedule (see the "keeping it fresh" notes at
the bottom of this file) so combined.xml / combined.html stay current.

Requires: feedparser  (pip install feedparser)
"""

import feedparser
import html
from datetime import datetime, timezone
from email.utils import format_datetime

FEEDS = {
    "News / World": {
        "BBC News \u2014 World": "https://feeds.bbci.co.uk/news/world/rss.xml",
        "NPR News": "https://feeds.npr.org/1001/rss.xml",
        "The Guardian \u2014 World": "https://www.theguardian.com/world/rss",
        "Al Jazeera": "https://www.aljazeera.com/xml/rss/all.xml",
        "NYT \u2014 World": "https://rss.nytimes.com/services/xml/rss/nyt/World.xml",
    },
    "Politics": {
        "Politico": "https://www.politico.com/rss/politicopicks.xml",
        "The Hill": "https://thehill.com/feed/",
        "NYT \u2014 Politics": "https://rss.nytimes.com/services/xml/rss/nyt/Politics.xml",
        # "Washington Post — Politics": "https://feeds.washingtonpost.com/rss/politics",  # verify before enabling
    },
    "Books & Literature": {
        "Literary Hub": "https://lithub.com/feed/",
        "The Paris Review": "https://www.theparisreview.org/blog/feed/",
        "Book Riot": "https://bookriot.com/feed/",
        "The Guardian \u2014 Books": "https://www.theguardian.com/books/rss",
    },
    "History": {
        "History Today": "https://www.historytoday.com/feed/blog.xml",
        "HistoryExtra": "https://www.historyextra.com/feed/atom",
        "Chicago History Museum Blog": "https://www.chicagohistory.org/feed",
        # "Smithsonian — History": "https://www.smithsonianmag.com/rss/history/",  # verify before enabling
    },
    "Philosophy": {
        "Aeon": "https://aeon.co/feed.rss",
        "Philosophy Now": "https://philosophynow.org/rss",
        "Daily Nous": "https://dailynous.com/feed/",
        # "3 Quarks Daily": "https://3quarksdaily.com/feed",  # verify before enabling
    },
    "Chicago": {
        "Chicago Tribune": "https://www.chicagotribune.com/feed/",
        "Block Club Chicago": "https://blockclubchicago.org/feed/",
        "Chicago Reader": "https://chicagoreader.com/feed/",
        # "Chicago Sun-Times": "https://chicago.suntimes.com/rss/index.xml",  # verify before enabling
    },
}

MAX_ITEMS_PER_FEED = 8   # keep the digest readable, not a firehose
MAX_TOTAL_ITEMS = 100

def fetch_all():
    items = []
    for category, sources in FEEDS.items():
        for name, url in sources.items():
            parsed = feedparser.parse(url)
            if parsed.bozo and not parsed.entries:
                print(f"  [skip] {name}: could not parse ({parsed.bozo_exception})")
                continue
            for entry in parsed.entries[:MAX_ITEMS_PER_FEED]:
                published = entry.get("published_parsed") or entry.get("updated_parsed")
                dt = datetime(*published[:6], tzinfo=timezone.utc) if published else datetime.now(timezone.utc)
                items.append({
                    "category": category,
                    "source": name,
                    "title": entry.get("title", "(untitled)"),
                    "link": entry.get("link", url),
                    "summary": entry.get("summary", ""),
                    "date": dt,
                })
            print(f"  [ok]   {name}: {len(parsed.entries)} items")
    items.sort(key=lambda x: x["date"], reverse=True)
    return items[:MAX_TOTAL_ITEMS]

def write_html(items, path="combined.html"):
    rows = []
    for it in items:
        rows.append(f"""
        <div class="item">
          <span class="cat">{html.escape(it['category'])}</span>
          <span class="src">{html.escape(it['source'])}</span>
          <span class="date">{it['date'].strftime('%b %d, %H:%M UTC')}</span>
          <h3><a href="{html.escape(it['link'])}" target="_blank" rel="noopener">{html.escape(it['title'])}</a></h3>
        </div>""")
    page = f"""<!DOCTYPE html><html><head><meta charset="utf-8">
<title>Combined digest</title>
<style>
body{{font-family:system-ui,sans-serif;max-width:760px;margin:40px auto;padding:0 16px;color:#222}}
.item{{border-bottom:1px solid #ddd;padding:14px 0}}
.cat{{font-size:11px;text-transform:uppercase;letter-spacing:.05em;color:#a33;font-weight:600;margin-right:8px}}
.src{{font-size:12px;color:#666}}
.date{{float:right;font-size:11px;color:#999}}
h3{{margin:6px 0 0;font-size:16px}}
a{{color:#222;text-decoration:none}}
a:hover{{text-decoration:underline}}
</style></head><body>
<h1>Combined digest \u2014 generated {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M UTC')}</h1>
{''.join(rows)}
</body></html>"""
    with open(path, "w", encoding="utf-8") as f:
        f.write(page)

def write_rss(items, path="combined.xml"):
    entries = []
    for it in items:
        entries.append(f"""
    <item>
      <title>{html.escape(f"[{it['category']}] {it['title']}")}</title>
      <link>{html.escape(it['link'])}</link>
      <description>{html.escape(f"{it['source']}: {it['summary'][:300]}")}</description>
      <pubDate>{format_datetime(it['date'])}</pubDate>
      <guid isPermaLink="true">{html.escape(it['link'])}</guid>
    </item>""")
    feed = f"""<?xml version="1.0" encoding="UTF-8"?>
<rss version="2.0"><channel>
  <title>A Character Quiz \u2014 Combined Digest</title>
  <link>https://www.acharacterquiz.com</link>
  <description>News, politics, books, history, philosophy, and Chicago \u2014 merged into one feed</description>
  <lastBuildDate>{format_datetime(datetime.now(timezone.utc))}</lastBuildDate>
  {''.join(entries)}
</channel></rss>"""
    with open(path, "w", encoding="utf-8") as f:
        f.write(feed)

if __name__ == "__main__":
    print("Fetching feeds...")
    all_items = fetch_all()
    write_html(all_items)
    write_rss(all_items)
    print(f"\nWrote {len(all_items)} items to combined.html and combined.xml")

# --- Keeping it fresh ---------------------------------------------------
# This script is a snapshot: run it, get one merged view, done. To make
# it check itself automatically, see the "best way to do this" notes
# in the accompanying write-up.
