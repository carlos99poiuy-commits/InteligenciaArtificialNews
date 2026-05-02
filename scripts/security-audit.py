#!/usr/bin/env python3
"""
AI PULSE - Security Audit Agent
Runs automated security checks on index.html and project files.
Exits with code 1 if critical issues are found.
"""

import os
import re
import sys
import logging

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
logger = logging.getLogger(__name__)

# ── CONSTANTS ──
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.dirname(SCRIPT_DIR)
INDEX_PATH = os.path.join(PROJECT_ROOT, "index.html")

# Patterns that should NEVER appear in generated HTML
DANGEROUS_PATTERNS = [
    (r"\beval\s*\(", "eval() usage detected — code injection risk"),
    (r"document\.write\s*\(", "document.write() detected — XSS risk"),
    (r"\.innerHTML\s*[=+]", "innerHTML assignment detected — XSS risk"),
    (r"onclick\s*=", "Inline onclick handler — use addEventListener"),
    (r"onerror\s*=", "Inline onerror handler — XSS risk"),
    (r"onload\s*=", "Inline onload handler — security risk"),
    (r"javascript:", "javascript: URI detected — XSS risk"),
    (r"data:text/html", "data:text/html URI — potential XSS vector"),
]

# Patterns that SHOULD exist (security headers/features)
REQUIRED_PATTERNS = [
    (r"Content-Security-Policy", "CSP meta tag missing"),
    (r"X-Content-Type-Options", "X-Content-Type-Options header missing"),
    (r'rel="noopener', "External links missing rel='noopener'"),
    (r"crossorigin", "CDN resources missing crossorigin attribute"),
    (r'aria-label', "Interactive elements missing aria-label"),
]

# Files that should NOT exist in the repo root
SENSITIVE_FILES = [
    ".env", ".env.local", ".env.production",
    "credentials.json", "secrets.json",
    "id_rsa", "id_ed25519",
    ".npmrc", ".pypirc",
]


def check_file_exists(path):
    """Verify a file exists before auditing."""
    if not os.path.isfile(path):
        logger.error("File not found: %s", path)
        return False
    return True


def audit_dangerous_patterns(content, filename):
    """Check for dangerous code patterns."""
    issues = []
    for pattern, message in DANGEROUS_PATTERNS:
        matches = list(re.finditer(pattern, content, re.IGNORECASE))
        if matches:
            for match in matches:
                line_num = content[:match.start()].count("\n") + 1
                issues.append({
                    "severity": "CRITICAL",
                    "file": filename,
                    "line": line_num,
                    "message": message,
                    "match": match.group()[:50],
                })
    return issues


def audit_required_patterns(content, filename):
    """Check that required security features are present."""
    issues = []
    for pattern, message in REQUIRED_PATTERNS:
        if not re.search(pattern, content, re.IGNORECASE):
            issues.append({
                "severity": "HIGH",
                "file": filename,
                "line": 0,
                "message": message,
            })
    return issues


def audit_external_links(content, filename):
    """Verify all target='_blank' links have rel='noopener'."""
    issues = []
    blank_links = re.finditer(r'<a\s[^>]*target="_blank"[^>]*>', content, re.IGNORECASE)
    for match in blank_links:
        tag = match.group()
        if 'rel="noopener' not in tag and "rel='noopener" not in tag:
            line_num = content[:match.start()].count("\n") + 1
            issues.append({
                "severity": "MEDIUM",
                "file": filename,
                "line": line_num,
                "message": f"target='_blank' link missing rel='noopener': {tag[:80]}",
            })
    return issues


def audit_url_schemes(content, filename):
    """Check for dangerous URL schemes in href/src attributes."""
    issues = []
    url_attrs = re.finditer(r'(?:href|src|action)\s*=\s*["\']([^"\']+)["\']', content, re.IGNORECASE)
    for match in url_attrs:
        url = match.group(1)
        if url.startswith(("javascript:", "vbscript:", "data:text/html")):
            line_num = content[:match.start()].count("\n") + 1
            issues.append({
                "severity": "CRITICAL",
                "file": filename,
                "line": line_num,
                "message": f"Dangerous URL scheme: {url[:60]}",
            })
    return issues


def audit_sensitive_files():
    """Check that no sensitive files are in the project."""
    issues = []
    for filename in SENSITIVE_FILES:
        filepath = os.path.join(PROJECT_ROOT, filename)
        if os.path.exists(filepath):
            issues.append({
                "severity": "CRITICAL",
                "file": filename,
                "line": 0,
                "message": f"Sensitive file found in project root: {filename}",
            })
    return issues


def audit_html_structure(content, filename):
    """Basic HTML structure validation."""
    issues = []

    if "<!DOCTYPE html>" not in content[:50]:
        issues.append({
            "severity": "LOW",
            "file": filename,
            "line": 1,
            "message": "Missing or misplaced DOCTYPE declaration",
        })

    open_tags = len(re.findall(r"<script[\s>]", content, re.IGNORECASE))
    close_tags = len(re.findall(r"</script>", content, re.IGNORECASE))
    if open_tags != close_tags:
        issues.append({
            "severity": "HIGH",
            "file": filename,
            "line": 0,
            "message": f"Mismatched <script> tags: {open_tags} open, {close_tags} close",
        })

    return issues


