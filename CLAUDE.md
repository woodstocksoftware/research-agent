# CLAUDE.md — Research Agent

> **Purpose:** Autonomous AI research agent that investigates topics and produces cited Markdown reports
> **Owner:** Jim Williams - Woodstock Software LLC
> **Repo:** woodstocksoftware/research-agent (public)

---

## Tech Stack

- Python 3.12 (Lambda runtime) / 3.14 (local venv)
- Anthropic Claude Sonnet (planning, extraction, gap analysis, synthesis)
- Tavily API (web search optimized for AI agents)
- Gradio (local web UI)
- AWS Lambda + SAM (production deployment)
- No frameworks (pure Python agent loop — no LangChain/LlamaIndex)

## Project Structure

```
research-agent/
├── app.py                         # Gradio UI entry point
├── research.sh                    # CLI helper for Lambda invocation
├── requirements.txt               # 4 dependencies
├── payload.json                   # Example Lambda payload
├── response.json                  # Example Lambda response
├── src/
│   ├── agent/
│   │   └── researcher.py          # Core ResearchAgent class (250 lines)
│   ├── tools/
│   │   └── search.py              # Tavily SearchTool wrapper (57 lines)
│   └── lambda/
│       └── handler.py             # AWS Lambda handler (290 lines)
├── infrastructure/
│   └── template.yaml              # SAM/CloudFormation
├── LICENSE                        # MIT
└── README.md
```

## How to Run

```bash
cd /Users/james/projects/research-agent
source venv/bin/activate
export ANTHROPIC_API_KEY="sk-ant-..."
export TAVILY_API_KEY="tvly-..."
python app.py
# Opens http://localhost:7860
```

## Environment Variables

| Variable | Required | Purpose |
|----------|----------|---------|
| `ANTHROPIC_API_KEY` | Yes | Claude API for all LLM calls |
| `TAVILY_API_KEY` | Yes | Tavily web search API |

## How It Works (4 Phases)

```
Topic
  ↓
Phase 1: PLAN — Claude generates 4-6 research questions
  ↓
Phase 2: RESEARCH (up to 3 iterations)
  ├── Tavily search (3 results per question)
  ├── Claude extracts structured findings {fact, source, url}
  └── Claude identifies coverage gaps → new questions or stop
  ↓
Phase 3: SYNTHESIZE — Claude writes Markdown report with inline citations
  ↓
Output: {report, findings_count, sources_count, iterations, log}
```

**Typical run**: 2-3 minutes, ~44 findings, ~33 sources, 3 iterations.

## Key Patterns

- **No framework**: Pure Python agent loop demonstrates the pattern without magic
- **JSON extraction**: Regex parses JSON from Claude's markdown code blocks with graceful fallback
- **Deduplication**: Removes duplicate findings by fact text before synthesis
- **Lazy search**: Tracks searched questions in a set, skips duplicates
- **Iterative deepening**: Gap analysis drives additional research rounds (max 3)
- **Citation format**: `[Title](url)` inline citations in final report

## AWS Deployment

```bash
sam build --template infrastructure/template.yaml
sam deploy --resolve-s3 --stack-name research-agent \
  --capabilities CAPABILITY_IAM CAPABILITY_NAMED_IAM \
  --parameter-overrides AnthropicApiKey=$ANTHROPIC_API_KEY TavilyApiKey=$TAVILY_API_KEY
```

Lambda: 512MB, 300s timeout. API Gateway: POST `/research`, x-api-key auth, 100 req/day.

**Note**: API Gateway has 29s timeout — use direct Lambda invocation for full research (2-3 min):
```bash
./research.sh "your topic"
```

## Cost

- Claude: ~$0.10-0.20 per research
- Tavily: Free tier (1,000 searches/month)
- AWS Lambda: ~$0.01 per research

## Testing

No formal test suite. Manual testing via Gradio UI or Lambda invocation.

## What's Missing

- [ ] Tests (pytest)
- [ ] CI workflow (.github/workflows/)
- [ ] pyproject.toml
