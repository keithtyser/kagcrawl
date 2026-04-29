# kagcrawl

Agent-first Kaggle discussion crawler.

v0 goals:
- crawl competition discussion threads
- extract thread text and comments
- resolve linked Kaggle notebooks via `kaggle kernels pull`
- export LLM-ready `.txt` and `.json`
- work in stateless sandbox mode first, optional local SQLite later
