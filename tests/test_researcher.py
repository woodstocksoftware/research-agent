"""
Tests for src/agent/researcher.ResearchAgent.

All Anthropic and Tavily calls are mocked -- no real API keys or network.
"""

import json
import pytest
from unittest.mock import MagicMock, patch, call

from tests.conftest import (
    make_claude_response,
    SAMPLE_QUESTIONS,
    SAMPLE_SEARCH_RESULTS,
    SAMPLE_FINDINGS,
    SAMPLE_GAPS,
    SAMPLE_REPORT,
)


# ---------------------------------------------------------------------------
# Helper to build a ResearchAgent with mocked dependencies
# ---------------------------------------------------------------------------

def _make_agent(mock_anthropic_client, mock_search_tool):
    """Construct a ResearchAgent with injected mocks."""
    with patch("src.agent.researcher.Anthropic", return_value=mock_anthropic_client), \
         patch("src.agent.researcher.SearchTool", return_value=mock_search_tool):
        from src.agent.researcher import ResearchAgent
        agent = ResearchAgent()
    return agent


# ═══════════════════════════════════════════════════════════════════════════
# _plan_research
# ═══════════════════════════════════════════════════════════════════════════

class TestPlanResearch:

    def test_parses_plain_json_array(self, mock_anthropic_client, mock_search_tool):
        """Claude returns a plain JSON array (no code block)."""
        mock_anthropic_client.messages.create.return_value = make_claude_response(
            json.dumps(SAMPLE_QUESTIONS)
        )
        agent = _make_agent(mock_anthropic_client, mock_search_tool)

        questions = agent._plan_research("quantum computing")

        assert questions == SAMPLE_QUESTIONS
        mock_anthropic_client.messages.create.assert_called_once()

    def test_parses_json_in_markdown_code_block(self, mock_anthropic_client, mock_search_tool):
        """Claude wraps the JSON in ```json ... ```."""
        text = '```json\n' + json.dumps(SAMPLE_QUESTIONS) + '\n```'
        mock_anthropic_client.messages.create.return_value = make_claude_response(text)
        agent = _make_agent(mock_anthropic_client, mock_search_tool)

        questions = agent._plan_research("quantum computing")
        assert questions == SAMPLE_QUESTIONS

    def test_parses_json_in_bare_code_block(self, mock_anthropic_client, mock_search_tool):
        """Claude wraps the JSON in ``` ... ``` without language tag."""
        text = '```\n' + json.dumps(SAMPLE_QUESTIONS) + '\n```'
        mock_anthropic_client.messages.create.return_value = make_claude_response(text)
        agent = _make_agent(mock_anthropic_client, mock_search_tool)

        questions = agent._plan_research("quantum computing")
        assert questions == SAMPLE_QUESTIONS

    def test_fallback_on_invalid_json(self, mock_anthropic_client, mock_search_tool):
        """If Claude returns non-JSON, fall back to generic questions."""
        mock_anthropic_client.messages.create.return_value = make_claude_response(
            "Here are some great questions to research..."
        )
        agent = _make_agent(mock_anthropic_client, mock_search_tool)

        questions = agent._plan_research("quantum computing")

        assert len(questions) == 4
        assert any("quantum computing" in q for q in questions)


# ═══════════════════════════════════════════════════════════════════════════
# _extract_findings
# ═══════════════════════════════════════════════════════════════════════════

