import os
import json
import pathlib
import sys
import threading
from flask import Flask, Response, render_template, stream_with_context
from dotenv import load_dotenv

# ─── Charger les variables d'env (Google, Nebius, etc.) ────────────
dotenv_path = os.path.join(os.path.dirname(__file__), ".env")
if os.path.exists(dotenv_path):
    load_dotenv(dotenv_path)

# Rendre src/ importable
SRC_DIR = pathlib.Path(__file__).parent / "src"
sys.path.append(str(SRC_DIR))

from bot_core import conversation_stream, active_event

app = Flask(__name__, template_folder="templates")


def sse_events():
    for evt in conversation_stream():
        try:
            yield f"data: {json.dumps(evt, ensure_ascii=False)}\n\n"
        except Exception as e:
            # log dans la console Flask
            app.logger.error("Erreur dans SSE: %s", e)
            # envoie un event 'error' au client
            yield f"event: error\ndata: {json.dumps({'error': str(e)})}\n\n"
            break

@app.route("/stream")
def stream():
    return Response(stream_with_context(sse_events()),
                    mimetype="text/event-stream")


@app.route("/")
def index():
    return render_template("index.html")


@app.route("/start", methods=["POST"])
def start():
    active_event.set()
    return ('', 204)


@app.route("/stop", methods=["POST"])
def stop():
    active_event.clear()
    return ('', 204)


if __name__ == "__main__":
    # Lance Flask en mode debug
    app.run(port=8000, debug=True)