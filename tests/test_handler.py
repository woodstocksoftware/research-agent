"""
Tests for src/lambda/handler.

The handler module initialises Anthropic and Tavily clients at module level,
so we must patch os.environ and the client constructors BEFORE importing it.
Each test class handles this via setUp/import mechanics.
"""

import json
import importlib
import pytest
from unittest.mock import MagicMock, patch

from tests.conftest import (
    make_claude_response,
    SAMPLE_QUESTIONS,
    SAMPLE_SEARCH_RESULTS,
    SAMPLE_FINDINGS,
    SAMPLE_GAPS,
    SAMPLE_REPORT,
)


# ---------------------------------------------------------------------------
# We need to import the handler module with mocked env vars and clients.
# This fixture reloads the module each time to ensure a clean state.
# ---------------------------------------------------------------------------

@pytest.fixture
def handler_module():
    """
    Import (or reimport) src.lambda.handler with mocked environment
    and mocked Anthropic / Tavily clients.  Returns (module, mock_anthropic,
    mock_tavily) so tests can configure return values.
    """
    mock_anthropic = MagicMock()
    mock_tavily = MagicMock()

    env = {
        "ANTHROPIC_API_KEY": "sk-ant-test-key",
        "TAVILY_API_KEY": "tvly-test-key",
    }

    with patch.dict("os.environ", env, clear=False), \
         patch("anthropic.Anthropic", return_value=mock_anthropic) as _ac, \
         patch("tavily.TavilyClient", return_value=mock_tavily) as _tc:
        # Force re-import so module-level init runs with our mocks
        # Can't use `import src.lambda.handler` because `lambda` is a reserved word
        handler_mod = importlib.import_module("src.lambda.handler")
        importlib.reload(handler_mod)

    # After reload, the module's globals point to our mocks
    handler_mod.anthropic_client = mock_anthropic
    handler_mod.tavily_client = mock_tavily

    return handler_mod, mock_anthropic, mock_tavily


# ═══════════════════════════════════════════════════════════════════════════
# search() function
# ═══════════════════════════════════════════════════════════════════════════

class TestHandlerSearch:

    def test_search_returns_normalized_results(self, handler_module):
        mod, _, mock_tavily = handler_module
        mock_tavily.search.return_value = {
            "results": [
                {"title": "T1", "url": "https://u1", "content": "C1", "score": 0.9},
                {"title": "T2", "url": "https://u2", "content": "C2"},
            ]
        }

        results = mod.search("query", max_results=2)

        assert len(results) == 2
        assert results[0] == {"title": "T1", "url": "https://u1", "content": "C1"}
        mock_tavily.search.assert_called_once_with(
            query="query",
            max_results=2,
            include_answer=False,
            include_raw_content=False,
        )

    def test_search_returns_empty_on_exception(self, handler_module):
        mod, _, mock_tavily = handler_module
        mock_tavily.search.side_effect = Exception("API down")

        results = mod.search("query")
        assert results == []


# ═══════════════════════════════════════════════════════════════════════════
# plan_research()
# ═══════════════════════════════════════════════════════════════════════════

class TestHandlerPlanResearch:

    def test_parses_plain_json(self, handler_module):
        mod, mock_anthropic, _ = handler_module
        mock_anthropic.messages.create.return_value = make_claude_response(
            json.dumps(SAMPLE_QUESTIONS)
        )

        questions = mod.plan_research("quantum computing")
        assert questions == SAMPLE_QUESTIONS

    def test_parses_code_block_json(self, handler_module):
        mod, mock_anthropic, _ = handler_module
        text = "```json\n" + json.dumps(SAMPLE_QUESTIONS) + "\n```"
        mock_anthropic.messages.create.return_value = make_claude_response(text)

        questions = mod.plan_research("quantum computing")
        assert questions == SAMPLE_QUESTIONS

    def test_fallback_on_invalid_json(self, handler_module):
        mod, mock_anthropic, _ = handler_module
        mock_anthropic.messages.create.return_value = make_claude_response(
            "Not valid JSON at all"
        )

        questions = mod.plan_research("quantum computing")
        assert len(questions) == 4
        assert any("quantum computing" in q for q in questions)


