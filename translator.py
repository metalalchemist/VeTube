from googletrans import Translator

class TranslatorWrapper:
    def __init__(self):
        self.translator = Translator()

    def translate(self, text="", target="en"):
        return self.translator.translate(text, dest=target).text

    @property
    def LANGUAGES(self):
        return LANGUAGES
