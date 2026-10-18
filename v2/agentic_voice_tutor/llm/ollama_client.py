"""LLM access. Uses a local Ollama server by default.

Set AVT_LLM=mock to use a deterministic fake model in tests; it never
contacts a server and its outputs are not real model answers.
"""
import json
import re

import config


def generate(prompt, system=None):
    if config.LLM_BACKEND == "mock":
        return _mock_generate(prompt, system)
    import ollama

    messages = []
    if system:
        messages.append({"role": "system", "content": system})
    messages.append({"role": "user", "content": prompt})
    res = ollama.chat(model=config.LLM_MODEL, messages=messages)
    return res["message"]["content"]


def backend_name():
    if config.LLM_BACKEND == "mock":
        return "mock"
    return "ollama:" + config.LLM_MODEL


# --- Mock backend (tests only) ---------------------------------------------

def _mock_generate(prompt, system=None):
    if "ROUTER_TASK" in prompt:
        query = prompt.rsplit("Query:", 1)[-1].lower()
        if "unparsable" in query:
            return "I am not sure what you mean."
        if "mixed" in query or "and also" in query:
            label = "mixed"
        elif "document" in query or "pdf" in query or "notes" in query:
            label = "document"
        else:
            label = "topic"
        return json.dumps({"label": label, "reason": "mock decision"})
    if "JUDGE_TASK" in prompt:
        return json.dumps({"faithfulness": "partial", "relevance": 3,
                           "comment": "mock judge output"})
    if "MERGE_TASK" in prompt:
        return "MOCK merged answer."
    if "NOTES_TASK" in prompt:
        return "- MOCK note"
    match = re.search(r"Question:\s*(.*)", prompt)
    question = match.group(1).strip() if match else "the question"
    return "MOCK answer to: " + question
