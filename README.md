# Research Agent

An AI-powered research agent that autonomously researches any topic and produces comprehensive reports with citations.

![Python](https://img.shields.io/badge/Python-3.12-blue)
![AWS](https://img.shields.io/badge/AWS-Lambda-orange)
![Claude](https://img.shields.io/badge/LLM-Claude-blueviolet)

## What It Does

1. **Plans** - Generates targeted research questions
2. **Searches** - Queries the web for information (Tavily API)
3. **Analyzes** - Identifies gaps and searches again
4. **Synthesizes** - Produces a structured report with citations

## Example Output
```
Input: "quantum computing applications in finance"

Output: 
- 44 findings extracted
- 33 unique sources cited
- 3 research iterations
- Comprehensive report with executive summary, 
  detailed sections, and key takeaways
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

| Component | Choice | Why |
|-----------|--------|-----|
| **LLM** | Claude (Anthropic) | Planning, extraction, synthesis |
| **Search** | Tavily API | Web search optimized for AI agents |
| **Compute** | AWS Lambda | Serverless, pay-per-use |
| **UI** | Gradio | Local web interface |
| **Framework** | Pure Python | No LangChain/LlamaIndex dependencies |

## Quick Start

### Local Development
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

# Run with Gradio UI
python app.py
# Open http://localhost:7860
```

### AWS Deployment
```bash
# Build
sam build --template infrastructure/template.yaml

# Deploy
sam deploy --resolve-s3 \
  --stack-name research-agent \
  --capabilities CAPABILITY_IAM CAPABILITY_NAMED_IAM \
  --parameter-overrides \
    AnthropicApiKey=$ANTHROPIC_API_KEY \
    TavilyApiKey=$TAVILY_API_KEY
```

### Usage

**Local (Gradio UI):**
```bash
python app.py
# Open http://localhost:7860
```

**AWS (CLI helper):**
```bash
./research.sh "your research topic"
```

**AWS (Direct Lambda):**
```bash
aws lambda invoke \
  --function-name research-agent-dev \
  --cli-read-timeout 300 \
  --cli-binary-format raw-in-base64-out \
  --payload file://payload.json \
  response.json
```

> **Note:** Research takes 2-3 minutes. API Gateway has a 29-second timeout, so use direct Lambda invocation or the CLI helper for best results.

## Project Structure
```
research-agent/
├── app.py                      # Gradio UI
├── research.sh                 # CLI helper for AWS
├── infrastructure/
│   └── template.yaml           # SAM/CloudFormation template
├── src/
│   ├── agent/
│   │   └── researcher.py       # Core agent logic
│   ├── tools/
│   │   └── search.py           # Tavily search wrapper
│   └── lambda/
│       └── handler.py          # AWS Lambda handler
└── requirements.txt
```

## How It Works

### 1. Planning Phase
The agent generates 4-6 specific research questions covering different aspects of the topic (definition, current state, key players, challenges, trends).

### 2. Research Loop (up to 3 iterations)
For each question:
- Search the web using Tavily
- Extract key findings with source attribution
- Analyze gaps in coverage
- Generate new queries if gaps exist

### 3. Synthesis Phase
Combines all findings into a structured report:
- Executive summary
- Organized sections with headers
- Inline citations with links
- Key takeaways
- Source list

## Why No Framework?

This agent is built with pure Python to demonstrate understanding of:
- Agent loops and control flow
- Tool integration patterns
- Prompt engineering for structured outputs
- Multi-step reasoning

No magic. Just code you can read, understand, and modify.

## Cost Estimate

| Service | Cost |
|---------|------|
| **Claude API** | ~$0.10-0.20 per research |
| **Tavily API** | Free tier: 1000 searches/month |
| **AWS Lambda** | ~$0.01 per research |

## License

MIT

---

Built by [Jim Williams](https://linkedin.com/in/woodstocksoftware) | [GitHub](https://github.com/woodstocksoftware)
