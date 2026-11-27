import logging
from app.config import settings
from app.models import RetrievedChunk


logger = logging.getLogger(__name__)

def search_web(question: str,max_results: int = 5) -> list[RetrievedChunk]:
    
    if not settings.tavily_api_key:
        raise ValueError("Tavily API key is not set")
    try:
        import tavily
        tavily.api_key = settings.tavily_api_key
        results = tavily.search(question,max_results = max_results)
        if results not in [None, []]:
            return [
                RetrievedChunk(
                    content = result["content"],
                    source = result["url"],
                    score = result.get("score",0.0) )
                    for result in results
            ]
    except Exception as e:
        logger.error("Error occurred during web search: %s", e)
        return []