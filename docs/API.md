# Research Agent — API Reference

> AI-powered autonomous research agent. Generates comprehensive reports with citations from web sources.

---

## Architecture

```
Topic Input
    ↓
Planning Phase (Claude) → 4-6 Research Questions
    ↓
Research Loop (up to 3 iterations):
    Search (Tavily) → Extract Findings (Claude) → Analyze Gaps (Claude)
    ↓
Synthesis Phase (Claude) → Structured Markdown Report
```

---

## Python API

### ResearchAgent

**Module:** `src/agent/researcher.py`

| Method | Signature | Returns | Description |
|--------|-----------|---------|-------------|
| `research` | `(topic: str, on_status=None)` | `str` | Run full research pipeline, returns Markdown report |

**Internal Methods (called by `research`):**

| Method | Signature | Returns | Description |
|--------|-----------|---------|-------------|
| `_plan_research` | `(topic: str)` | `list[str]` | Generate 4-6 targeted research questions |
| `_extract_findings` | `(question: str, results: list[dict])` | `list[dict]` | Extract structured findings from search results |
| `_identify_gaps` | `(topic: str, findings: list[dict])` | `list[str]` | Identify knowledge gaps for next iteration |
| `_synthesize_report` | `(topic: str, findings: list[dict])` | `str` | Generate final Markdown report with citations |

**Example:**
```python
from src.agent.researcher import ResearchAgent

agent = ResearchAgent()
report = agent.research("Impact of AI on K-12 education")
print(report)  # Markdown with sections, citations, sources
```

**Status Callback:**
```python
def on_status(message: str):
    print(f"[Status] {message}")

report = agent.research("quantum computing", on_status=on_status)
# [Status] Planning research questions...
# [Status] Searching: What are the latest quantum computing breakthroughs?
# [Status] Extracting findings...
# [Status] Analyzing gaps...
# [Status] Synthesizing report...
```

---

### SearchTool

**Module:** `src/tools/search.py`

| Method | Signature | Returns | Description |
|--------|-----------|---------|-------------|
| `search` | `(query: str, max_results: int = 5)` | `list[dict]` | Search the web via Tavily API |

**Search Result Format:**
```json
[
  {
    "title": "Article Title",
    "url": "https://example.com/article",
    "content": "Relevant excerpt from the article..."
  }
]
```

---

## AWS Lambda Endpoint

**Handler:** `src/lambda/handler.py`

### POST /

Research a topic and return a structured report.

**Request:**
```json
{
  "topic": "Impact of AI on K-12 education"
}
```

**Response:**
```json
{
  "report": "# Impact of AI on K-12 Education\n\n## Introduction\n...",
  "findings_count": 44,
  "sources_count": 33,
  "iterations": 3,
  "log": [
    "Planning research questions...",
    "Iteration 1: Searching 6 questions...",
    "Iteration 2: Searching 3 gap questions...",
    "Synthesizing report..."
  ]
}
```

**Error Response:**
```json
{
  "error": "Missing required field: topic"
}
```

**Invoke via CLI:**
```bash
# Local Gradio
python app.py

# AWS Lambda (via helper script)
./research.sh "Impact of AI on K-12 education"

# Direct Lambda invocation
aws lambda invoke \
  --function-name research-agent-dev \
  --payload '{"topic": "quantum computing"}' \
  output.json
```

---

## Gradio Web UI

**Launch:** `python app.py` (default: `http://localhost:7860`)

| Input | Output | Notes |
|-------|--------|-------|
| Topic text field | Markdown report | Progress bar shows research phases |

```python
def research_topic(topic: str, progress=gr.Progress()) -> str:
    """
    Full research pipeline with progress tracking.

    Args:
        topic: Research topic string

    Returns:
        Markdown-formatted research report with citations
    """
```

---

## Configuration

| Variable | Default | Description |
|----------|---------|-------------|
| `ANTHROPIC_API_KEY` | — | Required. Claude API key |
| `TAVILY_API_KEY` | — | Required. Tavily search API key |

---

## Cost Estimate

| Component | Cost per Research |
|-----------|------------------|
| Claude (planning + extraction + synthesis) | ~$0.05-0.15 |
| Tavily (web searches) | ~$0.01-0.05 |
| Lambda (if deployed) | ~$0.001 |
| **Total** | **~$0.10-0.20** |

---

## Output Example

A typical research report includes:
- **Title and introduction** with topic overview
- **3-5 thematic sections** with detailed analysis
- **Inline citations** (`[1]`, `[2]`, etc.)
- **Source list** with URLs at the end
- ~44 findings from ~33 unique sources across 3 research iterations
