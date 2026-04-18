#!/usr/bin/env python3
"""
AI PULSE - Daily News Updater
Fetches top AI news from RSS feeds, updates index.html,
and commits changes automatically.
"""

import urllib.request
import xml.etree.ElementTree as ET
import re
import html
import json
import os
from datetime import datetime, timezone


# ── RSS FEEDS TO CHECK ──
FEEDS = [
    "https://techcrunch.com/category/artificial-intelligence/feed/",
    "https://feeds.feedburner.com/venturebeat/SZYF",
    "https://www.technologyreview.com/feed/",
    "https://spectrum.ieee.org/feeds/topic/artificial-intelligence.rss",
    "https://www.theverge.com/rss/ai-artificial-intelligence/index.xml",
]

EMOJIS_POOL = [
    "🤖🧠🔥", "📊🌍⚡", "🚀🤖💡", "🧬🤖🔬",
    "💻🤖📈", "🌐🧠🔮", "⚡🤖🌟", "🔬🧠💫",
]


def fetch_feed(url, timeout=10):
    """Fetch and parse an RSS feed, return list of entries."""
    entries = []
    try:
        req = urllib.request.Request(url, headers={"User-Agent": "AI-PULSE-Bot/1.0"})
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            data = resp.read()
        root = ET.fromstring(data)

        # Handle RSS 2.0
        for item in root.findall(".//item"):
            title = item.findtext("title", "").strip()
            link = item.findtext("link", "").strip()
            desc = item.findtext("description", "").strip()
            pub = item.findtext("pubDate", "").strip()
            if title and link:
                # Clean HTML from description
                desc = re.sub(r"<[^>]+>", "", desc)
                desc = html.unescape(desc)
                if len(desc) > 300:
                    desc = desc[:297] + "..."
                entries.append({
                    "title": html.unescape(title),
                    "link": link,
                    "description": desc,
                    "pubDate": pub,
                    "source": url,
                })

        # Handle Atom
        ns = {"atom": "http://www.w3.org/2005/Atom"}
        for entry in root.findall(".//atom:entry", ns):
            title = entry.findtext("atom:title", "", ns).strip()
            link_el = entry.find("atom:link[@rel='alternate']", ns)
            if link_el is None:
                link_el = entry.find("atom:link", ns)
            link = link_el.get("href", "") if link_el is not None else ""
            summary = entry.findtext("atom:summary", "", ns).strip()
            summary = re.sub(r"<[^>]+>", "", summary)
            summary = html.unescape(summary)
            if len(summary) > 300:
                summary = summary[:297] + "..."
            pub = entry.findtext("atom:published", "", ns) or entry.findtext("atom:updated", "", ns)
            if title and link:
                entries.append({
                    "title": html.unescape(title),
                    "link": link,
                    "description": summary,
                    "pubDate": pub or "",
                    "source": url,
                })
    except Exception as e:
        print(f"  [WARN] Could not fetch {url}: {e}")
    return entries


def is_ai_related(title, desc):
    """Check if article is AI-related."""
    text = (title + " " + desc).lower()
    keywords = [
        "artificial intelligence", "ai ", " ai,", " ai.", "machine learning",
        "deep learning", "neural network", "llm", "gpt", "chatgpt", "gemini",
        "claude", "openai", "anthropic", "generative ai", "gen ai",
        "inteligencia artificial", "aprendizaje automatico",
        "large language model", "transformer", "diffusion model",
    ]
    return any(kw in text for kw in keywords)


def get_source_name(url):
    """Extract readable source name from URL."""
    if "techcrunch" in url:
        return "TechCrunch"
    if "venturebeat" in url:
        return "VentureBeat"
    if "technologyreview" in url:
        return "MIT Tech Review"
    if "spectrum.ieee" in url:
        return "IEEE Spectrum"
    if "theverge" in url:
        return "The Verge"
    domain = re.search(r"https?://(?:www\.)?([^/]+)", url)
    return domain.group(1) if domain else "Web"


def build_news_card(article, emoji, is_featured=False):
    """Generate HTML card for a news article."""
    source = get_source_name(article.get("source", article["link"]))
    title = html.escape(article["title"])
    desc = html.escape(article["description"])
    link = html.escape(article["link"])

    if is_featured:
        return f"""      <div class="card card-featured reveal">
        <div class="card-emoji-banner">{emoji}</div>
        <div style="display:flex; flex-direction:column; flex:1;">
          <div class="card-body">
            <p class="card-type">
              <span data-lang-inline="es">📰 Noticia del dia · {source}</span>
              <span data-lang-inline="en">📰 News of the day · {source}</span>
            </p>
            <h3>
              <span data-lang-inline="es">{title}</span>
              <span data-lang-inline="en">{title}</span>
            </h3>
            <p>
              <span data-lang-inline="es">{desc}</span>
              <span data-lang-inline="en">{desc}</span>
            </p>
          </div>
          <div class="card-footer">
            <a class="card-link" href="{link}" target="_blank" rel="noopener">
              <span data-lang-inline="es">Leer mas</span>
              <span data-lang-inline="en">Read more</span>
            </a>
            <span class="card-platform">{source}</span>
          </div>
        </div>
      </div>"""
    else:
        return f"""      <div class="card reveal">
        <div class="card-emoji-banner">{emoji}</div>
        <div class="card-body">
          <p class="card-type">
            <span data-lang-inline="es">📰 Noticia · {source}</span>
            <span data-lang-inline="en">📰 News · {source}</span>
          </p>
          <h3>
            <span data-lang-inline="es">{title}</span>
            <span data-lang-inline="en">{title}</span>
          </h3>
          <p>
            <span data-lang-inline="es">{desc}</span>
            <span data-lang-inline="en">{desc}</span>
          </p>
        </div>
        <div class="card-footer">
          <a class="card-link" href="{link}" target="_blank" rel="noopener">
            <span data-lang-inline="es">Leer mas</span>
            <span data-lang-inline="en">Read more</span>
          </a>
          <span class="card-platform">{source}</span>
        </div>
      </div>"""


