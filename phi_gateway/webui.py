"""Proper web UI for the PHI De-identification Gateway (Flask backend).

    python -m phi_gateway.webui          ->  http://localhost:8000

Endpoints:
    GET  /                the single-page app (static/index.html)
    GET  /api/status      provider info + headline metrics
    POST /api/deidentify  {text}                -> masked note + mapping
    POST /api/ask         {question, note, mock} -> LLM answer (placeholders only)

Rehydration for display is done client-side from the mapping (the backend
`rehydrate` remains the canonical implementation used by the pipeline).
"""

from __future__ import annotations

import json
import threading
import webbrowser
from pathlib import Path

from flask import Flask, jsonify, request, send_from_directory

from .llm import MockLLM, get_llm
from .masker import PHIGateway

ROOT = Path(__file__).resolve().parent.parent

app = Flask(__name__, static_folder="static", static_url_path="/static")

_LOCK = threading.Lock()          # gateway + LLM are not thread-safe state
_gateway: PHIGateway | None = None
_llm_real = None
_llm_mock = MockLLM()


def gateway() -> PHIGateway:
    global _gateway
    if _gateway is None:
        _gateway = PHIGateway()
    return _gateway


def llm_real():
    global _llm_real
    if _llm_real is None:
        _llm_real = get_llm()
    return _llm_real


def _stats() -> dict:
    out = {}
    try:
        m = json.loads((ROOT / "results" / "metrics_test.json").read_text())
        model = m.get("model", {})
        out["recall"] = model.get("micro", {}).get("recall")
        out["precision"] = model.get("micro", {}).get("precision")
        out["leak_rate"] = model.get("leak_rate")
    except Exception:
        pass
    try:
        s = json.loads((ROOT / "models" / "distilbert-phi" /
                        "training_summary.json").read_text())
        out["params"] = s.get("total_params")
    except Exception:
        pass
    return out


@app.get("/")
def index():
    return send_from_directory(app.static_folder, "index.html")


@app.get("/api/status")
def status():
    return jsonify({"stats": _stats(),
                    "llm_ready": _llm_real is not None})


@app.post("/api/deidentify")
def deidentify():
    data = request.get_json(force=True)
    text = (data or {}).get("text", "")
    if not text.strip():
        return jsonify({"error": "empty note"}), 400
    with _LOCK:
        masked, mapping, entities = gateway().deidentify(
            text, return_entities=True)
        report = dict(gateway().last_report)
    return jsonify({
        "masked": masked,
        "mapping": mapping,
        "entities": [
            {"start": e["start"], "end": e["end"], "label": e["label"],
             "value": e["value"], "late": e.get("late", False)}
            for e in entities],
        "n_masked": len(mapping),
        "late_catches": report.get("late_catches", 0),
    })


@app.post("/api/ask")
def ask():
    data = request.get_json(force=True) or {}
    question = data.get("question", "").strip()
    note = data.get("note", "").strip()
    use_mock = bool(data.get("mock"))
    if not question or not note:
        return jsonify({"error": "question and note required"}), 400
    prompt = f"{question}\n\nNOTE:\n{note}"
    with _LOCK:
        llm = _llm_mock if use_mock else llm_real()
        try:
            answer = llm.complete(prompt)
        except TypeError:
            answer = llm.complete(prompt, stream=False)
    return jsonify({"answer": answer, "provider": llm.name})


def main() -> None:
    port = 8000
    print("PHI De-identification Gateway UI -> http://localhost:%d" % port)
    threading.Timer(1.5, lambda: webbrowser.open(f"http://localhost:{port}")).start()
    app.run(host="127.0.0.1", port=port, debug=False, threaded=True)


if __name__ == "__main__":
    main()
