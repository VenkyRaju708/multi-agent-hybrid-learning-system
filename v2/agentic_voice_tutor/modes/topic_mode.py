from agents.topic_agent import explain_topic


def handle_topic(query, timings):
    response = timings.measure("generate", explain_topic, query)
    return response, []
