"""Generate the HTML digest and update docs/index.html."""

import json
from datetime import datetime, timedelta
from pathlib import Path

# ── CSS ──────────────────────────────────────────────────────────────────────
# Defined as a plain string so no Python format escaping is needed.
CSS = """
* { box-sizing: border-box; margin: 0; padding: 0; }

body {
  font-family: 'Inter', system-ui, -apple-system, sans-serif;
  background: #f0f2f5;
  color: #1e293b;
  line-height: 1.65;
  font-size: 15px;
}

a { color: inherit; }

.container {
  max-width: 860px;
  margin: 0 auto;
  padding: 0 24px;
}

/* ── Header ── */
header {
  background: #0f172a;
  color: #f8fafc;
  padding: 52px 0 44px;
  margin-bottom: 44px;
}
.logo {
  font-size: 11px;
  font-weight: 600;
  letter-spacing: 0.18em;
  text-transform: uppercase;
  color: #7c6af7;
  margin-bottom: 14px;
}
header h1 {
  font-size: 26px;
  font-weight: 700;
  letter-spacing: -0.02em;
  margin-bottom: 6px;
}
.subtitle {
  font-size: 14px;
  color: #94a3b8;
  margin-bottom: 24px;
}
.stats {
  display: flex;
  gap: 10px;
  flex-wrap: wrap;
}
.stat {
  font-size: 12px;
  font-weight: 500;
  padding: 4px 12px;
  border-radius: 20px;
  background: rgba(124, 106, 247, 0.15);
  color: #a89cf7;
}

/* ── Paper cards ── */
.papers {
  display: flex;
  flex-direction: column;
  gap: 20px;
  margin-bottom: 64px;
}

.card {
  background: #ffffff;
  border-radius: 12px;
  border-left: 4px solid #c7d2fe;
  padding: 26px 28px 22px;
  box-shadow: 0 1px 4px rgba(0,0,0,0.06);
  transition: box-shadow 0.2s;
}
.card:hover { box-shadow: 0 4px 16px rgba(0,0,0,0.10); }
.card.has-code { border-left-color: #34d399; }

.card-top {
  display: flex;
  align-items: center;
  gap: 8px;
  flex-wrap: wrap;
  margin-bottom: 12px;
}

.badge {
  font-size: 10px;
  font-weight: 700;
  letter-spacing: 0.08em;
  text-transform: uppercase;
  padding: 3px 9px;
  border-radius: 4px;
}
.badge-code { background: #d1fae5; color: #065f46; }
.badge-cat  { background: #ede9fe; color: #5b21b6; }

.card-title {
  font-size: 17px;
  font-weight: 650;
  line-height: 1.4;
  letter-spacing: -0.01em;
  margin-bottom: 5px;
}
.card-title a {
  text-decoration: none;
  color: #0f172a;
}
.card-title a:hover { color: #4f46e5; }

.card-meta {
  font-size: 12.5px;
  color: #94a3b8;
  margin-bottom: 18px;
}

.one-liner {
  font-size: 14px;
  font-style: italic;
  color: #475569;
  border-left: 3px solid #e0e7ff;
  padding-left: 14px;
  margin-bottom: 22px;
  line-height: 1.55;
}

/* ── 4-section summary grid ── */
.sections {
  display: grid;
  grid-template-columns: max-content 1fr;
  gap: 6px 12px;
  margin-bottom: 22px;
  align-items: start;
}
.sec-label {
  font-size: 10.5px;
  font-weight: 700;
  letter-spacing: 0.1em;
  text-transform: uppercase;
  padding-top: 3px;
  white-space: nowrap;
}
.lbl-problem   { color: #dc2626; }
.lbl-approach  { color: #2563eb; }
.lbl-result    { color: #7c3aed; }
.lbl-relevance { color: #059669; }
.sec-content {
  font-size: 13.5px;
  color: #334155;
  line-height: 1.6;
}

/* ── Links ── */
.card-links { display: flex; gap: 8px; flex-wrap: wrap; }
.btn {
  font-size: 12.5px;
  font-weight: 500;
  padding: 6px 14px;
  border-radius: 6px;
  text-decoration: none;
  transition: background 0.15s;
}
.btn-arxiv { background: #f1f5f9; color: #475569; }
.btn-arxiv:hover { background: #e2e8f0; color: #1e293b; }
.btn-code  { background: #d1fae5; color: #065f46; }
.btn-code:hover { background: #a7f3d0; }

/* ── Footer ── */
footer {
  background: #0f172a;
  color: #64748b;
  padding: 28px 0;
  font-size: 13px;
}
footer .container {
  display: flex;
  justify-content: space-between;
  align-items: center;
  flex-wrap: wrap;
  gap: 12px;
}
footer a { color: #94a3b8; text-decoration: none; }
footer a:hover { color: #f8fafc; }

/* ── Index page ── */
.digest-list {
  display: flex;
  flex-direction: column;
  gap: 14px;
  margin-bottom: 64px;
}
.digest-entry {
  background: #ffffff;
  border-radius: 10px;
  padding: 18px 22px;
  box-shadow: 0 1px 4px rgba(0,0,0,0.06);
  display: flex;
  justify-content: space-between;
  align-items: center;
  gap: 16px;
}
.digest-info { display: flex; flex-direction: column; gap: 4px; }
.digest-week { font-weight: 600; font-size: 15px; color: #0f172a; }
.digest-meta { font-size: 13px; color: #94a3b8; }
.btn-view {
  font-size: 13px;
  font-weight: 500;
  padding: 7px 16px;
  border-radius: 7px;
  background: #ede9fe;
  color: #4f46e5;
  text-decoration: none;
  white-space: nowrap;
}
.btn-view:hover { background: #ddd6fe; }

@media (max-width: 600px) {
  .sections { grid-template-columns: 1fr; }
  .sec-label { margin-bottom: -4px; }
  .digest-entry { flex-direction: column; align-items: flex-start; }
}
"""


