# kagcrawl

Agent-first Kaggle discussion crawler.

What works now:
- discovers competition discussion threads from live Kaggle pages
- extracts thread text from Kaggle discussion pages using accessibility snapshots
- pulls Kaggle notebooks with `kaggle kernels pull` and parses `.ipynb`
- resolves linked notebooks automatically during `alpha --resolve-notebooks` and `context --resolve-notebooks`
- exports alpha reports as `.txt` or `.json`
- works stateless-first, which makes it usable in sandboxed agent environments

How discussion discovery works:
- preferred path: `agent-browser` accessibility snapshots
- fallback path: plain HTTP HTML parsing

Why this matters:
Kaggle discussion listings and notebook pages are annoying for generic chatbots. `kagcrawl` uses the same style of browser-accessibility extraction that actually works on those pages instead of trusting raw rendered HTML.

API mode:
- FastAPI app lives at `src/kagcrawl/api.py`
- local run:
  uvicorn kagcrawl.api:app --host 0.0.0.0 --port 8787
- auth:
  - set `KAGCRAWL_API_KEY` in the server environment
  - `GET /health` stays public
  - all other endpoints require either `X-API-Key: <key>` or `Authorization: Bearer <key>`
- endpoints:
  - `GET /health`
  - `GET /doctor`
  - `POST /alpha`
  - `POST /thread`
  - `POST /notebook`

Example API call:
- `curl -H 'X-API-Key: YOUR_KEY' https://kagcrawl.keithtyser.com/doctor`
- `curl -X POST https://kagcrawl.keithtyser.com/alpha -H 'Content-Type: application/json' -H 'X-API-Key: YOUR_KEY' -d '{"competition":"neurogolf-2026","max_threads":10,"resolve_notebooks":true}'`

ChatGPT sandbox tip:
- first run:
  python kagcrawl_singlefile.py doctor
- if `git clone` or `pip install` is blocked, upload `kagcrawl_singlefile.py` directly into the sandbox and run it there
- if live crawling is available:
  python kagcrawl_singlefile.py alpha neurogolf-2026 --max-threads 10 --resolve-notebooks --format txt
- if the sandbox has no network, no `agent-browser`, or no `kaggle` CLI, upload discussion snapshots/json plus `.ipynb` files and run offline/hybrid mode:
  python kagcrawl_singlefile.py alpha neurogolf-2026 --thread-artifact-dir ./threads --notebook-artifact-dir ./notebooks --format txt
