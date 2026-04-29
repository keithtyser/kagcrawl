from kagcrawl.capabilities import CapabilityReport


def test_capability_recommendations_offline_only() -> None:
    report = CapabilityReport(False, False, False, False)
    assert report.live_discussion_crawl is False
    assert report.live_notebook_pull is False
    assert report.offline_artifacts_only is True
    assert report.recommended_modes() == ["offline_artifacts"]


def test_capability_recommendations_hybrid() -> None:
    report = CapabilityReport(True, False, True, False)
    assert report.live_discussion_crawl is True
    assert report.live_notebook_pull is False
    assert report.offline_artifacts_only is False
    assert report.recommended_modes() == ["live_discussions", "hybrid_artifacts"]
