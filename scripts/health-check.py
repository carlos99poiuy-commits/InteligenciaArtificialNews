#!/usr/bin/env python3
"""
AI PULSE - Site Health Check Agent
Validates that the live site is healthy: links work, i18n is complete,
sections are present, and content is fresh.
"""

import os
import re
import sys
import urllib.request
import urllib.error
import logging
from datetime import datetime, timezone, timedelta

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
logger = logging.getLogger(__name__)

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.dirname(SCRIPT_DIR)
INDEX_PATH = os.path.join(PROJECT_ROOT, "index.html")

# Sections that must exist in the page
REQUIRED_SECTIONS = [
    "NOTICIA DEL DIA",
    "VIDEOS DESTACADOS",
    "MAS NOTICIAS DE IA",
    "LO QUE DEBES SABER",
]

# CSS classes that must exist
REQUIRED_CSS_CLASSES = [
    "section-divider",
    "card-featured",
    "ticker-inner",
    "cards-grid",
    "section-header",
]

HTTP_TIMEOUT = 10
MAX_STALE_DAYS = 3


def check_sections_present(content):
    """Verify all required sections exist in HTML."""
    issues = []
    for section in REQUIRED_SECTIONS:
        if section not in content:
            issues.append({
                "severity": "HIGH",
                "check": "sections",
                "message": f"Missing section: {section}",
            })
        else:
            logger.info("  Section found: %s", section)
    return issues


def check_css_classes(content):
    """Verify required CSS classes are defined."""
    issues = []
    for cls in REQUIRED_CSS_CLASSES:
        if cls not in content:
            issues.append({
                "severity": "MEDIUM",
                "check": "css",
                "message": f"Missing CSS class: .{cls}",
            })
    return issues


def check_i18n_completeness(content):
    """Verify bilingual coverage is balanced."""
    issues = []

    es_block = len(re.findall(r'data-lang="es"', content))
    en_block = len(re.findall(r'data-lang="en"', content))
    es_inline = len(re.findall(r'data-lang-inline="es"', content))
    en_inline = len(re.findall(r'data-lang-inline="en"', content))

    logger.info("  Block:  ES=%d EN=%d", es_block, en_block)
    logger.info("  Inline: ES=%d EN=%d", es_inline, en_inline)

    if es_block != en_block:
        issues.append({
            "severity": "MEDIUM",
            "check": "i18n",
            "message": f"Block lang mismatch: {es_block} ES vs {en_block} EN",
        })

    if es_inline != en_inline:
        issues.append({
            "severity": "MEDIUM",
            "check": "i18n",
            "message": f"Inline lang mismatch: {es_inline} ES vs {en_inline} EN",
        })

    # Check for untranslated content (English text inside ES spans)
    es_spans = re.findall(r'data-lang-inline="es">([^<]+)<', content)
    for text in es_spans:
        text = text.strip()
        if len(text) < 5:
            continue
        # Simple heuristic: if it starts with common English words, flag it
        english_starters = ["the ", "a ", "an ", "this ", "that ", "sources:", "legal "]
        if any(text.lower().startswith(w) for w in english_starters):
            issues.append({
                "severity": "HIGH",
                "check": "i18n",
                "message": f"Possible untranslated ES text: '{text[:60]}...'",
            })

    return issues


def check_content_freshness(content):
    """Check if news content is recent (not stale)."""
    issues = []

    # Look for "Actualizado:" date in comments
    dates = re.findall(r"Actualizado:\s*(\d{4}-\d{2}-\d{2})", content)
    if not dates:
        issues.append({
            "severity": "MEDIUM",
            "check": "freshness",
            "message": "No 'Actualizado' date found in HTML comments",
        })
        return issues

    latest = max(dates)
    try:
        update_date = datetime.strptime(latest, "%Y-%m-%d").replace(tzinfo=timezone.utc)
        now = datetime.now(timezone.utc)
        days_old = (now - update_date).days

        logger.info("  Last update: %s (%d days ago)", latest, days_old)

        if days_old > MAX_STALE_DAYS:
            issues.append({
                "severity": "HIGH",
                "check": "freshness",
                "message": f"Content is {days_old} days old (last: {latest}, max: {MAX_STALE_DAYS})",
            })
    except ValueError:
        issues.append({
            "severity": "LOW",
            "check": "freshness",
            "message": f"Could not parse date: {latest}",
        })

    return issues


