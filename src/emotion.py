import random

EMO_TAGS = [
    ('<prosody rate="slow">', '</prosody>'),
    ('<prosody pitch="+4st">', '</prosody>'),
    ('<prosody volume="loud">', '</prosody>'),
    ('<prosody rate="slow" pitch="-2st">', '</prosody>'),   # combo
]

def inject_prosody(text: str) -> str:
    start, end = random.choice(EMO_TAGS)
    # petite pause avant de finir la phrase
    return f'<speak>{start}{text}<break time="600ms"/>{end}</speak>'
