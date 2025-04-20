import random
import re

# ————————————————————————————————————————————————————————————
HESITATIONS = ["[pause]", "[euh]", "[hum]", "[silence]",
               "[inspiration]", "[expiration]"]

GREETINGS = {"bonjour", "allo", "salut", "bonsoir", "coucou"}

SCAM_KEYWORDS = {"arnaque", "bitcoin", "frais", "prix", "payer", "virement", "argent", "transaction"}

# ── Insertions d’hésitations ───────────────────────────────
def insert_hesitations(text: str) -> str:
    words = text.split()
    n = max(1, len(text) // 40)          # ~1 hésitation / 40 caractères
    for _ in range(n):
        idx = random.randint(1, len(words) - 1)
        words.insert(idx, random.choice(HESITATIONS))
    return " ".join(words)

# ── Coupe à 25 mots max ────────────────────────────────────
def trim_reply(text: str, limit: int = 25) -> str:
    words = text.split()
    return " ".join(words[:limit]) + ("…" if len(words) > limit else "")

# ── Détection salutation courte ────────────────────────────
def is_greeting_only(text: str) -> bool:
    w = text.lower().split()
    return 0 < len(w) <= 2 and all(tok in GREETINGS for tok in w)

# ── Détection phrase “significative” ───────────────────────
def is_meaningful(text: str) -> bool:
    w = text.split()
    return (
        len(w) >= 3                        # au moins 3 mots
        or "?" in text                     # ou une question
        or not is_greeting_only(text)      # ou salutation intégrée dans phrase
    )
def first_sentence(text: str) -> str:
    """
    Garde jusqu’au premier '?' ou '.', pour forcer une seule question / phrase.
    """
    for stop in ["?", "."]:
        if stop in text:
            return text.split(stop)[0][:120].strip() + stop
    return text[:120]            # fail‑safe

def scam_already_mentioned(history: list[dict]) -> bool:
    for msg in history:
        if msg["role"] == "user":
            if any(word in msg["content"].lower() for word in SCAM_KEYWORDS):
                return True
    return False

def to_ssml(text: str) -> str:
    """
    Convertit nos marqueurs custom en balises SSML Google TTS.
    - [pause] / [silence]      →  <break time="600ms"/>
    - [hum]                    →  <break time="400ms"/>  (remplace ou supprime)
    - [inspiration] / [expiration] supprimés
    """
    text = re.sub(r"\[(pause|silence)\]",   '<break time="600ms"/>', text, flags=re.I)
    text = re.sub(r"\[hum\]",               '<break time="400ms"/>', text, flags=re.I)  # ou '' si tu préfères supprimer
    text = re.sub(r"\[inspiration\]|\[expiration\]", '', text, flags=re.I)
    return " ".join(text.split())           # nettoie espaces doublons