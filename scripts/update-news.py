#!/usr/bin/env python3
"""
AI PULSE - Daily News Updater
Fetches top AI news from RSS feeds, updates index.html,
and commits changes automatically.
"""

import urllib.request
import urllib.parse
import urllib.error
import xml.etree.ElementTree as ET
import re
import html
import json
import os
import sys
import time
import logging
from datetime import datetime, timezone

# ── LOGGING SETUP ──
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
logger = logging.getLogger(__name__)

# ── CONSTANTS ──
MAX_TRANSLATION_CHARS = 500
MAX_DESCRIPTION_CHARS = 300
MAX_SECONDARY_ARTICLES = 2
HTTP_TIMEOUT = 10
TRANSLATION_DELAY = 0.5

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


def is_safe_url(url):
    """Validate that a URL uses http or https scheme only."""
    return isinstance(url, str) and url.startswith(("http://", "https://"))


def strip_html_tags(text):
    """Remove HTML tags from text safely."""
    clean = re.sub(r"<[^>]+>", "", text)
    return html.unescape(clean)


def translate_text(text, source='en', target='es'):
    """Translate text using MyMemory API (free, no key needed)."""
    if not isinstance(text, str) or len(text.strip()) < 3:
        return text if isinstance(text, str) else ""
    try:
        encoded = urllib.parse.quote(text[:MAX_TRANSLATION_CHARS])
        url = f"https://api.mymemory.translated.net/get?q={encoded}&langpair={source}|{target}"
        req = urllib.request.Request(url, headers={"User-Agent": "AI-PULSE-Bot/1.0"})
        with urllib.request.urlopen(req, timeout=HTTP_TIMEOUT) as resp:
            data = json.loads(resp.read())
        translated = data.get("responseData", {}).get("translatedText", "")
        if translated and translated.upper() != translated:
            return html.unescape(translated)
        if translated:
            # MyMemory sometimes returns ALL CAPS, try to fix
            return html.unescape(translated.capitalize())
    except (urllib.error.URLError, urllib.error.HTTPError) as e:
        logger.warning("Translation network error: %s", e)
    except (json.JSONDecodeError, KeyError) as e:
        logger.warning("Translation parse error: %s", e)
    except OSError as e:
        logger.warning("Translation failed: %s", e)
    return text


def translate_article(article):
    """Add Spanish translations to an article dict."""
    logger.info("  Translating: %s...", article['title'][:60])
    article["title_es"] = translate_text(article["title"])
    time.sleep(TRANSLATION_DELAY)
    article["description_es"] = translate_text(article["description"])
    time.sleep(TRANSLATION_DELAY)
    return article


