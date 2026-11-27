import json
import logging

from ragas import evaluation

from app.config import settings
from app.models import CRAGEvaluation,RetrievedChunk
from app.services.llm_service import generate_with_json
from app.services.web_search import search_web, search_web_search

logger = logging.getLogger(__name__)

_GRADING_PROMPT = """You are evaluating whether retrieved documents are relevant to answering a user question.

User Question: {question}

Retrieved Documents:
{documents}

Rate the overall relevance on a scale of 0.0 to 1.0, where:
- 0.0-0.3: Irrelevant — documents do not help answer the question
- 0.3-0.5: Ambiguous — documents partially help but are unclear or insufficient
- 0.5-0.7: Somewhat relevant — documents contain useful information but may need more
- 0.7-1.0: Highly relevant — documents directly answer the question

Respond ONLY with a JSON object:
{{"relevance_score": float, "relevance_label": "irrelevant"|"ambiguous"|"somewhat_relevant"|"highly_relevant", "confidence": float, "reasoning": str}}
"""

def grade_chunks(question: str, chunks: list[RetrievedChunk]) -> CRAGEvaluation:
    """Grade retrived chunks for the relevance """
    documents = (
        "\n\n".join(f"{i+1}. {chunk.text}" for i , chunk in enumerate(chunks))
    )
    prompt = _GRADING_PROMPT.format(question=question,documents=documents)
    try:
        result = generate_with_json(system_prompt = "you are a document relevance grader.",
                    user_prompt = prompt,
                    model= settings.llm_model_grader,
                    temperature = 0.0)
        parsed = result.get("text","")
        parsed_json = json.loads(parsed)
        return CRAGEvaluation(
            relevance_score = parsed_json.get("relevance_score",0.0),
            relevance_label = parsed_json.get("relevance_label","irrelevant"),
            confidence = parsed_json.get("confidence",0.0),
            reasoning = parsed_json.get("reasoning","")
        )
    except Exception as e:
        logger.error("Error grading chunks: %s", e)
        return CRAGEvaluation(
            relevance_score = 0.0,
            relevance_label = "irrelevant",
            confidence = 0.0,
            reasoning = "Error occurred during grading."
        )
def should_trigger_web_Search(evaluation: CRAGEvaluation) -> bool:
    """Determine if a web search should be triggered based on the evaluation."""
    return evaluation.relevance_score < settings.crag_relevance_threshold

def crag_pipeline(question: str, chunks: list[RetrievedChunk],enable_crag: bool = True) -> tuple[list[RetrievedChunk],CRAGEvaluation,bool]:
    
    if not enable_crag:
        logger.info("CRAG is disabled.")
        evaluation = CRAGEvaluation(
                    relevance_score = 0.0,
                    relevance_label = "irrelevant",
                    confidence = 1.0,
                    reasoning = "CRAG disabled."
                )
        return (chunks, evaluation, False)
    if not chunks:
        evaluation =    CRAGEvaluation(
                    relevance_score = 0.0,
                    relevance_label = "irrelevant",
                    confidence = 1.0,
                    reasoning = "No chunks retrieved."
                )
        try:
            logger.info("No chunks retrieved, triggering web search.")
            web_chunks =  search_web(question)
            return (web_chunks,evaluation,True)
        except ValueError:
            logger.warning("Web search triggered but Tavily API key not configured")
            return ([], evaluation, False)
    evaluation = grade_chunks(question, chunks)
    if should_trigger_web_Search(evaluation):
        try:
            logger.info("Relevance score below threshold, triggering web search.")
            web_chunks =  search_web(question)
            return (web_chunks,evaluation,True)
        except ValueError:
            logger.warning("Web search triggered but Tavily API key not configured")
            return ([], evaluation, False)
    return (chunks, evaluation, False)