# ═══════════════════════════════════════════════════════════════════════════
# extract_findings()
# ═══════════════════════════════════════════════════════════════════════════

class TestHandlerExtractFindings:

    def test_extracts_findings(self, handler_module):
        mod, mock_anthropic, _ = handler_module
        mock_anthropic.messages.create.return_value = make_claude_response(
            json.dumps(SAMPLE_FINDINGS)
        )

        findings = mod.extract_findings("question", SAMPLE_SEARCH_RESULTS)
        assert len(findings) == 3

    def test_returns_empty_on_bad_json(self, handler_module):
        mod, mock_anthropic, _ = handler_module
        mock_anthropic.messages.create.return_value = make_claude_response("garbage")

        findings = mod.extract_findings("question", SAMPLE_SEARCH_RESULTS)
        assert findings == []


# ═══════════════════════════════════════════════════════════════════════════
# identify_gaps()
# ═══════════════════════════════════════════════════════════════════════════

class TestHandlerIdentifyGaps:

    def test_returns_gaps(self, handler_module):
        mod, mock_anthropic, _ = handler_module
        mock_anthropic.messages.create.return_value = make_claude_response(
            json.dumps(SAMPLE_GAPS)
        )

        gaps = mod.identify_gaps("topic", SAMPLE_FINDINGS)
        assert gaps == SAMPLE_GAPS

    def test_returns_empty_on_no_gaps(self, handler_module):
        mod, mock_anthropic, _ = handler_module
        mock_anthropic.messages.create.return_value = make_claude_response("[]")

        gaps = mod.identify_gaps("topic", SAMPLE_FINDINGS)
        assert gaps == []


# ═══════════════════════════════════════════════════════════════════════════
# synthesize_report()
# ═══════════════════════════════════════════════════════════════════════════

class TestHandlerSynthesizeReport:

    def test_returns_report(self, handler_module):
        mod, mock_anthropic, _ = handler_module
        mock_anthropic.messages.create.return_value = make_claude_response(SAMPLE_REPORT)

        report = mod.synthesize_report("topic", SAMPLE_FINDINGS)
        assert report == SAMPLE_REPORT

    def test_deduplicates_findings(self, handler_module):
        mod, mock_anthropic, _ = handler_module
        mock_anthropic.messages.create.return_value = make_claude_response("# Report")

        duplicated = SAMPLE_FINDINGS + [SAMPLE_FINDINGS[0]]
        mod.synthesize_report("topic", duplicated)

        prompt = mock_anthropic.messages.create.call_args.kwargs["messages"][0]["content"]
        fact = SAMPLE_FINDINGS[0]["fact"]
        assert prompt.count(fact) == 1


# ═══════════════════════════════════════════════════════════════════════════
# research() pipeline
# ═══════════════════════════════════════════════════════════════════════════

class TestHandlerResearch:

    def test_full_pipeline_no_gaps(self, handler_module):
        mod, mock_anthropic, mock_tavily = handler_module

        mock_tavily.search.return_value = {
            "results": [
                {"title": "T", "url": "https://u", "content": "C"},
            ]
        }

        responses = [
            # plan_research
            make_claude_response(json.dumps(["Q1", "Q2"])),
            # extract_findings x2
            make_claude_response(json.dumps(SAMPLE_FINDINGS[:1])),
            make_claude_response(json.dumps(SAMPLE_FINDINGS[1:2])),
            # identify_gaps → empty
            make_claude_response("[]"),
            # synthesize_report
            make_claude_response(SAMPLE_REPORT),
        ]
        mock_anthropic.messages.create.side_effect = responses

        result = mod.research("quantum computing")

        assert "report" in result
        assert result["report"] == SAMPLE_REPORT
        assert result["findings_count"] == 2
        assert "iterations" in result
        assert "log" in result
        assert isinstance(result["log"], list)

    def test_pipeline_with_gaps(self, handler_module):
        mod, mock_anthropic, mock_tavily = handler_module

        mock_tavily.search.return_value = {
            "results": [
                {"title": "T", "url": "https://u", "content": "C"},
            ]
        }

        responses = [
            # plan_research
            make_claude_response(json.dumps(["Q1"])),
            # extract_findings x1 (iteration 1)
            make_claude_response(json.dumps(SAMPLE_FINDINGS[:1])),
            # identify_gaps → new question
            make_claude_response(json.dumps(["Gap Q1"])),
            # extract_findings x1 (iteration 2)
            make_claude_response(json.dumps(SAMPLE_FINDINGS[1:2])),
            # identify_gaps → done
            make_claude_response("[]"),
            # synthesize_report
            make_claude_response(SAMPLE_REPORT),
        ]
        mock_anthropic.messages.create.side_effect = responses

        result = mod.research("topic")

        assert result["findings_count"] == 2
        assert result["iterations"] == 2


