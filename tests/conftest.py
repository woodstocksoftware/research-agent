"""
Shared fixtures for research-agent tests.

All external API calls (Anthropic Claude, Tavily) are mocked here so tests
never require API keys or make real network requests.
"""

import json
import pytest
from unittest.mock import MagicMock, patch


# ---------------------------------------------------------------------------
# Helpers to build Anthropic-style mock responses
# ---------------------------------------------------------------------------

def make_claude_response(text: str):
    """Build a mock Anthropic Messages response with the given text."""
    content_block = MagicMock()
    content_block.text = text
    response = MagicMock()
    response.content = [content_block]
    return response


# ---------------------------------------------------------------------------
# Sample data used across multiple test modules
# ---------------------------------------------------------------------------

SAMPLE_QUESTIONS = [
    "What is quantum computing?",
    "Who are the key players in quantum computing?",
    "What are the current challenges in quantum computing?",
    "What are the future trends in quantum computing?",
]

SAMPLE_SEARCH_RESULTS = [
    {
        "title": "Quantum Computing Overview",
        "url": "https://example.com/quantum",
        "content": "Quantum computing uses qubits to perform calculations exponentially faster.",
    },
    {
        "title": "IBM Quantum",
        "url": "https://example.com/ibm-quantum",
        "content": "IBM has deployed a 1000-qubit processor for enterprise use.",
    },
    {
        "title": "Quantum Challenges",
        "url": "https://example.com/challenges",
        "content": "Error correction remains the biggest hurdle for practical quantum computing.",
    },
]

SAMPLE_FINDINGS = [
    {
        "fact": "Quantum computing uses qubits to perform calculations exponentially faster than classical computers.",
        "source": "Quantum Computing Overview",
        "url": "https://example.com/quantum",
    },
    {
        "fact": "IBM has deployed a 1000-qubit processor for enterprise use.",
        "source": "IBM Quantum",
        "url": "https://example.com/ibm-quantum",
    },
    {
        "fact": "Error correction remains the biggest hurdle for practical quantum computing.",
        "source": "Quantum Challenges",
        "url": "https://example.com/challenges",
    },
]

SAMPLE_GAPS = [
    "What quantum computing programming languages exist?",
    "How does quantum computing affect cryptography?",
]

SAMPLE_REPORT = """## Executive Summary

Quantum computing is an emerging technology that leverages quantum mechanics to solve problems
beyond the reach of classical computers.

## Current State

Quantum computing uses qubits to perform calculations exponentially faster than classical
computers [Quantum Computing Overview](https://example.com/quantum). IBM has deployed a
1000-qubit processor for enterprise use [IBM Quantum](https://example.com/ibm-quantum).

## Challenges

Error correction remains the biggest hurdle for practical quantum computing
[Quantum Challenges](https://example.com/challenges).

## Key Takeaways

- Quantum computing is advancing rapidly
- IBM leads in enterprise quantum hardware
- Error correction is the primary technical challenge

## Sources

- [Quantum Computing Overview](https://example.com/quantum)
- [IBM Quantum](https://example.com/ibm-quantum)
- [Quantum Challenges](https://example.com/challenges)
"""


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture
def mock_anthropic_client():
    """Return a MagicMock Anthropic client with messages.create patched."""
    client = MagicMock()
    client.messages = MagicMock()
    client.messages.create = MagicMock()
    return client


@pytest.fixture
def mock_tavily_client():
    """Return a MagicMock TavilyClient."""
    client = MagicMock()
    client.search = MagicMock(return_value={
        "results": [
            {
                "title": r["title"],
                "url": r["url"],
                "content": r["content"],
            }
            for r in SAMPLE_SEARCH_RESULTS
        ]
    })
    return client


@pytest.fixture
def mock_search_tool():
    """Return a MagicMock SearchTool that returns sample results."""
    tool = MagicMock()
    tool.search = MagicMock(return_value=SAMPLE_SEARCH_RESULTS)
    return tool