def update_index_html(top_article, secondary_articles):
    """Replace the 'Noticia del Dia' section in index.html."""
    index_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "index.html")

    with open(index_path, "r", encoding="utf-8") as f:
        content = f.read()

    # Build the featured card
    featured_card = build_news_card(top_article, EMOJIS_POOL[0], is_featured=True)

    # Build secondary cards
    secondary_html = ""
    for i, art in enumerate(secondary_articles[:2]):
        emoji = EMOJIS_POOL[(i + 1) % len(EMOJIS_POOL)]
        secondary_html += "\n\n" + build_news_card(art, emoji)

    # Build complete section
    today = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    new_section = f"""  <!-- =============================== -->
  <!-- NOTICIA DEL DIA                -->
  <!-- Actualizado: {today}       -->
  <!-- =============================== -->
  <section>
    <div class="section-header reveal">
      <span class="section-emoji">📰</span>
      <h2 class="section-title">
        <span data-lang-inline="es">Noticia del Dia</span>
        <span data-lang-inline="en">News of the Day</span>
      </h2>
      <span class="section-badge hot">
        <span data-lang-inline="es">🔥 HOY</span>
        <span data-lang-inline="en">🔥 TODAY</span>
      </span>
    </div>

    <div class="cards-grid">
{featured_card}
{secondary_html}
    </div>
  </section>"""

    # Replace existing section using markers
    pattern = r"  <!-- =+\s*-->\s*\n\s*<!-- NOTICIA DEL D[IÍ]A.*?</section>"
    match = re.search(pattern, content, re.DOTALL | re.IGNORECASE)

    if match:
        content = content[:match.start()] + new_section + content[match.end():]
        print(f"[OK] Noticia del Dia section updated")
    else:
        # Insert after breaking banner
        marker = "</div>\n\n  <!-- "
        idx = content.find("<!-- SECCION 1") or content.find("<!-- SECCIÓN 1")
        if idx == -1:
            idx = content.find("<!-- =")
            if idx == -1:
                print("[ERROR] Could not find insertion point")
                return False

        # Find the line before section 1
        insert_before = content.rfind("\n", 0, idx)
        content = content[:insert_before] + "\n\n" + new_section + "\n\n" + content[insert_before:]
        print(f"[OK] Noticia del Dia section inserted")

    # Update ticker with top news
    top_title = html.escape(top_article["title"])
    ticker_es_pattern = r'(<div class="ticker-inner" data-lang="es">)(.*?)(</div>)'
    ticker_en_pattern = r'(<div class="ticker-inner" data-lang="en">)(.*?)(</div>)'

    def update_ticker(match, new_item):
        opening, inner, closing = match.group(1), match.group(2), match.group(3)
        spans = re.findall(r"<span>.*?</span>", inner)
        if len(spans) >= 5:
            spans[-1] = f"<span>📰 {new_item}</span>"
        else:
            spans.append(f"<span>📰 {new_item}</span>")
        return opening + "\n    " + "\n    ".join(spans) + "\n  " + closing

    content = re.sub(ticker_es_pattern, lambda m: update_ticker(m, top_title), content, flags=re.DOTALL)
    content = re.sub(ticker_en_pattern, lambda m: update_ticker(m, top_title), content, flags=re.DOTALL)

    with open(index_path, "w", encoding="utf-8") as f:
        f.write(content)

    return True


def main():
    print("=" * 50)
    print("AI PULSE - Daily News Updater")
    print(f"Date: {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M UTC')}")
    print("=" * 50)

    # Fetch all feeds
    all_articles = []
    for feed_url in FEEDS:
        print(f"\nFetching: {feed_url}")
        entries = fetch_feed(feed_url)
        print(f"  Found {len(entries)} entries")
        for entry in entries:
            entry["source"] = feed_url
        all_articles.extend(entries)

    # Filter AI-related
    ai_articles = [a for a in all_articles if is_ai_related(a["title"], a["description"])]
    print(f"\nTotal articles: {len(all_articles)}")
    print(f"AI-related: {len(ai_articles)}")

    if not ai_articles:
        print("[WARN] No AI articles found, using all articles")
        ai_articles = all_articles[:5]

    if not ai_articles:
        print("[ERROR] No articles found at all. Exiting.")
        return

    # Pick top article (first one, feeds are usually newest-first)
    top = ai_articles[0]
    secondary = ai_articles[1:3]

    print(f"\nTop article: {top['title']}")
    for i, s in enumerate(secondary):
        print(f"Secondary {i+1}: {s['title']}")

    # Update index.html
    if update_index_html(top, secondary):
        print("\n[SUCCESS] index.html updated!")
    else:
        print("\n[ERROR] Failed to update index.html")


if __name__ == "__main__":
    main()