def audit_i18n_consistency(content, filename):
    """Check that data-lang-inline spans come in ES/EN pairs."""
    issues = []
    es_spans = len(re.findall(r'data-lang-inline="es"', content))
    en_spans = len(re.findall(r'data-lang-inline="en"', content))
    if es_spans != en_spans:
        issues.append({
            "severity": "MEDIUM",
            "file": filename,
            "line": 0,
            "message": f"i18n mismatch: {es_spans} Spanish spans vs {en_spans} English spans",
        })
    return issues


def generate_report(all_issues):
    """Print audit report and return exit code."""
    critical = [i for i in all_issues if i["severity"] == "CRITICAL"]
    high = [i for i in all_issues if i["severity"] == "HIGH"]
    medium = [i for i in all_issues if i["severity"] == "MEDIUM"]
    low = [i for i in all_issues if i["severity"] == "LOW"]

    logger.info("=" * 60)
    logger.info("AI PULSE — SECURITY AUDIT REPORT")
    logger.info("=" * 60)
    logger.info("CRITICAL: %d | HIGH: %d | MEDIUM: %d | LOW: %d",
                len(critical), len(high), len(medium), len(low))
    logger.info("-" * 60)

    if not all_issues:
        logger.info("ALL CHECKS PASSED — No security issues found")
        return 0

    for issue in all_issues:
        line_info = f":{issue['line']}" if issue["line"] > 0 else ""
        logger.log(
            logging.CRITICAL if issue["severity"] == "CRITICAL" else
            logging.ERROR if issue["severity"] == "HIGH" else
            logging.WARNING if issue["severity"] == "MEDIUM" else
            logging.INFO,
            "[%s] %s%s — %s",
            issue["severity"], issue["file"], line_info, issue["message"],
        )

    logger.info("-" * 60)

    if critical:
        logger.error("AUDIT FAILED — %d critical issues must be fixed", len(critical))
        return 1

    if high:
        logger.warning("AUDIT WARNING — %d high-severity issues found", len(high))
        return 1

    logger.info("AUDIT PASSED with %d minor findings", len(medium) + len(low))
    return 0


def main():
    logger.info("Starting security audit...")

    all_issues = []

    # Audit sensitive files in project root
    all_issues.extend(audit_sensitive_files())

    # Audit index.html
    if check_file_exists(INDEX_PATH):
        with open(INDEX_PATH, "r", encoding="utf-8") as f:
            content = f.read()

        all_issues.extend(audit_dangerous_patterns(content, "index.html"))
        all_issues.extend(audit_required_patterns(content, "index.html"))
        all_issues.extend(audit_external_links(content, "index.html"))
        all_issues.extend(audit_url_schemes(content, "index.html"))
        all_issues.extend(audit_html_structure(content, "index.html"))
        all_issues.extend(audit_i18n_consistency(content, "index.html"))
    else:
        all_issues.append({
            "severity": "CRITICAL",
            "file": "index.html",
            "line": 0,
            "message": "index.html not found — site is broken",
        })

    # Audit update-news.py for unsafe patterns
    updater_path = os.path.join(SCRIPT_DIR, "update-news.py")
    if check_file_exists(updater_path):
        with open(updater_path, "r", encoding="utf-8") as f:
            py_content = f.read()

        # Check Python-specific dangers
        py_dangers = [
            (r"\bos\.system\s*\(", "os.system() — command injection risk"),
            (r"\bsubprocess\..*shell\s*=\s*True", "subprocess with shell=True — injection risk"),
            (r"\bexec\s*\(", "exec() — code injection risk"),
            (r"\bpickle\.loads?\s*\(", "pickle.load() — deserialization risk"),
            (r"__import__\s*\(", "__import__() — dynamic import risk"),
        ]
        for pattern, message in py_dangers:
            matches = list(re.finditer(pattern, py_content))
            if matches:
                for match in matches:
                    line_num = py_content[:match.start()].count("\n") + 1
                    all_issues.append({
                        "severity": "CRITICAL",
                        "file": "scripts/update-news.py",
                        "line": line_num,
                        "message": message,
                    })

        # Verify URL validation exists
        if "is_safe_url" not in py_content:
            all_issues.append({
                "severity": "HIGH",
                "file": "scripts/update-news.py",
                "line": 0,
                "message": "URL validation function (is_safe_url) not found",
            })

        # Verify html.escape is used
        if "html.escape" not in py_content:
            all_issues.append({
                "severity": "HIGH",
                "file": "scripts/update-news.py",
                "line": 0,
                "message": "html.escape() not used — RSS content may be unescaped",
            })

    exit_code = generate_report(all_issues)
    sys.exit(exit_code)


if __name__ == "__main__":
    main()
