# Research Agent

An AI-powered research agent that autonomously researches any topic and produces comprehensive reports with citations.

## What It Does

1. **Plans** - Generates targeted research questions
2. **Searches** - Queries the web for information
3. **Analyzes** - Identifies gaps and searches again
4. **Synthesizes** - Produces a structured report with citations

## Example
```
Input: "AI agents in enterprise software"

Output: A comprehensive report covering:
- Definition and evolution
- Key players and platforms  
- Use cases and applications
- Technical integration requirements
- Governance and security
- ROI and investment considerations
- Future trends

With 15-20 cited sources
```

## Architecture
```
User Query
    │
    ▼
┌─────────────────┐
│  Plan Research  │ → Generate 4-6 targeted questions
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│  Research Loop  │ → Search → Extract → Analyze Gaps
└────────┬────────┘   (repeats up to 3 iterations)
         │
         ▼
┌─────────────────┐
│   Synthesize    │ → Combine findings into report
└────────┬────────┘
         │
         ▼
  Markdown Report
  (with citations)
```

## Tech Stack

- **LLM**: Claude (Anthropic) - Planning, extraction, synthesis
- **Search**: Tavily API - Web search optimized for AI agents
- **UI**: Gradio - Web interface
- **Framework**: Pure Python (no LangChain/LlamaIndex)

## Setup
```bash
# Clone
git clone https://github.com/woodstocksoftware/research-agent.git
cd research-agent

# Environment
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt

# API Keys
export ANTHROPIC_API_KEY="your-key"
export TAVILY_API_KEY="your-key"

# Run
python app.py
```

## Why No Framework?

This agent is built with pure Python to demonstrate understanding of:
- Agent loops and control flow
- Tool integration patterns
- Prompt engineering for structured outputs
- Multi-step reasoning

No magic. Just code you can read, understand, and modify.

## License

MIT

---

Built by [Jim Williams](https://linkedin.com/in/woodstocksoftware)
