import threading
from prompts import build_system_prompt
from voice import record_chunk, transcribe, speak, detect_silence
from llm_client import chat_completion
from emotion import inject_prosody
from utils import (
    insert_hesitations,
    trim_reply,
    first_sentence,
    is_meaningful,
    is_greeting_only,
)

# Event pour contrôler le démarrage/arret
active_event = threading.Event()

IDLE_LIMIT = 3  # tours muets avant digression

def conversation_stream():
    messages = [{"role": "system", "content": build_system_prompt()}]
    idle_turns = 0

    while True:
        # Attend que l'on démarre
        active_event.wait()

        chunk = record_chunk(5)

        # Silence → incrémente idle, digression si atteint
        if detect_silence(chunk):
            idle_turns += 1
            if idle_turns >= IDLE_LIMIT:
                idle_turns = 0
                reply = insert_hesitations("Oh, à propos… vous aimez les timbres ?")
                yield {"role": "michel", "text": reply}
                speak(inject_prosody(reply))
            continue

        user_text = transcribe(chunk).strip()
        if not user_text:
            continue  # bruit ignoré

        yield {"role": "escroc", "text": user_text}

        # Salutation courte
        if is_greeting_only(user_text):
            idle_turns = 0
            reply = insert_hesitations("Bonjour, monsieur.")
            yield {"role": "michel", "text": reply}
            speak(inject_prosody(reply))
            continue

        # Filtrer phrases non signifiantes
        if not is_meaningful(user_text):
            continue

        idle_turns = 0
        raw = chat_completion(messages + [{"role": "user", "content": user_text}])
        reply = first_sentence(raw)
        reply = trim_reply(reply)
        reply = insert_hesitations(reply)

        yield {"role": "michel", "text": reply}
        speak(inject_prosody(reply))

        # Mémorise le tour
        messages.append({"role": "user", "content": user_text})
        messages.append({"role": "assistant", "content": reply})