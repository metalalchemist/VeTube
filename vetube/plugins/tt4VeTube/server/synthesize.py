from torch import autograd, from_numpy
import numpy as np
from scipy.io.wavfile import write

from clean_text import clean_text


SYMBOLS = "_-!¡\'(),.:;?¿ áàãâéêíîñóõôúüûçÇTUVWXYZabcdefghijklmnopqrstuvwxyz"
SYMBOL_TO_ID = {s: i for i, s in enumerate(SYMBOLS)}
SAMPLE_RATE = 22050


def text_to_sequence(text):
    sequence = np.array([[SYMBOL_TO_ID[s] for s in text if s in SYMBOL_TO_ID]])
    return autograd.Variable(from_numpy(sequence)).cpu().long()


def synthesize(model, vocoder, text, inflect_engine, audio_path):
    text = clean_text(text, inflect_engine)
    sequence = text_to_sequence(text)
    _, mel_outputs_postnet, _, _ = model.inference(sequence)
    audio = vocoder.generate_audio(mel_outputs_postnet)
    write(audio_path, SAMPLE_RATE, audio)
