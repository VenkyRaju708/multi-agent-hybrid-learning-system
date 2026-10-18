from agents.retrieval_agent import retrieve
from agents.tutor_agent import explain


def handle_document(query, doc_index, timings):
    hits, context = timings.measure("retrieve", retrieve, doc_index, query)
    response = timings.measure("generate", explain, context, query)
    return response, hits