def check_external_links(content):
    """Verify external links are reachable (HTTP HEAD)."""
    issues = []

    links = re.findall(r'href="(https?://[^"]+)"', content)
    unique_links = list(dict.fromkeys(links))  # dedupe preserving order

    logger.info("  Checking %d unique external links...", len(unique_links))

    for url in unique_links:
        # Skip known CDN/font URLs (always up)
        if "fonts.googleapis.com" in url or "fonts.gstatic.com" in url:
            continue
        try:
            req = urllib.request.Request(url, method="HEAD", headers={
                "User-Agent": "AI-PULSE-HealthCheck/1.0",
            })
            with urllib.request.urlopen(req, timeout=HTTP_TIMEOUT) as resp:
                status = resp.status
                if status >= 400:
                    issues.append({
                        "severity": "MEDIUM",
                        "check": "links",
                        "message": f"HTTP {status} — {url[:80]}",
                    })
                else:
                    logger.info("    OK %d — %s", status, url[:60])
        except urllib.error.HTTPError as e:
            # Some sites block HEAD, try GET
            if e.code == 405:
                logger.info("    SKIP (HEAD not allowed) — %s", url[:60])
            else:
                issues.append({
                    "severity": "MEDIUM",
                    "check": "links",
                    "message": f"HTTP {e.code} — {url[:80]}",
                })
        except (urllib.error.URLError, OSError) as e:
            issues.append({
                "severity": "MEDIUM",
                "check": "links",
                "message": f"Unreachable — {url[:60]}: {e}",
            })

    return issues


def check_page_size(content):
    """Warn if page is too large."""
    issues = []
    size_kb = len(content.encode("utf-8")) / 1024
    logger.info("  Page size: %.1f KB", size_kb)

    if size_kb > 500:
        issues.append({
            "severity": "LOW",
            "check": "performance",
            "message": f"Page size is {size_kb:.0f} KB (recommended: <500 KB)",
        })
    return issues


def generate_report(all_issues):
    """Print health check report."""
    critical = [i for i in all_issues if i["severity"] == "CRITICAL"]
    high = [i for i in all_issues if i["severity"] == "HIGH"]
    medium = [i for i in all_issues if i["severity"] == "MEDIUM"]
    low = [i for i in all_issues if i["severity"] == "LOW"]

    logger.info("=" * 60)
    logger.info("AI PULSE — SITE HEALTH CHECK REPORT")
    logger.info("=" * 60)
    logger.info("CRITICAL: %d | HIGH: %d | MEDIUM: %d | LOW: %d",
                len(critical), len(high), len(medium), len(low))
    logger.info("-" * 60)

    if not all_issues:
        logger.info("ALL CHECKS PASSED — Site is healthy")
        return 0

    for issue in all_issues:
        logger.log(
            logging.CRITICAL if issue["severity"] == "CRITICAL" else
            logging.ERROR if issue["severity"] == "HIGH" else
            logging.WARNING if issue["severity"] == "MEDIUM" else
            logging.INFO,
            "[%s] [%s] %s",
            issue["severity"], issue["check"], issue["message"],
        )

    logger.info("-" * 60)

    if critical or high:
        logger.error("HEALTH CHECK FAILED — issues require attention")
        return 1

    logger.info("HEALTH CHECK PASSED with %d minor findings", len(medium) + len(low))
    return 0


def main():
    logger.info("Starting health check...")

    if not os.path.isfile(INDEX_PATH):
        logger.error("index.html not found at %s", INDEX_PATH)
        sys.exit(1)

    with open(INDEX_PATH, "r", encoding="utf-8") as f:
        content = f.read()

    all_issues = []

    logger.info("\n[1/6] Checking required sections...")
    all_issues.extend(check_sections_present(content))

    logger.info("\n[2/6] Checking CSS classes...")
    all_issues.extend(check_css_classes(content))

    logger.info("\n[3/6] Checking i18n completeness...")
    all_issues.extend(check_i18n_completeness(content))

    logger.info("\n[4/6] Checking content freshness...")
    all_issues.extend(check_content_freshness(content))

    logger.info("\n[5/6] Checking external links...")
    all_issues.extend(check_external_links(content))

    logger.info("\n[6/6] Checking page size...")
    all_issues.extend(check_page_size(content))

    exit_code = generate_report(all_issues)
    sys.exit(exit_code)


if __name__ == "__main__":
    main()
