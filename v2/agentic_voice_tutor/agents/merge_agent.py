"""Combines the document answer and the general answer for mixed queries."""
from llm.ollama_client import generate

PROMPT = """MERGE_TASK
Combine the two answers below into one explanation for the learner.
Keep what the document says separate from general knowledge, and say
"According to your document" before document facts.

Question: {query}

Answer from the document:
{doc_answer}

General answer:
{topic_answer}"""


def merge(query, doc_answer, topic_answer):
    return generate(PROMPT.format(query=query, doc_answer=doc_answer,
                                  topic_answer=topic_answer))
