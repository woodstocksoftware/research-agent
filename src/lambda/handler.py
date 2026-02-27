"""
Research Agent Lambda Handler

Handles API Gateway requests for research queries.
"""

import json
import os

from anthropic import Anthropic
from tavily import TavilyClient

# Initialize clients
anthropic_client = Anthropic(api_key=os.environ['ANTHROPIC_API_KEY'])
tavily_client = TavilyClient(api_key=os.environ['TAVILY_API_KEY'])

MODEL = "claude-sonnet-4-20250514"
MAX_ITERATIONS = 3


def search(query: str, max_results: int = 3) -> list[dict]:
    """Search the web using Tavily."""
    try:
        response = tavily_client.search(
            query=query,
            max_results=max_results,
            include_answer=False,
            include_raw_content=False,
        )
        return [
            {
                "title": item.get("title", ""),
                "url": item.get("url", ""),
                "content": item.get("content", ""),
            }
            for item in response.get("results", [])
        ]
    except Exception as e:
        print(f"Search error: {e}")
        return []


def plan_research(topic: str) -> list[str]:
    """Generate research questions for the topic."""
    response = anthropic_client.messages.create(
        model=MODEL,
        max_tokens=1024,
        messages=[{
            "role": "user",
            "content": f"""Generate 4-6 specific research questions to thoroughly understand this topic:

Topic: {topic}

Requirements:
- Questions should cover different aspects (definition, current state, key players, challenges, future trends)
- Questions should be specific enough to search effectively
- Return ONLY a JSON array of strings, no other text

Example format:
["What is X?", "Who are the main companies in X?", "What are the challenges of X?"]"""
        }]
    )

    try:
        text = response.content[0].text
        if "```" in text:
            text = text.split("```")[1]
            if text.startswith("json"):
                text = text[4:]
        return json.loads(text.strip())
    except Exception:
        return [
            f"What is {topic}?",
            f"Current state of {topic}",
            f"Key companies and players in {topic}",
            f"Challenges and limitations of {topic}",
        ]


def extract_findings(question: str, results: list[dict]) -> list[dict]:
    """Extract key findings from search results."""
    context = "\n\n".join([
        f"Source: {r['title']}\nURL: {r['url']}\nContent: {r['content']}"
        for r in results
    ])

    response = anthropic_client.messages.create(
        model=MODEL,
        max_tokens=1024,
        messages=[{
            "role": "user",
            "content": f"""Extract key findings from these search results that answer the question.

Question: {question}

Search Results:
{context}

Return a JSON array of findings. Each finding should have:
- "fact": The key information (1-2 sentences)
- "source": The source title
- "url": The source URL

Only include factual, relevant information. Return ONLY valid JSON, no other text."""
        }]
    )

    try:
        text = response.content[0].text
        if "```" in text:
            text = text.split("```")[1]
            if text.startswith("json"):
                text = text[4:]
        return json.loads(text.strip())
    except Exception:
        return []


def identify_gaps(topic: str, findings: list[dict]) -> list[str]:
    """Identify gaps in current research."""
    findings_summary = "\n".join([f"- {f['fact']}" for f in findings[:20]])

    response = anthropic_client.messages.create(
        model=MODEL,
        max_tokens=512,
        messages=[{
            "role": "user",
            "content": f"""Given this research topic and current findings, identify any important gaps.

Topic: {topic}

Current Findings:
{findings_summary}

Are there important aspects of this topic that haven't been covered?
If yes, return a JSON array of 2-3 new search queries to fill the gaps.
If the research is comprehensive, return an empty array [].

Return ONLY a JSON array, no other text."""
        }]
    )

    try:
        text = response.content[0].text
        if "```" in text:
            text = text.split("```")[1]
            if text.startswith("json"):
                text = text[4:]
        return json.loads(text.strip())
    except Exception:
        return []


def synthesize_report(topic: str, findings: list[dict]) -> str:
    """Synthesize findings into a final report."""
    seen = set()
    unique_findings = []
    for f in findings:
        if f['fact'] not in seen:
            seen.add(f['fact'])
            unique_findings.append(f)

    findings_text = "\n".join([
        f"- {f['fact']} [Source: {f['source']}]({f['url']})"
        for f in unique_findings
    ])

    response = anthropic_client.messages.create(
        model=MODEL,
        max_tokens=4096,
        messages=[{
            "role": "user",
            "content": f"""Write a comprehensive research report on this topic using the provided findings.

Topic: {topic}

Findings:
{findings_text}

Requirements:
1. Write in clear, professional prose (not bullet points for the main content)
2. Organize into logical sections with ## headers
3. Include a brief executive summary at the start
4. Cite sources inline using [Source Name](url) format
5. End with a "Key Takeaways" section (3-5 bullet points)
6. End with a "Sources" section listing all unique sources

Write the report in Markdown format."""
        }]
    )

    return response.content[0].text


def research(topic: str) -> dict:
    """Run the full research pipeline."""
    log = []

    # Phase 1: Planning
    log.append("Planning research questions...")
    questions = plan_research(topic)
    log.append(f"Generated {len(questions)} questions")

    # Phase 2: Research Loop
    all_findings = []
    searched_queries = set()

    for iteration in range(MAX_ITERATIONS):
        log.append(f"Research iteration {iteration + 1}/{MAX_ITERATIONS}")

        new_findings = []
        for question in questions:
            if question in searched_queries:
                continue

            searched_queries.add(question)
            results = search(question, max_results=3)

            if results:
                findings = extract_findings(question, results)
                new_findings.extend(findings)
                log.append(f"  Found {len(findings)} findings for: {question[:50]}...")

        all_findings.extend(new_findings)

        # Gap Analysis
        if iteration < MAX_ITERATIONS - 1:
            gaps = identify_gaps(topic, all_findings)
            if gaps:
                log.append(f"Found {len(gaps)} gaps, continuing research...")
                questions = gaps
            else:
                log.append("Research complete, no gaps found")
                break

    # Phase 3: Synthesis
    log.append("Synthesizing final report...")
    report = synthesize_report(topic, all_findings)

    return {
        "report": report,
        "findings_count": len(all_findings),
        "sources_count": len(set(f.get('url', '') for f in all_findings)),
        "iterations": iteration + 1,
        "log": log
    }


def lambda_handler(event, context):
    """Main Lambda handler."""
    try:
        # Parse request
        body = json.loads(event.get('body', '{}'))
        topic = body.get('topic', '').strip()

        if not topic:
            return {
                'statusCode': 400,
                'headers': {
                    'Content-Type': 'application/json',
                    'Access-Control-Allow-Origin': '*'
                },
                'body': json.dumps({'error': 'Topic is required'})
            }

        print(f"Researching: {topic}")

        # Run research
        result = research(topic)

        return {
            'statusCode': 200,
            'headers': {
                'Content-Type': 'application/json',
                'Access-Control-Allow-Origin': '*'
            },
            'body': json.dumps(result)
        }

    except Exception as e:
        print(f"Error: {str(e)}")
        return {
            'statusCode': 500,
            'headers': {
                'Content-Type': 'application/json',
                'Access-Control-Allow-Origin': '*'
            },
            'body': json.dumps({'error': str(e)})
        }
