import streamlit as st

import config
from pipeline import Timings, answer, load_document

st.title("Agentic Voice Tutor")

uploaded_file = st.file_uploader("Upload PDF", type=["pdf"])

query = st.text_input("Ask a question or topic")

recording = None
if hasattr(st, "audio_input"):
    recording = st.audio_input("Or ask by voice")
else:
    st.caption("Voice input needs a newer Streamlit (st.audio_input).")

if st.button("Ask"):
    timings = Timings()

    if recording is not None:
        from llm.stt_engine import transcribe

        spoken = timings.measure("stt", transcribe, recording.getvalue())
        if spoken:
            query = spoken
            st.write(f"**You asked:** {query}")

    if not query:
        st.warning("Type a question or record one.")
        st.stop()

    doc_index = None
    if uploaded_file:
        doc_index, _cached = load_document(uploaded_file.getvalue(),
                                           uploaded_file.name, timings)

    browser_tts = config.TTS_MODE == "browser"
    result = answer(query, doc_index, tts=browser_tts, timings=timings)

    st.write("### Explanation")
    st.write(result["answer"])

    st.write("### Notes")
    st.write(result["notes"])

    if browser_tts and result["audio_path"]:
        st.audio(result["audio_path"], format="audio/wav")
    elif config.TTS_MODE == "host":
        from llm.tts_engine import speak

        timings.measure("tts", speak, result["answer"])

    with st.expander("How this answer was produced"):
        route = result["route"]
        st.write(f"Route: **{result['answered_as']}** ({route['method']}) - {route['reason']}")
        if result["chunks"]:
            st.write("Retrieved chunks (cosine similarity):")
            for c in result["chunks"]:
                st.write(f"- {c['score']:.2f}: {c['text'][:200]}...")
        st.write("Stage timings (seconds):")
        st.json({k: round(v, 3) for k, v in timings.items()})
