"""Topic knowledge agent: general explanations from the language model."""
from llm.ollama_client import generate

SYSTEM = ("You are a patient tutor. Explain concepts step by step for a learner: "
          "start with a one-sentence definition, then the key ideas, then a short "
          "example. Say when you are unsure rather than guessing.")

PROMPT = "Question: {query}"


def explain_topic(query):
    return generate(PROMPT.format(query=query), system=SYSTEM)
