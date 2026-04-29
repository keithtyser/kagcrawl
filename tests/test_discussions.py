from kagcrawl.discussions import _extract_discussion_urls_from_snapshot


def test_extract_discussion_urls_from_snapshot_dedupes_and_filters() -> None:
    snapshot = """
- link "Thread one" [ref=e1]:
  - /url: /competitions/neurogolf-2026/discussion/695230
- link "Thread two" [ref=e2]:
  - /url: /competitions/neurogolf-2026/discussion/694772
- link "Comment permalink" [ref=e3]:
  - /url: /competitions/neurogolf-2026/discussion/695230#3449841
- link "Other competition" [ref=e4]:
  - /url: /competitions/other-comp/discussion/123
- link "External" [ref=e5]:
  - /url: https://example.com/post
- link "Thread one again" [ref=e6]:
  - /url: https://www.kaggle.com/competitions/neurogolf-2026/discussion/695230
"""
    urls = _extract_discussion_urls_from_snapshot(snapshot, "neurogolf-2026")
    assert urls == [
        "https://www.kaggle.com/competitions/neurogolf-2026/discussion/695230",
        "https://www.kaggle.com/competitions/neurogolf-2026/discussion/694772",
    ]