class TestExtractFindings:

    def test_extracts_findings_from_plain_json(self, mock_anthropic_client, mock_search_tool):
        mock_anthropic_client.messages.create.return_value = make_claude_response(
            json.dumps(SAMPLE_FINDINGS)
        )
        agent = _make_agent(mock_anthropic_client, mock_search_tool)

        findings = agent._extract_findings("What is quantum computing?", SAMPLE_SEARCH_RESULTS)

        assert len(findings) == 3
        assert findings[0]["fact"] == SAMPLE_FINDINGS[0]["fact"]
        assert findings[0]["source"] == SAMPLE_FINDINGS[0]["source"]
        assert findings[0]["url"] == SAMPLE_FINDINGS[0]["url"]

    def test_extracts_findings_from_code_block(self, mock_anthropic_client, mock_search_tool):
        text = '```json\n' + json.dumps(SAMPLE_FINDINGS) + '\n```'
        mock_anthropic_client.messages.create.return_value = make_claude_response(text)
        agent = _make_agent(mock_anthropic_client, mock_search_tool)

        findings = agent._extract_findings("question", SAMPLE_SEARCH_RESULTS)
        assert len(findings) == 3

    def test_returns_empty_on_invalid_json(self, mock_anthropic_client, mock_search_tool):
        mock_anthropic_client.messages.create.return_value = make_claude_response(
            "I couldn't parse the results properly."
        )
        agent = _make_agent(mock_anthropic_client, mock_search_tool)

        findings = agent._extract_findings("question", SAMPLE_SEARCH_RESULTS)
        assert findings == []

    def test_context_includes_all_results(self, mock_anthropic_client, mock_search_tool):
        """Verify the prompt sent to Claude includes all search result content."""
        mock_anthropic_client.messages.create.return_value = make_claude_response("[]")
        agent = _make_agent(mock_anthropic_client, mock_search_tool)

        agent._extract_findings("question", SAMPLE_SEARCH_RESULTS)

        call_args = mock_anthropic_client.messages.create.call_args
        prompt = call_args.kwargs["messages"][0]["content"]
        for r in SAMPLE_SEARCH_RESULTS:
            assert r["title"] in prompt
            assert r["url"] in prompt


# ═══════════════════════════════════════════════════════════════════════════
# _identify_gaps
# ═══════════════════════════════════════════════════════════════════════════

class TestIdentifyGaps:

    def test_returns_gap_queries(self, mock_anthropic_client, mock_search_tool):
        mock_anthropic_client.messages.create.return_value = make_claude_response(
            json.dumps(SAMPLE_GAPS)
        )
        agent = _make_agent(mock_anthropic_client, mock_search_tool)

        gaps = agent._identify_gaps("quantum computing", SAMPLE_FINDINGS)
        assert gaps == SAMPLE_GAPS

    def test_returns_empty_when_no_gaps(self, mock_anthropic_client, mock_search_tool):
        mock_anthropic_client.messages.create.return_value = make_claude_response("[]")
        agent = _make_agent(mock_anthropic_client, mock_search_tool)

        gaps = agent._identify_gaps("quantum computing", SAMPLE_FINDINGS)
        assert gaps == []

    def test_returns_empty_on_invalid_json(self, mock_anthropic_client, mock_search_tool):
        mock_anthropic_client.messages.create.return_value = make_claude_response(
            "The research looks comprehensive."
        )
        agent = _make_agent(mock_anthropic_client, mock_search_tool)

        gaps = agent._identify_gaps("quantum computing", SAMPLE_FINDINGS)
        assert gaps == []

    def test_handles_code_block_wrapped_gaps(self, mock_anthropic_client, mock_search_tool):
        text = '```json\n' + json.dumps(SAMPLE_GAPS) + '\n```'
        mock_anthropic_client.messages.create.return_value = make_claude_response(text)
        agent = _make_agent(mock_anthropic_client, mock_search_tool)

        gaps = agent._identify_gaps("quantum computing", SAMPLE_FINDINGS)
        assert gaps == SAMPLE_GAPS

    def test_limits_findings_to_20(self, mock_anthropic_client, mock_search_tool):
        """Only the first 20 findings should be included in the gap analysis prompt."""
        mock_anthropic_client.messages.create.return_value = make_claude_response("[]")
        agent = _make_agent(mock_anthropic_client, mock_search_tool)

        many_findings = [{"fact": f"Fact {i}", "source": "S", "url": "http://x"} for i in range(30)]
        agent._identify_gaps("topic", many_findings)

        prompt = mock_anthropic_client.messages.create.call_args.kwargs["messages"][0]["content"]
        # Facts 0-19 should be present, fact 20+ should not
        assert "Fact 0" in prompt
        assert "Fact 19" in prompt
        assert "Fact 20" not in prompt


# ═══════════════════════════════════════════════════════════════════════════
# _synthesize_report
# ═══════════════════════════════════════════════════════════════════════════

