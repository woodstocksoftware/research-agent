"""
Search tool using Tavily API.
Tavily is designed for AI agents - returns clean, structured content.
"""

import os

from tavily import TavilyClient


class SearchTool:
    def __init__(self):
        api_key = os.environ.get("TAVILY_API_KEY")
        if not api_key:
            raise ValueError("TAVILY_API_KEY environment variable not set")
        self.client = TavilyClient(api_key=api_key)

    def search(self, query: str, max_results: int = 5) -> list[dict]:
        """
        Search the web for a query.

        Returns list of results with:
        - title: Page title
        - url: Source URL
        - content: Extracted text content
        """
        try:
            response = self.client.search(
                query=query,
                max_results=max_results,
                include_answer=False,
                include_raw_content=False,
            )

            results = []
            for item in response.get("results", []):
                results.append({
                    "title": item.get("title", ""),
                    "url": item.get("url", ""),
                    "content": item.get("content", ""),
                })

            return results

        except Exception as e:
            print(f"Search error: {e}")
            return []


# Quick test
if __name__ == "__main__":
    tool = SearchTool()
    results = tool.search("AI agents in enterprise software 2024")
    for r in results:
        print(f"\n{r['title']}")
        print(f"  {r['url']}")
        print(f"  {r['content'][:200]}...")
