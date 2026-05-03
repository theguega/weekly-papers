# weekly-papers

Automated weekly digest of VLA & robot learning papers — curated from ArXiv and Papers With Code, summarized with Gemini Flash, published to GitHub Pages.

Every Monday at 07:00 UTC a GitHub Action fetches the latest papers, scores them by relevance and code availability, calls Gemini Flash for structured summaries, and commits a self-contained HTML digest to `docs/`.

---

## Configuration

Edit `config.yaml` to tune what gets fetched:

| Key                | Default                  | Description                |
| ------------------ | ------------------------ | -------------------------- |
| `keywords`         | VLA, diffusion policy, … | Relevance scoring keywords |
| `arxiv_categories` | cs.RO, cs.LG, cs.CV      | ArXiv categories to search |
| `max_papers`       | 12                       | Max papers per digest      |
| `lookback_days`    | 8                        | How far back to search     |
| `gemini_model`     | gemini-2.0-flash         | Gemini model to use        |

---

## Local run

```bash
uv sync
export GEMINI_API_KEY=your_key
uv run python scripts/run.py
# open docs/digests/YYYY-WNN.html
```

---

## How it works

```
ArXiv API ──┐
            ├─→ fetch.py (score by keywords + has-code) ─→ top 12
PWC API  ───┘
                    ↓
             summarize.py (Gemini Flash, 4-field card per paper)
                    ↓
              render.py (self-contained HTML)
                    ↓
           docs/digests/YYYY-WNN.html + docs/index.html
                    ↓
            GitHub Actions commits → GitHub Pages
```

Papers are ranked by: has-code repo (+5) → keyword hits in title (+3 each) → keyword hits in abstract (+1 each) → cs.RO category (+2). Top `max_papers` are kept.
