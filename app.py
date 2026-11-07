"""Interactive web preview of the PHI De-identification Gateway.

    streamlit run app.py        ->  http://localhost:8501

Paste (or upload) a clinical note, mask it, ask the LLM a question about
the MASKED note, and watch the identifiers come back in the answer.
The mapping never leaves this machine - only the masked note is sent to
the LLM, and by default even the LLM runs locally on CPU.
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

import streamlit as st

from phi_gateway.llm import MockLLM, get_llm
from phi_gateway.masker import PHIGateway

st.set_page_config(page_title="PHI De-identification Gateway",
                   page_icon="🛡️", layout="wide")

DEFAULT_NOTE = (Path(__file__).parent / "data" / "example_note.txt")


@st.cache_resource(show_spinner="Loading the de-identification model (first run ~10 s)...")
def load_gateway() -> PHIGateway:
    return PHIGateway()


@st.cache_resource(show_spinner="Loading the LLM (first run loads the local model)...")
def load_llm(use_mock: bool):
    return MockLLM() if use_mock else get_llm()


st.title("🛡️ PHI De-identification Gateway")
st.caption(
    "mask → LLM → restore. The mapping stays on this machine; the LLM only "
    "ever sees placeholders like [NAME_1].")

gateway = load_gateway()
mode = st.sidebar.radio(
    "LLM for the round trip",
    ["Local LLM (real, on CPU, ~30 s/answer)", "Instant mock (no waiting)"],
    index=0)
use_mock = mode.startswith("Instant")
llm = load_llm(use_mock)
st.sidebar.success(f"Provider: {llm.name}")
st.sidebar.markdown(
    "**Model**: DistilBERT fine-tune, 65,211,675 params + regex safety net\n\n"
    "**Test-set recall**: 0.966 · **leak rate**: 4% (Presidio: 74.6% / 88%)")

left, right = st.columns(2)

with left:
    st.subheader("1 · Clinical note (never sent as-is)")
    text = st.text_area(
        "note", value=DEFAULT_NOTE.read_text(encoding="utf-8"), height=300,
        label_visibility="collapsed")
    if st.button("🔒 Deidentify", type="primary", use_container_width=True):
        masked, mapping = gateway.deidentify(text)
        st.session_state.update(masked=masked, mapping=mapping,
                                report=dict(gateway.last_report))
    if "masked" in st.session_state:
        rep = st.session_state.report
        st.metric("identifiers masked", rep.get("entities", 0),
                  f"{rep.get('late_catches', 0)} by safety net")
        st.code(st.session_state.masked, language=None)

with right:
    st.subheader("2 · Private mapping (stays local)")
    if "mapping" in st.session_state:
        st.dataframe(
            [{"placeholder": k, "original value": v}
             for k, v in st.session_state.mapping.items()],
            use_container_width=True, hide_index=True)
    else:
        st.info("Click **Deidentify** to build the mapping.")

st.divider()
st.subheader("3 · Round trip through the LLM")
if "masked" in st.session_state:
    question = st.text_input(
        "Ask about the MASKED note",
        value="What is the working diagnosis and the follow-up plan? "
              "Answer in 3 sentences.",
        key="question")
    if st.button("🤖 Ask the LLM", type="primary"):
        prompt = f"{question}\n\nNOTE:\n{st.session_state.masked}"
        with st.spinner(f"{llm.name} is answering (local CPU model takes "
                        f"~30 s)..."):
            try:
                answer = llm.complete(prompt)
            except TypeError:
                answer = llm.complete(prompt, stream=False)
        restored = gateway.rehydrate(answer, st.session_state.mapping)
        unknowns = gateway.last_report.get("unknown_placeholders", [])
        c1, c2 = st.columns(2)
        with c1:
            st.markdown("**LLM answer (what it could see)**")
            st.write(answer)
        with c2:
            st.markdown("**Rehydrated answer (identifiers restored)**")
            st.write(restored)
        if unknowns:
            st.warning(f"LLM returned {len(unknowns)} placeholder(s) that "
                       f"were never in the input - left untouched (no data "
                       f"risk): {unknowns}")
        st.caption("Privacy check: the prompt contained only the masked "
                   "note; the mapping was applied AFTER the answer came "
                   "back, on this machine.")
else:
    st.info("Deidentify a note first (step 1).")
