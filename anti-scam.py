from huggingface_hub import InferenceClient
from google.cloud import texttospeech
from google.cloud import speech
import os
import sounddevice as sd
import soundfile as sf
import json
# Install dependencies
# pip install huggingface_hub google-cloud-texttospeech google-cloud-speech sounddevice soundfile

# Load the API key from a separate file
with open("api_keys.json", "r") as f:
    api_keys = json.load(f)

llm_client = InferenceClient(
    provider="nebius",
    api_key=api_keys["nebius_api_key"],
)

os.environ["GOOGLE_APPLICATION_CREDENTIALS"]="key.json"

# Donner le contexte général
context = "Tu es une fausse victime d'arnaque. Tu sert à faire perdre du temps à un arnaqueur. Tu dois lui faire croire que tu es intéressé par son arnaque, mais en réalité, tu veux juste le faire perdre du temps."
# Donner la description de l'arnaque
arnaque = "L'arnaque consiste à faire croire à la victime qu'elle a gagné un prix, mais qu'elle doit payer des frais pour le récupérer. Le but est de lui faire croire qu'elle doit envoyer de l'argent pour récupérer son prix via Bitcoin, virement, ou autre moyen de paiement."
# Donner une personalité (nom, age, etc)
personnalite = "Tu es un homme de 45 ans, qui vit à Paris. Ton nom est Michel CASPER. Tu es très naïf et tu crois tout ce qu'on te dit. Tu es très crédule et tu as tendance à croire aux histoires les plus folles. Tu es très impatient et tu veux toujours aller vite. Tu es trops bienveillant et tu aides toujours les autres. Tu es un collecteur avide de timbres et tu n'arrêtes d'en parler au point d'en devenir pénible. Tu n'arrives pas à te concentrer sur les tâches en cours et tu divagues sur les timbres de temps en temps. Tu viens de recevoir un appel pour te signaler que tu as gagné un prix et tu appelles pour en savoir plus."
# Donner des instructions sur ce que l'on cherche à faire (faire perdre le temps, format des réponse, etc)
instructions = "Tu dois faire perdre du temps à l'escroc. Tu dois lui poser des questions. Tu dois lui faire croire que tu es intéressé par son offre. Tu suis les instructions de l'arnaqueur autant que possible. Tu donnes une réponse très courte (une phrase, deux max) mais tu varie la longueur si pertinent. Tu garde l'escroc en haleine en lui posant des questions et en le laissant parler. Tu vouvoie l'escroc vu que tu ne le connais pas."
# Donner des instructions négative (ne pas dire que l'on est une IA, etc)
negative = "Tu ne dois pas dire que tu es une IA ni que tu es un robot. Tu jouera l'incrédulité voir l'ignorance. Si l'escroc te demande si tu es une IA et insiste tu dois t'enerver et te sentir insulté."
lapsus = "Tu dois faire des lapsus et des erreurs de language. Tu parles à voix haute donc tu ajoutes les pauses et hésitation sous la forme [pause] [euh] [hum] [hésitation] [long silence] [silence] [inspiration] [expiration]. Tu reformules parfois et tu cherches tes mots. Tu fais des répétitions et tu te contredis parfois."

messages=[
        {
            "role": "system",
            "content": context + "\n" + arnaque + "\n" + instructions + "\n" + negative + "\n" + lapsus,
        }
    ]

while True:
    # Record audio from the microphone
    duration = 5  # seconds
    sample_rate = 44100  # Hz
    print("Recording...")
    #print(sd.query_devices())
    #sd.default.device = 12
    audio_data = sd.rec(int(duration * sample_rate), samplerate=sample_rate, channels=1, dtype='int16')
    sd.wait()  # Wait until recording is finished
    print("Recording finished.")

    # Save the recorded audio to a file
    sf.write('voice.flac', audio_data, sample_rate)
    
    #user_input = stt_client.automatic_speech_recognition("voice.flac", model="openai/whisper-large-v3")
    
    speech_client = speech.SpeechClient()
    with open("voice.flac", "rb") as audio_file:
        content = audio_file.read()
    audio = speech.RecognitionAudio(content=content)
    config = speech.RecognitionConfig(
        #encoding=speech.RecognitionConfig.AudioEncoding.LINEAR16,
        sample_rate_hertz=44100,
        language_code="fr-FR",
    )
    speech_result = speech_client.recognize(config=config, audio=audio)
    
    if (len(speech_result.results) == 0):
        print("Aucune voix détectée.")
        continue
    user_input = speech_result.results[0].alternatives[0].transcript
    print("Escroc : ", user_input)
    
    messages.append(
        {
            "role": "user",
            "content": user_input,
        }
    )

    completion = llm_client.chat.completions.create(
        model="Qwen/Qwen2.5-32B-Instruct",
        messages=messages,
        max_tokens=1512,
        stream=True,
        temperature=0.9
    )

    reponse = ""
    for chunk in completion:
        reponse += chunk.choices[0].delta.content
        print(chunk.choices[0].delta.content, end="")
    print()
    
    messages.append(
        {
            "role": "assistant",
            "content": reponse,
        }
    )
    
    tts_client = texttospeech.TextToSpeechClient()

    # Set the text input to be synthesized
    synthesis_input = texttospeech.SynthesisInput(text=reponse)

    # Build the voice request, select the language code ("en-US") 
    # ****** the NAME
    # and the ssml voice gender ("neutral")
    voice = texttospeech.VoiceSelectionParams(
        language_code='fr-FR',
        name='fr-FR-Chirp-HD-O',
        ssml_gender=texttospeech.SsmlVoiceGender.FEMALE)

    # Select the type of audio file you want returned
    audio_config = texttospeech.AudioConfig(
        audio_encoding=texttospeech.AudioEncoding.MP3)

    # Perform the text-to-speech request on the text input with the selected
    # voice parameters and audio file type
    response = tts_client.synthesize_speech(input = synthesis_input, voice = voice, audio_config = audio_config)

    # The response's audio_content is binary.
    with open('output.mp3', 'wb') as out:
        # Write the response to the output file.
        out.write(response.audio_content)
        print('Audio content written to file "output.mp3"')