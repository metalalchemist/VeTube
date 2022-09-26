from flask import request, jsonify, send_file
import os
import io
import inflect
import uuid
import gc
import json
from torch import load, device
import gdown
d = 'https://drive.google.com/uc?id='
from tacotron2_model import Tacotron2
from playsound import playsound
from app import app, DATA_FOLDER, RESULTS_FOLDER
from vocoders import Hifigan
from synthesize import synthesize


VOCODER_FILES = {
    "hifigan.pt": "15-CfChiUdX2zay0kZmQNuXd0jRsqfmhq",
    "config.json": "1sJ71OLN6FcP7sY4vsKTrm0SJnp4flDy2",
}
HIFIGAN_MODEL = "hifigan.pt"
HIFIGAN_CONFIG = "config.json"

with open("voices.json") as f:
    VOICES = json.load(f)


def get_model_name(voice_name):
    return voice_name.replace(" ", "_") + ".pt"


def check_files():
    files = os.listdir(DATA_FOLDER)

    for name, id in VOCODER_FILES.items():
        if name not in files:
            print(name+" It is not located on your computer.")
            #gdown.download(d+id, os.path.join(DATA_FOLDER, name), quiet=False)
    for name, id in VOICES.items():
        if name not in files:
            print(name+" It is not located on your computer.")
            #gdown.download(d+id, os.path.join(DATA_FOLDER, get_model_name(name)), quiet=False)
# Synthesis
os.makedirs(DATA_FOLDER, exist_ok=True)
os.makedirs(RESULTS_FOLDER, exist_ok=True)
inflect_engine = inflect.engine()
VOCODER = None
MODEL = Tacotron2()
MODEL_NAME = None


@app.route("/", methods=["GET"])
def index():
    global VOCODER, MODEL, MODEL_NAME
    check_files()
    gc.collect()

    if not VOCODER:
        VOCODER = Hifigan(os.path.join(DATA_FOLDER, HIFIGAN_MODEL), os.path.join(DATA_FOLDER, HIFIGAN_CONFIG))

    voice_name = request.args.get("name")
    if not voice_name:
        return jsonify({"error": "No name given"}), 400

    text = request.args.get("text")
    if not text:
        return jsonify({"error": "No text given"}), 400

    if MODEL_NAME != voice_name:
        model_path = os.path.join(DATA_FOLDER, get_model_name(voice_name))
        if not os.path.isfile(model_path):
            return jsonify({"error": "Voice not found"}), 400

        MODEL.load_state_dict(load(model_path, map_location=device("cpu"))["state_dict"])
        MODEL_NAME = voice_name
        
    id = str(uuid.uuid4())
    audio_path = os.path.join(RESULTS_FOLDER, f"{id}.wav")
    synthesize(MODEL, VOCODER, text, inflect_engine, audio_path)
    playsound("results/"+f"{id}.wav",False)
    with open(audio_path, "rb") as f:
        return send_file(io.BytesIO(f.read()), attachment_filename=audio_path, mimetype="audio/wav")


@app.route("/voices", methods=["GET"])
def available_voices():
    return jsonify({"voices": list(VOICES.keys())})