def _page_shell(title: str, body: str) -> str:
    return f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>{title}</title>
  <link rel="preconnect" href="https://fonts.googleapis.com">
  <link href="https://fonts.googleapis.com/css2?family=Inter:ital,wght@0,400;0,500;0,600;0,700;1,400&display=swap" rel="stylesheet">
  <style>{CSS}</style>
</head>
<body>
{body}
</body>
</html>"""


def _card_html(paper: dict) -> str:
    s = paper.get("summary", {})
    has_code = paper["has_code"]
    card_class = "card has-code" if has_code else "card"

    # Badges
    code_badge = '<span class="badge badge-code">&#x2713; Code</span>' if has_code else ""
    primary_cat = paper["categories"][0] if paper["categories"] else ""
    cat_badge = f'<span class="badge badge-cat">{primary_cat}</span>' if primary_cat else ""
    badges = f'<div class="card-top">{code_badge}{cat_badge}</div>'

    # Authors line
    authors = paper["authors"]
    author_str = ", ".join(authors[:3])
    if len(paper["authors"]) > 3:
        author_str += " et al."
    meta = f"{author_str} &nbsp;·&nbsp; {paper['published']}"

    # Links
    arxiv_link = f'<a class="btn btn-arxiv" href="{paper["url"]}" target="_blank">ArXiv ↗</a>'
    code_link = ""
    if has_code and paper.get("code_url"):
        code_link = f'<a class="btn btn-code" href="{paper["code_url"]}" target="_blank">Code ↗</a>'

    # Summary sections — fall back gracefully if empty
    def row(label_class: str, label: str, text: str) -> str:
        if not text:
            return ""
        return (
            f'<span class="sec-label {label_class}">{label}</span>'
            f'<span class="sec-content">{text}</span>'
        )

    sections = (
        row("lbl-problem",   "Problem",   s.get("problem", ""))
        + row("lbl-approach",  "Approach",  s.get("approach", ""))
        + row("lbl-result",    "Result",    s.get("result", ""))
        + row("lbl-relevance", "Why it matters", s.get("relevance", ""))
    )

    one_liner = s.get("one_liner", "")
    one_liner_html = f'<p class="one-liner">{one_liner}</p>' if one_liner else ""

    return f"""<div class="{card_class}">
  {badges}
  <h2 class="card-title"><a href="{paper['url']}" target="_blank">{paper['title']}</a></h2>
  <p class="card-meta">{meta}</p>
  {one_liner_html}
  <div class="sections">{sections}</div>
  <div class="card-links">{arxiv_link}{code_link}</div>
