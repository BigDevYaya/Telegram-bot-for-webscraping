import requests
from bs4 import BeautifulSoup
import re
from datetime import datetime
import os

header = os.getenv('HEADERS')

def fetch_html(url, timeout=12):
    resp = requests.get(url, headers=header, timeout=timeout)
    resp.raise_for_status()
    return resp.text

def absolute_link(base, link):
    return requests.compat.urljoin(base, link) if link else None

def extract_articles_from_soup(soup, base_url):
    candidates = []

    # 1) Preferred: <article> blocks
    for art in soup.find_all("article"):
        title_tag = art.find(["h1","h2","h3"])
        title = title_tag.get_text(strip=True) if title_tag else None

        # try to find a main <a>
        link_tag = art.find("a", href=True)
        link = absolute_link(base_url, link_tag['href']) if link_tag else None

        snippet_tag = art.find("p")
        snippet = snippet_tag.get_text(strip=True) if snippet_tag else None

        time_tag = art.find("time")
        date = time_tag.get("datetime") if time_tag and time_tag.has_attr("datetime") else (time_tag.get_text(strip=True) if time_tag else None)

        if title and len(title) > 8:
            candidates.append({"title": title, "link": link, "snippet": snippet, "date": date})

    # 2) Headings + anchors (fallback)
    for h in soup.find_all(["h1","h2","h3"]):
        a = h.find("a", href=True)
        title = a.get_text(strip=True) if a else h.get_text(strip=True)
        href = a['href'] if a and a.has_attr('href') else None
        link = absolute_link(base_url, href) if href else None

        # try to find close sibling paragraph as snippet
        snippet = None
        p = h.find_next_sibling("p")
        if not p:
            # maybe parent paragraph
            p = h.parent.find("p") if h.parent else None
        snippet = p.get_text(strip=True) if p else None

        if title and len(title) > 8:
            candidates.append({"title": title, "link": link, "snippet": snippet, "date": None})

    # 3) Anchor-heavy pages (last resort)
    for a in soup.find_all("a", href=True):
        text = a.get_text(" ", strip=True)
        href = a['href']
        if len(text) >= 20 and not text.lower().startswith(("read more","learn more","home")):
            link = absolute_link(base_url, href)
            candidates.append({"title": text, "link": link, "snippet": None, "date": None})

    # dedupe by normalized title
    seen = set()
    unique = []
    for c in candidates:
        t = (c.get("title") or "").strip()
        key = re.sub(r'\s+',' ', t).lower()
        if key and key not in seen:
            seen.add(key)
            unique.append(c)
    return unique

def filter_by_keywords(articles, keywords):
    kws = [k.lower() for k in keywords]
    results = []
    for a in articles:
        hay = " ".join(filter(None, [a.get("title",""), a.get("snippet",""), (a.get("link") or "")])).lower()
        if any(k in hay for k in kws):
            results.append(a)
    return results


def format_articles_message(articles, keyword=None, limit=5):
    if not articles:
        suffix = f' for "{keyword}"' if keyword else ''
        return f"❌ No articles found{suffix}."

    lines = []
    suffix = f' for "{keyword}"' if keyword else ''
    header = f"📰 Results{suffix} ({len(articles)} found):"
    lines.append(header)

    for i, art in enumerate(articles[:limit], 1):
        title = art.get("title") or "Untitled"
        link = art.get("link") or ""
        snippet = art.get("snippet") or ""
        date = art.get("date") or ""

        msg = f"\n{i}. {title}"
        if date:
            msg += f" ({date})"
        if link:
            msg += f"\n🔗 {link}"
        if snippet:
            msg += f"\n   {snippet}"

        lines.append(msg)

    return "\n".join(lines)


