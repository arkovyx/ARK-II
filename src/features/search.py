import os
import requests
from dotenv import load_dotenv

load_dotenv()

TAVILY_API_KEY = os.getenv("TAVILY_API_KEY")
TAVILY_URL = "https://api.tavily.com/search"


def web_search(query, max_results=5):
    """
    Search the web using Tavily.
    Returns (dict_with_context, None) on success,
    or (None, error_message) on failure.
    """
    if not TAVILY_API_KEY:
        return None, "❌ TAVILY_API_KEY not set in .env"

    try:
        r = requests.post(
            TAVILY_URL,
            json={
                "api_key": TAVILY_API_KEY,
                "query": query,
                "search_depth": "basic",       # "basic" = 1 credit, "advanced" = 2
                "max_results": max_results,
                "include_answer": True,
                "include_raw_content": False,
            },
            timeout=15,
        )
        data = r.json()

        if "results" not in data:
            return None, f"❌ Search error: {data.get('detail', 'unknown')}"

        lines = []
        for i, item in enumerate(data["results"], 1):
            title = item.get("title", "")
            url = item.get("url", "")
            snippet = item.get("content", "")[:400]
            lines.append(f"[{i}] {title}\n{url}\n{snippet}\n")

        context = "\n".join(lines)
        tavily_answer = data.get("answer", "")

        return {
            "context": context,
            "answer": tavily_answer,
            "query": query,
        }, None

    except requests.Timeout:
        return None, "❌ Search timed out"
    except Exception as e:
        return None, f"❌ Search error: {e}"