</div>"""


def _week_label(iso_week: int, year: int, lookback_days: int) -> str:
    """Return a human-readable date range for the digest."""
    # End of range = today; start = lookback_days ago
    today = datetime.utcnow()
    start = today - timedelta(days=lookback_days - 1)
    fmt = "%b %-d"
    return f"{start.strftime(fmt)} – {today.strftime(fmt)}, {year}"


def generate_digest(papers: list[dict], docs_dir: Path, lookback_days: int) -> str:
    """Write the weekly digest HTML. Returns the relative filename."""
    now = datetime.utcnow()
    iso_week = now.isocalendar()[1]
    year = now.year
    filename = f"{year}-W{iso_week:02d}.html"
    date_range = _week_label(iso_week, year, lookback_days)

    n_with_code = sum(1 for p in papers if p["has_code"])
    cards_html = "\n".join(_card_html(p) for p in papers)

    header = f"""<header>
  <div class="container">
    <div class="logo">weekly-papers</div>
    <h1>VLA &amp; Robot Learning Digest</h1>
    <p class="subtitle">{date_range}</p>
    <div class="stats">
      <span class="stat">{len(papers)} papers</span>
      <span class="stat">{n_with_code} with code</span>
    </div>
  </div>
</header>"""

    main = f"""<main class="container">
  <div class="papers">
{cards_html}
  </div>
</main>"""

    footer = f"""<footer>
  <div class="container">
    <a href="../index.html">&#8592; All digests</a>
    <span>Curated from ArXiv &amp; Papers With Code &nbsp;·&nbsp; Summarized with Gemini Flash</span>
  </div>
</footer>"""

    html = _page_shell(f"Weekly Papers · {date_range}", f"{header}\n{main}\n{footer}")
    out = docs_dir / "digests" / filename
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(html, encoding="utf-8")
    return filename


def _read_digest_meta(path: Path) -> dict | None:
    """Extract week label and stats from an existing digest HTML."""
    try:
        text = path.read_text(encoding="utf-8")
        import re
        title_m = re.search(r"<title>Weekly Papers · (.+?)</title>", text)
        papers_m = re.search(r"<span class=\"stat\">(\d+) papers</span>", text)
        code_m   = re.search(r"<span class=\"stat\">(\d+) with code</span>", text)
        return {
            "filename": path.name,
            "date_range": title_m.group(1) if title_m else path.stem,
            "n_papers": int(papers_m.group(1)) if papers_m else "?",
            "n_code":   int(code_m.group(1))   if code_m   else "?",
        }
    except Exception:
        return None


def update_index(docs_dir: Path) -> None:
    """Regenerate docs/index.html from all digest files."""
    digests_dir = docs_dir / "digests"
    digest_files = sorted(digests_dir.glob("*.html"), reverse=True)

    entries_html = ""
    for f in digest_files:
        meta = _read_digest_meta(f)
        if not meta:
            continue
        entries_html += f"""<div class="digest-entry">
  <div class="digest-info">
    <span class="digest-week">{meta['date_range']}</span>
    <span class="digest-meta">{meta['n_papers']} papers &nbsp;·&nbsp; {meta['n_code']} with code</span>
  </div>
  <a class="btn-view" href="digests/{meta['filename']}">View digest &rarr;</a>
</div>
"""

    if not entries_html:
        entries_html = "<p style='color:#94a3b8'>No digests yet. Run the workflow to generate one.</p>"

    header = """<header>
  <div class="container">
    <div class="logo">weekly-papers</div>
    <h1>VLA &amp; Robot Learning Digest</h1>
    <p class="subtitle">Weekly curated papers on robot learning, VLAs &amp; imitation learning.</p>
  </div>
</header>"""

    main = f"""<main class="container">
  <div class="digest-list">
{entries_html}
  </div>
</main>"""

    footer = """<footer>
  <div class="container">
    <span>Curated from ArXiv &amp; Papers With Code &nbsp;·&nbsp; Summarized with Gemini Flash</span>
  </div>
</footer>"""

    html = _page_shell("Weekly Papers · VLA & Robot Learning", f"{header}\n{main}\n{footer}")
    (docs_dir / "index.html").write_text(html, encoding="utf-8")
