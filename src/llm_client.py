from huggingface_hub import InferenceClient
import os

# ─── Client Nebius synchrone ─────────────────────────────────────────────
client = InferenceClient(
    provider="nebius",
    api_key=os.getenv("NEBIUS_API_KEY"),  # doit être défini ou présent dans api_keys.json
)


def chat_completion(messages: list[dict]) -> str:
    """
    Appelle le modèle Qwen2.5‑32B‑Instruct en mode streaming.
    Bloquant, mais on le lancera dans un thread pour ne pas figer l'event‑loop.
    """
    stream = client.chat.completions.create(
        model="Qwen/Qwen2.5-32B-Instruct",
        messages=messages,
        max_tokens=120,
        stream=True,
        temperature=0.9,
    )

    reply = ""
    for chunk in stream:  # itérateur synchrone
        delta = chunk.choices[0].delta.content
        if delta:
            reply += delta
    return reply