# ═══════════════════════════════════════════════════════════════════════════
# lambda_handler() — API Gateway integration
# ═══════════════════════════════════════════════════════════════════════════

class TestLambdaHandler:

    def test_success_response(self, handler_module):
        mod, mock_anthropic, mock_tavily = handler_module

        mock_tavily.search.return_value = {
            "results": [{"title": "T", "url": "https://u", "content": "C"}]
        }

        responses = [
            make_claude_response(json.dumps(["Q1"])),
            make_claude_response(json.dumps(SAMPLE_FINDINGS[:1])),
            make_claude_response("[]"),
            make_claude_response(SAMPLE_REPORT),
        ]
        mock_anthropic.messages.create.side_effect = responses

        event = {"body": json.dumps({"topic": "quantum computing"})}

        result = mod.lambda_handler(event, None)

        assert result["statusCode"] == 200
        assert result["headers"]["Content-Type"] == "application/json"
        assert result["headers"]["Access-Control-Allow-Origin"] == "*"

        body = json.loads(result["body"])
        assert "report" in body
        assert "findings_count" in body
        assert "sources_count" in body
        assert "iterations" in body
        assert "log" in body

    def test_missing_topic_returns_400(self, handler_module):
        mod, _, _ = handler_module

        event = {"body": json.dumps({"topic": ""})}
        result = mod.lambda_handler(event, None)

        assert result["statusCode"] == 400
        body = json.loads(result["body"])
        assert body["error"] == "Topic is required"

    def test_missing_body_returns_400(self, handler_module):
        mod, _, _ = handler_module

        event = {}  # no body key
        result = mod.lambda_handler(event, None)

        assert result["statusCode"] == 400
        body = json.loads(result["body"])
        assert body["error"] == "Topic is required"

    def test_whitespace_only_topic_returns_400(self, handler_module):
        mod, _, _ = handler_module

        event = {"body": json.dumps({"topic": "   "})}
        result = mod.lambda_handler(event, None)

        assert result["statusCode"] == 400

    def test_internal_error_returns_500(self, handler_module):
        mod, mock_anthropic, _ = handler_module

        mock_anthropic.messages.create.side_effect = RuntimeError("boom")

        event = {"body": json.dumps({"topic": "quantum computing"})}
        result = mod.lambda_handler(event, None)

        assert result["statusCode"] == 500
        body = json.loads(result["body"])
        assert "error" in body
        assert "boom" in body["error"]

    def test_invalid_json_body_returns_500(self, handler_module):
        mod, _, _ = handler_module

        event = {"body": "not valid json"}
        result = mod.lambda_handler(event, None)

        assert result["statusCode"] == 500

    def test_cors_headers_on_error(self, handler_module):
        mod, _, _ = handler_module

        event = {"body": json.dumps({"topic": ""})}
        result = mod.lambda_handler(event, None)

        assert result["headers"]["Access-Control-Allow-Origin"] == "*"

    def test_cors_headers_on_500(self, handler_module):
        mod, mock_anthropic, _ = handler_module
        mock_anthropic.messages.create.side_effect = RuntimeError("fail")

        event = {"body": json.dumps({"topic": "test"})}
        result = mod.lambda_handler(event, None)

        assert result["statusCode"] == 500
        assert result["headers"]["Access-Control-Allow-Origin"] == "*"
