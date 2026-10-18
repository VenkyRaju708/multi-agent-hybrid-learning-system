"""Document agent: answers only from the retrieved document context."""
from llm.ollama_client import generate

SYSTEM = ("You are a tutor answering from the learner's own document. Use only "
          "the context provided. If the context does not contain the answer, "
          "say that the document does not cover it.")

PROMPT = """Context from the learner's document:
{context}

Question: {query}

Explain the answer clearly using only the context above."""


def explain(context, query):
    return generate(PROMPT.format(context=context or "(no context)", query=query),
                    system=SYSTEM)