class TestSynthesizeReport:

    def test_returns_report_text(self, mock_anthropic_client, mock_search_tool):
        mock_anthropic_client.messages.create.return_value = make_claude_response(SAMPLE_REPORT)
        agent = _make_agent(mock_anthropic_client, mock_search_tool)

        report = agent._synthesize_report("quantum computing", SAMPLE_FINDINGS)
        assert report == SAMPLE_REPORT

    def test_deduplicates_findings(self, mock_anthropic_client, mock_search_tool):
        """Duplicate facts should be removed before synthesis."""
        mock_anthropic_client.messages.create.return_value = make_claude_response("# Report")
        agent = _make_agent(mock_anthropic_client, mock_search_tool)

        duplicated = SAMPLE_FINDINGS + [SAMPLE_FINDINGS[0]]  # first finding repeated
        agent._synthesize_report("topic", duplicated)

        prompt = mock_anthropic_client.messages.create.call_args.kwargs["messages"][0]["content"]
        # The duplicated fact should appear only once in the prompt
        fact = SAMPLE_FINDINGS[0]["fact"]
        assert prompt.count(fact) == 1

    def test_uses_max_tokens_4096(self, mock_anthropic_client, mock_search_tool):
        mock_anthropic_client.messages.create.return_value = make_claude_response("# Report")
        agent = _make_agent(mock_anthropic_client, mock_search_tool)

        agent._synthesize_report("topic", SAMPLE_FINDINGS)

        call_args = mock_anthropic_client.messages.create.call_args
        assert call_args.kwargs["max_tokens"] == 4096


# ═══════════════════════════════════════════════════════════════════════════
# research (end-to-end flow)
# ═══════════════════════════════════════════════════════════════════════════

