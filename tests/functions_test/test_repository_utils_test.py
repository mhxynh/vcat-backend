import pytest

from functions.tests.test_repository import TestRepository


def test_normalize_evidence_links_none_returns_none():
    assert TestRepository._normalize_evidence_links(None) is None


def test_normalize_evidence_links_non_list_raises():
    with pytest.raises(ValueError):
        TestRepository._normalize_evidence_links("not-a-list")


def test_normalize_evidence_links_filters_none_and_empty_and_dedups():
    links = [None, "  http://a.com  ", "", "http://a.com", "http://b.com"]
    cleaned = TestRepository._normalize_evidence_links(links)
    assert cleaned == ["http://a.com", "http://b.com"]


def test_normalize_evidence_links_preserves_order_first_occurrence():
    links = ["b", "a", "b", "c"]
    assert TestRepository._normalize_evidence_links(links) == ["b", "a", "c"]
