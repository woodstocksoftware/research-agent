"""
Tests for src/tools/search.SearchTool.

All Tavily API calls are mocked -- no real network requests.
"""

import pytest
from unittest.mock import MagicMock, patch


# ── Constructor ────────────────────────────────────────────────────────────

class TestSearchToolInit:
    """SearchTool.__init__ reads TAVILY_API_KEY and builds a TavilyClient."""

    @patch.dict("os.environ", {"TAVILY_API_KEY": "tvly-test-key"})
    @patch("src.tools.search.TavilyClient")
    def test_init_with_valid_key(self, mock_tavily_cls):
        from src.tools.search import SearchTool
        tool = SearchTool()
        mock_tavily_cls.assert_called_once_with(api_key="tvly-test-key")
        assert tool.client is mock_tavily_cls.return_value

    @patch.dict("os.environ", {}, clear=True)
    def test_init_raises_without_key(self):
        # Need to reimport to trigger __init__ with cleared env
        from src.tools.search import SearchTool
        with pytest.raises(ValueError, match="TAVILY_API_KEY"):
            SearchTool()


# ── search() ───────────────────────────────────────────────────────────────

class TestSearchToolSearch:
    """SearchTool.search wraps TavilyClient.search and normalizes results."""

    @patch.dict("os.environ", {"TAVILY_API_KEY": "tvly-test-key"})
    @patch("src.tools.search.TavilyClient")
    def test_search_returns_normalized_results(self, mock_tavily_cls):
        from src.tools.search import SearchTool

        mock_client = mock_tavily_cls.return_value
        mock_client.search.return_value = {
            "results": [
                {
                    "title": "Page One",
                    "url": "https://example.com/1",
                    "content": "Content of page one",
                    "score": 0.95,  # extra field should be ignored
                },
                {
                    "title": "Page Two",
                    "url": "https://example.com/2",
                    "content": "Content of page two",
                },
            ]
        }

        tool = SearchTool()
        results = tool.search("test query", max_results=2)

        mock_client.search.assert_called_once_with(
            query="test query",
            max_results=2,
            include_answer=False,
            include_raw_content=False,
        )
        assert len(results) == 2
        assert results[0] == {
            "title": "Page One",
            "url": "https://example.com/1",
            "content": "Content of page one",
        }
        assert results[1] == {
            "title": "Page Two",
            "url": "https://example.com/2",
            "content": "Content of page two",
        }

    @patch.dict("os.environ", {"TAVILY_API_KEY": "tvly-test-key"})
    @patch("src.tools.search.TavilyClient")
    def test_search_handles_empty_results(self, mock_tavily_cls):
        from src.tools.search import SearchTool

        mock_client = mock_tavily_cls.return_value
        mock_client.search.return_value = {"results": []}

        tool = SearchTool()
        results = tool.search("obscure query")
        assert results == []

    @patch.dict("os.environ", {"TAVILY_API_KEY": "tvly-test-key"})
    @patch("src.tools.search.TavilyClient")
    def test_search_handles_missing_fields(self, mock_tavily_cls):
        from src.tools.search import SearchTool

        mock_client = mock_tavily_cls.return_value
        mock_client.search.return_value = {
            "results": [
                {"url": "https://example.com/no-title"},  # missing title & content
            ]
        }

        tool = SearchTool()
        results = tool.search("query")
        assert len(results) == 1
        assert results[0]["title"] == ""
        assert results[0]["content"] == ""
        assert results[0]["url"] == "https://example.com/no-title"

    @patch.dict("os.environ", {"TAVILY_API_KEY": "tvly-test-key"})
    @patch("src.tools.search.TavilyClient")
    def test_search_returns_empty_on_exception(self, mock_tavily_cls):
        from src.tools.search import SearchTool

        mock_client = mock_tavily_cls.return_value
        mock_client.search.side_effect = Exception("Tavily API error")

        tool = SearchTool()
        results = tool.search("query")
        assert results == []

    @patch.dict("os.environ", {"TAVILY_API_KEY": "tvly-test-key"})
    @patch("src.tools.search.TavilyClient")
    def test_search_default_max_results(self, mock_tavily_cls):
        from src.tools.search import SearchTool

        mock_client = mock_tavily_cls.return_value
        mock_client.search.return_value = {"results": []}

        tool = SearchTool()
        tool.search("query")  # no max_results arg

        mock_client.search.assert_called_once_with(
            query="query",
            max_results=5,  # default
            include_answer=False,
            include_raw_content=False,
        )
