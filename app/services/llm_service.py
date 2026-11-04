from openai import OpenAI

from app.config import settings

client = OpenAI(api_key=settings.OPENAI_API_KEY)

def generate(system_prompt: str, user_prompt: str, model: str | None = None,temperature: float = 0.0) -> dict:
    if model is None:
        model = settings.llm_model_answer
    response = client.chat.completions.create(
        model=model,
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt}
        ],
        temperature=temperature
    )
    text = response.choices[0].message.content
    usage = {
        "prompt_tokens": response.usage.prompt_tokens if response.usage else 0,
        "completion_tokens": response.usage.completion_tokens if response.usage else 0,
        "total_tokens": response.usage.total_tokens if response.usage else 0
    }
    return {"text": text, "usage": usage}

def generate_with_json(system_prompt: str, user_prompt: str, model: str | None = None, temperature: float = 0.0) -> dict:
    if model is None:
        model = settings.llm_model_answer
    response = client.chat.completions.create(
        model=model,
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt}
        ],
        temperature=temperature,
        response_format={"type": "json_object"}
    )
    text = response.choices[0].message.content or ""
    usage = {
        "prompt_tokens": response.usage.prompt_tokens if response.usage else 0,
        "completion_tokens": response.usage.completion_tokens if response.usage else 0,
        "total_tokens": response.usage.total_tokens if response.usage else 0
    }
    return {"text": text, "usage": usage}