class TestResearchFlow:

    def test_single_iteration_no_gaps(self, mock_anthropic_client, mock_search_tool):
        """When gap analysis returns [], the loop stops after one iteration."""
        responses = [
            # _plan_research
            make_claude_response(json.dumps(SAMPLE_QUESTIONS)),
            # _extract_findings x4 (one per question)
            make_claude_response(json.dumps(SAMPLE_FINDINGS[:1])),
            make_claude_response(json.dumps(SAMPLE_FINDINGS[1:2])),
            make_claude_response(json.dumps(SAMPLE_FINDINGS[2:])),
            make_claude_response(json.dumps([])),
            # _identify_gaps (returns empty → stop)
            make_claude_response("[]"),
            # _synthesize_report
            make_claude_response(SAMPLE_REPORT),
        ]
        mock_anthropic_client.messages.create.side_effect = responses
        agent = _make_agent(mock_anthropic_client, mock_search_tool)

        report = agent.research("quantum computing")

        assert "Quantum computing" in report
        # Plan (1) + Extract (4) + Gaps (1) + Synthesize (1) = 7 calls
        assert mock_anthropic_client.messages.create.call_count == 7

    def test_two_iterations_with_gaps(self, mock_anthropic_client, mock_search_tool):
        """Gap analysis returns new questions, triggering a second iteration."""
        responses = [
            # _plan_research → 4 questions
            make_claude_response(json.dumps(SAMPLE_QUESTIONS)),
            # _extract_findings x4 (iteration 1)
            make_claude_response(json.dumps(SAMPLE_FINDINGS[:1])),
            make_claude_response(json.dumps(SAMPLE_FINDINGS[1:2])),
            make_claude_response(json.dumps(SAMPLE_FINDINGS[2:])),
            make_claude_response(json.dumps([])),
            # _identify_gaps → 2 new questions
            make_claude_response(json.dumps(SAMPLE_GAPS)),
            # _extract_findings x2 (iteration 2)
            make_claude_response(json.dumps(SAMPLE_FINDINGS[:1])),
            make_claude_response(json.dumps(SAMPLE_FINDINGS[1:2])),
            # _identify_gaps → no more gaps
            make_claude_response("[]"),
            # _synthesize_report
            make_claude_response(SAMPLE_REPORT),
        ]
        mock_anthropic_client.messages.create.side_effect = responses
        agent = _make_agent(mock_anthropic_client, mock_search_tool)

        report = agent.research("quantum computing")

        assert report == SAMPLE_REPORT
        # Plan(1) + Extract(4) + Gaps(1) + Extract(2) + Gaps(1) + Synth(1) = 10
        assert mock_anthropic_client.messages.create.call_count == 10

    def test_skips_already_searched_questions(self, mock_anthropic_client, mock_search_tool):
        """Questions that have already been searched are not searched again."""
        # Gap analysis returns one question that was already in the initial set
        gaps_with_duplicate = [SAMPLE_QUESTIONS[0], "New question about quantum"]

        responses = [
            make_claude_response(json.dumps(SAMPLE_QUESTIONS)),
            # Extract x4 (iteration 1)
            make_claude_response(json.dumps(SAMPLE_FINDINGS[:1])),
            make_claude_response(json.dumps(SAMPLE_FINDINGS[1:2])),
            make_claude_response(json.dumps(SAMPLE_FINDINGS[2:])),
            make_claude_response(json.dumps([])),
            # Gaps → includes a duplicate question
            make_claude_response(json.dumps(gaps_with_duplicate)),
            # Extract x1 (only the new question, duplicate skipped)
            make_claude_response(json.dumps(SAMPLE_FINDINGS[:1])),
            # Gaps → done
            make_claude_response("[]"),
            # Synthesize
            make_claude_response(SAMPLE_REPORT),
        ]
        mock_anthropic_client.messages.create.side_effect = responses
        agent = _make_agent(mock_anthropic_client, mock_search_tool)

        agent.research("quantum computing")

        # Search should be called 5 times (4 original + 1 new), not 6
        assert mock_search_tool.search.call_count == 5

    def test_max_iterations_respected(self, mock_anthropic_client, mock_search_tool):
        """The loop runs at most max_iterations times even if gaps keep appearing."""
        # Return gaps every time so the loop would run forever without the cap
        gap_response = make_claude_response(json.dumps(["New gap question"]))

        responses = [
            # Plan
            make_claude_response(json.dumps(["Q1"])),
        ]
        # 3 iterations: each has extract(1) then gaps(1), except last has no gaps check
        for i in range(3):
            # extract for the question
            responses.append(make_claude_response(json.dumps(SAMPLE_FINDINGS[:1])))
            if i < 2:  # gap analysis only before last iteration
                responses.append(make_claude_response(json.dumps([f"Gap question {i + 1}"])))
        # Synthesize
        responses.append(make_claude_response(SAMPLE_REPORT))

        mock_anthropic_client.messages.create.side_effect = responses
        agent = _make_agent(mock_anthropic_client, mock_search_tool)
        agent.max_iterations = 3

        report = agent.research("topic")

        assert report == SAMPLE_REPORT

    def test_empty_search_results_skipped(self, mock_anthropic_client, mock_search_tool):
        """If search returns [], _extract_findings should not be called for that question."""
        mock_search_tool.search.return_value = []

        responses = [
            # Plan
            make_claude_response(json.dumps(["Q1", "Q2"])),
            # No extract calls because search returns empty
            # Gaps
            make_claude_response("[]"),
            # Synthesize (with empty findings)
            make_claude_response("# Empty report"),
        ]
        mock_anthropic_client.messages.create.side_effect = responses
        agent = _make_agent(mock_anthropic_client, mock_search_tool)

        report = agent.research("topic")

        # Plan(1) + Gaps(1) + Synth(1) = 3 (no extract calls)
        assert mock_anthropic_client.messages.create.call_count == 3
        assert report == "# Empty report"

    def test_status_callback_called(self, mock_anthropic_client, mock_search_tool):
        """The on_status callback receives progress messages."""
        responses = [
            make_claude_response(json.dumps(["Q1"])),
            make_claude_response(json.dumps(SAMPLE_FINDINGS[:1])),
            make_claude_response("[]"),
            make_claude_response(SAMPLE_REPORT),
        ]
        mock_anthropic_client.messages.create.side_effect = responses
        agent = _make_agent(mock_anthropic_client, mock_search_tool)

        status_msgs = []
        agent.research("topic", on_status=lambda msg: status_msgs.append(msg))

        assert len(status_msgs) > 0
        # Should contain planning, iteration, and synthesis messages
        assert any("Planning" in m for m in status_msgs)
        assert any("Synthesizing" in m for m in status_msgs)

    def test_no_status_callback_is_fine(self, mock_anthropic_client, mock_search_tool):
        """research() works without an on_status callback."""
        responses = [
            make_claude_response(json.dumps(["Q1"])),
            make_claude_response(json.dumps(SAMPLE_FINDINGS[:1])),
            make_claude_response("[]"),
            make_claude_response(SAMPLE_REPORT),
        ]
        mock_anthropic_client.messages.create.side_effect = responses
        agent = _make_agent(mock_anthropic_client, mock_search_tool)

        report = agent.research("topic")  # no on_status
        assert report == SAMPLE_REPORT
