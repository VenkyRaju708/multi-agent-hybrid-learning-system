from agents.merge_agent import merge
from agents.retrieval_agent import retrieve
from agents.topic_agent import explain_topic
from agents.tutor_agent import explain


def handle_mixed(query, doc_index, timings):
    hits, context = timings.measure("retrieve", retrieve, doc_index, query)

    def _generate():
        doc_answer = explain(context, query)
        topic_answer = explain_topic(query)
        return merge(query, doc_answer, topic_answer)

    response = timings.measure("generate", _generate)
    return response, hits
