"""Fetch and score recent papers from ArXiv and Papers With Code."""

import re
import time
from datetime import datetime, timedelta, timezone

import arxiv
import requests


def fetch_arxiv_papers(categories: list[str], keywords: list[str], lookback_days: int) -> list[dict]:
    client = arxiv.Client(page_size=100, delay_seconds=3)
    cutoff = datetime.now(timezone.utc) - timedelta(days=lookback_days)

    # Broad category query — we score/filter by keyword afterwards
    category_query = " OR ".join(f"cat:{c}" for c in categories)
    # Add keyword hints to narrow down (use first 6 keywords to avoid query-length limits)
    kw_sample = keywords[:6]
    kw_query = " OR ".join(f'ti:"{kw}"' for kw in kw_sample)
    query = f"({category_query}) AND ({kw_query})"

    search = arxiv.Search(
        query=query,
        max_results=150,
        sort_by=arxiv.SortCriterion.SubmittedDate,
        sort_order=arxiv.SortOrder.Descending,
    )

    papers = []
    for result in client.results(search):
        if result.published < cutoff:
            break
        arxiv_id = result.entry_id.split("/")[-1]
        papers.append({
            "arxiv_id": arxiv_id,
            "title": result.title.replace("\n", " ").strip(),
            "authors": [a.name for a in result.authors[:5]],
            "abstract": result.summary.replace("\n", " ").strip(),
            "published": result.published.strftime("%Y-%m-%d"),
            "url": f"https://arxiv.org/abs/{arxiv_id}",
            "pdf_url": result.pdf_url,
            "categories": result.categories,
            "has_code": False,
            "code_url": None,
        })

    return papers


def enrich_with_code(papers: list[dict]) -> list[dict]:
    """Check Papers With Code for code repos. Mutates papers in place."""
    pwc_base = "https://paperswithcode.com/api/v1/papers/"
    for paper in papers:
        base_id = re.sub(r"v\d+$", "", paper["arxiv_id"])
        try:
            resp = requests.get(pwc_base, params={"arxiv_id": base_id}, timeout=8)
            if resp.ok:
                results = resp.json().get("results", [])
                if results:
                    repos = results[0].get("repositories", [])
                    if repos:
                        paper["has_code"] = True
                        best = max(repos, key=lambda r: r.get("stars", 0))
                        paper["code_url"] = best.get("url")
        except Exception:
            pass
        time.sleep(0.3)
    return papers


def score(paper: dict, keywords: list[str]) -> int:
    title = paper["title"].lower()
    abstract = paper["abstract"].lower()
    s = 0
    for kw in keywords:
        kw = kw.lower()
        if kw in title:
            s += 3
        elif kw in abstract:
            s += 1
    if paper["has_code"]:
        s += 5
    if "cs.RO" in paper.get("categories", []):
        s += 2
    return s


def fetch_and_filter(config: dict) -> list[dict]:
    papers = fetch_arxiv_papers(
        config["arxiv_categories"],
        config["keywords"],
        config["lookback_days"],
    )
    papers = enrich_with_code(papers)
    keywords = config["keywords"]
    for paper in papers:
        paper["score"] = score(paper, keywords)
    papers.sort(key=lambda p: (-p["score"], -p["has_code"]))
    return papers[: config["max_papers"]]
