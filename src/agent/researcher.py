"""
Research Agent: Plans, searches, and synthesizes research on any topic.

The agent uses a loop:
1. Plan research questions
2. Search for each question
3. Analyze gaps
4. Search more if needed
5. Synthesize final report
"""

import json
from anthropic import Anthropic
from ..tools.search import SearchTool


class ResearchAgent:
    def __init__(self):
        self.client = Anthropic()
        self.search_tool = SearchTool()
        self.model = "claude-sonnet-4-20250514"
        self.max_iterations = 3
        
    def research(self, topic: str, on_status=None) -> str:
        """
        Research a topic and return a comprehensive report.
        
        Args:
            topic: The research topic
            on_status: Optional callback for status updates (for UI)
        
        Returns:
            Markdown-formatted research report
        """
        def status(msg):
            if on_status:
                on_status(msg)
            print(msg)
        
        # Phase 1: Planning
        status("📋 Planning research questions...")
        questions = self._plan_research(topic)
        status(f"   Generated {len(questions)} research questions")
        
        # Phase 2: Research Loop
        all_findings = []
        searched_queries = set()
        
        for iteration in range(self.max_iterations):
            status(f"\n🔍 Research iteration {iteration + 1}/{self.max_iterations}")
            
            # Search for each question we haven't searched yet
            new_findings = []
            for question in questions:
                if question in searched_queries:
                    continue
                    
                status(f"   Searching: {question[:50]}...")
                searched_queries.add(question)
                
                results = self.search_tool.search(question, max_results=3)
                
                if results:
                    findings = self._extract_findings(question, results)
                    new_findings.extend(findings)
                    status(f"   Found {len(findings)} relevant findings")
            
            all_findings.extend(new_findings)
            
            # Phase 3: Gap Analysis
            if iteration < self.max_iterations - 1:
                status("\n🔎 Analyzing gaps...")
                gaps = self._identify_gaps(topic, all_findings)
                
                if gaps:
                    status(f"   Found {len(gaps)} gaps, generating new queries...")
                    questions = gaps
                else:
                    status("   No significant gaps found")
                    break
        
        # Phase 4: Synthesis
        status("\n📝 Synthesizing final report...")
        report = self._synthesize_report(topic, all_findings)
        status("✅ Research complete!")
        
        return report
    
    def _plan_research(self, topic: str) -> list[str]:
        """Generate research questions for the topic."""
        response = self.client.messages.create(
            model=self.model,
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
            # Extract JSON from response
            text = response.content[0].text
            # Handle potential markdown code blocks
            if "```" in text:
                text = text.split("```")[1]
                if text.startswith("json"):
                    text = text[4:]
            return json.loads(text.strip())
        except:
            # Fallback: simple questions
            return [
                f"What is {topic}?",
                f"Current state of {topic} in 2024",
                f"Key companies and players in {topic}",
                f"Challenges and limitations of {topic}",
            ]
    
    def _extract_findings(self, question: str, results: list[dict]) -> list[dict]:
        """Extract key findings from search results."""
        # Combine results into context
        context = "\n\n".join([
            f"Source: {r['title']}\nURL: {r['url']}\nContent: {r['content']}"
            for r in results
        ])
        
        response = self.client.messages.create(
            model=self.model,
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

Only include factual, relevant information. Return ONLY valid JSON, no other text.

Example:
[{{"fact": "AI agents market grew 40% in 2024", "source": "TechCrunch", "url": "https://..."}}]"""
            }]
        )
        
        try:
            text = response.content[0].text
            if "```" in text:
                text = text.split("```")[1]
                if text.startswith("json"):
                    text = text[4:]
            return json.loads(text.strip())
        except:
            return []
    
    def _identify_gaps(self, topic: str, findings: list[dict]) -> list[str]:
        """Identify gaps in current research."""
        findings_summary = "\n".join([f"- {f['fact']}" for f in findings[:20]])
        
        response = self.client.messages.create(
            model=self.model,
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
        except:
            return []
    
    def _synthesize_report(self, topic: str, findings: list[dict]) -> str:
        """Synthesize findings into a final report."""
        # Deduplicate and format findings
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
        
        response = self.client.messages.create(
            model=self.model,
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


# Quick test
if __name__ == "__main__":
    agent = ResearchAgent()
    report = agent.research("AI agents in enterprise software")
    print("\n" + "="*60 + "\n")
    print(report)
