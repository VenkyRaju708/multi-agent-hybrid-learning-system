from llm.ollama_client import generate

PROMPT = """NOTES_TASK
Write 3 to 6 short bullet-point study notes for the explanation below.

{text}"""


def generate_notes(text):
    return generate(PROMPT.format(text=text))
