# -*- coding: utf-8 -*-
from googletrans import Translator, LANGUAGES


# create a single translator instance
# see https://github.com/ssut/py-googletrans/issues/234
t = None

def translate(text="", target="en"):
    global t
    if t == None:
        t = Translator()
    vars = dict(text=text, dest=target)
    return t.translate(**vars).text