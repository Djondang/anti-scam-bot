import os
import asyncio
import logging
from dotenv import load_dotenv

from prompts import build_system_prompt
from voice import record_chunk, transcribe, speak, detect_silence
from llm_client import chat_completion
from emotion import inject_prosody
from utils import (
    insert_hesitations, 
    trim_reply, first_sentence,
    is_meaningful, 
    is_greeting_only, 
    scam_already_mentioned,
    to_ssml,
    SCAM_KEYWORDS
)

# ─── Initialisation ──────────────────────────────────────────────────────
load_dotenv()
logger = logging.getLogger("anti-scam")

MICHEL_PROMPT = build_system_prompt()

IDLE_LIMIT = 3   # n tours muets avant digression timbres

# ─── Boucle principale ──────────────────────────────────────────────────
async def loop_call() -> None:
    messages: list[dict] = [{"role": "system", "content": MICHEL_PROMPT}]
    idle_turns = 0  # compteur de tours sans vraie interaction

    while True:
        # 1. Enregistrement micro (5 s, 48 kHz)
        chunk = record_chunk(5)

        # 2. Silence absolu → incrémente idle, peut déclencher digression
        if detect_silence(chunk):
            idle_turns += 1
            if idle_turns >= IDLE_LIMIT:
                idle_turns = 0
                reply = insert_hesitations("Oh, à propos… vous aimez les timbres ?")
                print(f"Michel : {reply}")
                speak(inject_prosody(reply))
            continue

        # 3. Transcription
        user_text = transcribe(chunk).strip()
        if not user_text:          # bruit résiduel
            continue

        # 4. Salutation très courte
        if is_greeting_only(user_text):
            idle_turns = 0
            reply = insert_hesitations("Bonjour !")
            print(f"Michel : {reply}")
            speak(inject_prosody(reply))
            continue

        # 5. Vraie phrase ? sinon ignore
        if not is_meaningful(user_text):
            continue

        # 6. Dialogue normal : reset idle, envoie au LLM
        idle_turns = 0
        print(f"Escroc : {user_text}")
        messages.append({"role": "user", "content": user_text})
        
        reply = await asyncio.to_thread(chat_completion, messages)

        if not scam_already_mentioned(messages):
            for w in SCAM_KEYWORDS:
                reply = reply.replace(w, "").replace(w.capitalize(), "")
            reply = " ".join(reply.split())           # nettoie espaces doublons

        # ── Post‑traitements dans le bon ordre ──────────────────────────
        reply = first_sentence(reply)      # 1. garde UNE seule phrase/question
        reply = trim_reply(reply)          # 2. limite à 25 mots max
        reply = insert_hesitations(reply)  # 3. ajoute [pause] [euh] …
        reply = to_ssml(reply)             # 4. convertit en SSML
        ssml_reply = inject_prosody(reply) # 5. enveloppe en SSML

        print(f"Michel : {reply}")
        messages.append({"role": "assistant", "content": reply})
        speak(ssml_reply)

# ─── Lancement ───────────────────────────────────────────────────────────
if __name__ == "__main__":
    asyncio.run(loop_call())
