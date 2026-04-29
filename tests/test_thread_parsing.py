from kagcrawl.thread import (
    _extract_author,
    _extract_author_role,
    _extract_created_at,
    _extract_thread_title,
)


SNAPSHOT = """
- main:
  - separator
  - link "Michael D. Moffitt's profile" [ref=e38]:
    - /url: /mmoffitt
  - link "Michael D. Moffitt" [ref=e39]:
    - /url: /mmoffitt
  - text: · Posted 4 hours ago · Competition Host
  - button "1 votes" [ref=e41]: "1"
  - heading "NeuroGolf Update for April 28th" [ref=e43] [level=3]
  - paragraph:
    - text: Thanks again to all teams for their helpful and detailed feedback.
"""


def test_extract_thread_metadata_from_snapshot() -> None:
    assert _extract_thread_title(SNAPSHOT, "fallback") == "NeuroGolf Update for April 28th"
    assert _extract_author(SNAPSHOT) == "Michael D. Moffitt"
    assert _extract_author_role(SNAPSHOT) == "host"
    assert _extract_created_at(SNAPSHOT) == "Posted 4 hours ago · Competition Host"
