"""
Central config for ResearchFlow.

Groq's structured-output support is less reliable than OpenAI's on complex nested schemas (Plan, GlobalImagePlan).

NOTE: llama-3.3-70b-versatile was deprecated by Groq on June 17, 2026.
Switched to openai/gpt-oss-120b (Groq's recommended replacement) below,
using method="json_schema" instead of "function_calling" since that's
what Groq specifically built for gpt-oss models (function_calling and
the default/tool-calling strategies have a known bug with gpt-oss-120b).
"""
import os
from dotenv import load_dotenv
from langchain_groq import ChatGroq

load_dotenv()

GROQ_API_KEY = os.getenv("GROQ_API_KEY")

if not GROQ_API_KEY:
    raise RuntimeError(
        "GROQ_API_KEY not set. Copy .env.example to .env and add your key."
    )

DEFAULT_MODEL = "openai/gpt-oss-120b"


def get_llm(temperature: float = 0.0, model: str = DEFAULT_MODEL) -> ChatGroq:
    return ChatGroq(model=model, temperature=temperature, api_key=GROQ_API_KEY)


# Shared LLM instance for nodes that don't need a custom temperature/model.
llm = get_llm()


def structured(schema, model_llm=None):
    """
    Helper so every node requests structured output the same, tested way.
    json_schema (strict mode) is what Groq built specifically for
    openai/gpt-oss-120b - safer than function_calling for this model.
    """
    target = model_llm or llm
    return target.with_structured_output(schema, method="json_schema")