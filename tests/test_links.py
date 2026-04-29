from kagcrawl.utils.links import classify_link, parse_competition_slug, parse_discussion_id, parse_notebook_slug


def test_classify_link():
    assert classify_link("https://www.kaggle.com/competitions/foo/discussion/123") == "discussion"
    assert classify_link("https://www.kaggle.com/code/mmoffitt/demo") == "notebook"
    assert classify_link("https://example.com/x") == "external"


def test_parse_helpers():
    assert parse_competition_slug("https://www.kaggle.com/competitions/foo/discussion/123") == "foo"
    assert parse_discussion_id("https://www.kaggle.com/competitions/foo/discussion/123") == "123"
    assert parse_notebook_slug("https://www.kaggle.com/code/mmoffitt/demo") == ("mmoffitt", "demo")
