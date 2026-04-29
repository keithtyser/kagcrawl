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