def fetch_feed(url, timeout=HTTP_TIMEOUT):
    """Fetch and parse an RSS feed, return list of entries."""
    entries = []
    try:
        req = urllib.request.Request(url, headers={"User-Agent": "AI-PULSE-Bot/1.0"})
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            data = resp.read()

        # Harden XML parser against entity expansion attacks
        parser = ET.XMLParser()
        root = ET.fromstring(data, parser=parser)

        # Handle RSS 2.0
        for item in root.findall(".//item"):
            title = item.findtext("title", "").strip()
            link = item.findtext("link", "").strip()
            desc = item.findtext("description", "").strip()
            pub = item.findtext("pubDate", "").strip()
            if title and link and is_safe_url(link):
                desc = strip_html_tags(desc)
                if len(desc) > MAX_DESCRIPTION_CHARS:
                    desc = desc[:MAX_DESCRIPTION_CHARS - 3] + "..."
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
            if not is_safe_url(link):
                continue
            summary = entry.findtext("atom:summary", "", ns).strip()
            summary = strip_html_tags(summary)
            if len(summary) > MAX_DESCRIPTION_CHARS:
                summary = summary[:MAX_DESCRIPTION_CHARS - 3] + "..."
            pub = entry.findtext("atom:published", "", ns) or entry.findtext("atom:updated", "", ns)
            if title and link:
                entries.append({
                    "title": html.unescape(title),
                    "link": link,
                    "description": summary,
                    "pubDate": pub or "",
                    "source": url,
                })
    except (urllib.error.URLError, urllib.error.HTTPError) as e:
        logger.warning("Network error fetching %s: %s", url, e)
    except ET.ParseError as e:
        logger.warning("XML parse error for %s: %s", url, e)
    except OSError as e:
        logger.warning("Could not fetch %s: %s", url, e)
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
    """Generate HTML card for a news article (bilingual ES/EN)."""
    source = html.escape(get_source_name(article.get("source", article["link"])))
    title_en = html.escape(article["title"])
    title_es = html.escape(article.get("title_es", article["title"]))
    desc_en = html.escape(article["description"])
    desc_es = html.escape(article.get("description_es", article["description"]))
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
              <span data-lang-inline="es">{title_es}</span>
              <span data-lang-inline="en">{title_en}</span>
            </h3>
            <p>
              <span data-lang-inline="es">{desc_es}</span>
              <span data-lang-inline="en">{desc_en}</span>
            </p>
          </div>
          <div class="card-footer">
            <a class="card-link" href="{link}" target="_blank" rel="noopener noreferrer">
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
            <span data-lang-inline="es">{title_es}</span>
            <span data-lang-inline="en">{title_en}</span>
          </h3>
          <p>
            <span data-lang-inline="es">{desc_es}</span>
            <span data-lang-inline="en">{desc_en}</span>
          </p>
        </div>
        <div class="card-footer">
          <a class="card-link" href="{link}" target="_blank" rel="noopener noreferrer">
            <span data-lang-inline="es">Leer mas</span>
            <span data-lang-inline="en">Read more</span>
          </a>
          <span class="card-platform">{source}</span>
        </div>
      </div>"""


def update_index_html(top_article, secondary_articles):
    """Replace 'Noticia del Dia' and 'Mas Noticias' sections in index.html."""
    script_dir = os.path.dirname(os.path.abspath(__file__))
    index_path = os.path.join(os.path.dirname(script_dir), "index.html")

    if not os.path.isfile(index_path):
        logger.error("index.html not found at %s", index_path)
        return False

    try:
        with open(index_path, "r", encoding="utf-8") as f:
            content = f.read()
    except OSError as e:
        logger.error("Failed to read index.html: %s", e)
        return False

    today = datetime.now(timezone.utc).strftime("%Y-%m-%d")

    # ── SECTION 1: Noticia del Dia (featured card only) ──
    featured_card = build_news_card(top_article, EMOJIS_POOL[0], is_featured=True)

    noticia_section = f"""  <!-- =============================== -->
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
    </div>
  </section>"""

    # Replace NOTICIA DEL DIA section
    pattern = r"  <!-- [=═]+\s*-->\s*\n\s*<!-- NOTICIA DEL D[IÍi]A.*?</section>"
    match = re.search(pattern, content, re.DOTALL | re.IGNORECASE)

    if match:
        content = content[:match.start()] + noticia_section + content[match.end():]
        logger.info("Noticia del Dia section updated")
    else:
        # Fallback: insert before Videos Destacados or first section divider
        insertion_idx = -1
        for marker in ["VIDEOS DESTACADOS", "SECCION 2", "section-divider"]:
            insertion_idx = content.find(marker)
            if insertion_idx != -1:
                break
        if insertion_idx == -1:
            logger.error("Could not find insertion point for Noticia del Dia")
            return False
        comment_start = content.rfind("<!--", 0, insertion_idx)
        if comment_start == -1:
            comment_start = content.rfind("<hr", 0, insertion_idx)
        line_start = content.rfind("\n", 0, comment_start) if comment_start != -1 else -1
        if line_start == -1:
            line_start = 0
        content = content[:line_start] + "\n\n" + noticia_section + "\n\n" + content[line_start:]
        logger.info("Noticia del Dia section inserted")

    # ── SECTION 3: Mas Noticias de IA (secondary cards) ──
    secondary_html = ""
    for i, art in enumerate(secondary_articles[:MAX_SECONDARY_ARTICLES]):
        emoji = EMOJIS_POOL[(i + 1) % len(EMOJIS_POOL)]
        secondary_html += "\n\n" + build_news_card(art, emoji)

    mas_noticias_section = f"""  <!-- =============================== -->
  <!-- MAS NOTICIAS DE IA             -->
  <!-- Actualizado: {today}       -->
  <!-- =============================== -->
  <section>
    <div class="section-header reveal">
      <span class="section-emoji">📡</span>
      <h2 class="section-title">
        <span data-lang-inline="es">Mas Noticias de IA</span>
        <span data-lang-inline="en">More AI News</span>
      </h2>
      <span class="section-badge trending">
        <span data-lang-inline="es">📈 RECIENTES</span>
        <span data-lang-inline="en">📈 RECENT</span>
      </span>
    </div>

    <div class="cards-grid">
{secondary_html}
    </div>
  </section>"""

    # Replace MAS NOTICIAS section
    pattern2 = r"  <!-- [=═]+\s*-->\s*\n\s*<!-- MAS NOTICIAS.*?</section>"
    match2 = re.search(pattern2, content, re.DOTALL | re.IGNORECASE)

    if match2:
        content = content[:match2.start()] + mas_noticias_section + content[match2.end():]
        logger.info("Mas Noticias section updated")
    else:
        # Fallback: insert before "Lo que debes saber" section
        insertion_idx2 = -1
        for marker in ["LO QUE DEBES SABER", "SECCION 4", "TOP TEMAS"]:
            insertion_idx2 = content.find(marker)
            if insertion_idx2 != -1:
                break
        if insertion_idx2 != -1:
            comment_start = content.rfind("<!--", 0, insertion_idx2)
            if comment_start == -1:
                comment_start = content.rfind("<hr", 0, insertion_idx2)
            line_start = content.rfind("\n", 0, comment_start) if comment_start != -1 else -1
            if line_start == -1:
                line_start = 0
            content = content[:line_start] + "\n\n" + mas_noticias_section + "\n\n" + content[line_start:]
            logger.info("Mas Noticias section inserted")
        else:
            logger.warning("Could not find insertion point for Mas Noticias")

    # ── Update ticker with top news (bilingual) ──
    top_title_en = html.escape(top_article["title"])
    top_title_es = html.escape(top_article.get("title_es", top_article["title"]))
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

    content = re.sub(ticker_es_pattern, lambda m: update_ticker(m, top_title_es), content, flags=re.DOTALL)
    content = re.sub(ticker_en_pattern, lambda m: update_ticker(m, top_title_en), content, flags=re.DOTALL)

    try:
        with open(index_path, "w", encoding="utf-8") as f:
            f.write(content)
    except OSError as e:
        logger.error("Failed to write index.html: %s", e)
        return False

    return True


def main():
    logger.info("=" * 50)
    logger.info("AI PULSE - Daily News Updater")
    logger.info("Date: %s", datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M UTC'))
    logger.info("=" * 50)

    # Fetch all feeds
    all_articles = []
    for feed_url in FEEDS:
        logger.info("Fetching: %s", feed_url)
        entries = fetch_feed(feed_url)
        logger.info("  Found %d entries", len(entries))
        for entry in entries:
            entry["source"] = feed_url
        all_articles.extend(entries)

    # Filter AI-related
    ai_articles = [a for a in all_articles if is_ai_related(a["title"], a["description"])]
    logger.info("Total articles: %d", len(all_articles))
    logger.info("AI-related: %d", len(ai_articles))

    if not ai_articles:
        logger.warning("No AI articles found, using all articles")
        ai_articles = all_articles[:5]

    if not ai_articles:
        logger.error("No articles found at all. Exiting.")
        sys.exit(1)

    # Pick top article (first one, feeds are usually newest-first)
    top = ai_articles[0]
    secondary = ai_articles[1:MAX_SECONDARY_ARTICLES + 1]

    logger.info("Top article: %s", top['title'])
    for i, s in enumerate(secondary):
        logger.info("Secondary %d: %s", i + 1, s['title'])

    # Translate articles to Spanish
    logger.info("── Translating to Spanish ──")
    translate_article(top)
    for art in secondary:
        translate_article(art)
    logger.info("  ES title: %s", top.get('title_es', 'N/A'))

    # Update index.html
    if update_index_html(top, secondary):
        logger.info("index.html updated successfully!")
    else:
        logger.error("Failed to update index.html")
        sys.exit(1)


if __name__ == "__main__":
    main()
