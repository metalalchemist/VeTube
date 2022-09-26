from flask import Flask
import os

# Flask
app = Flask(__name__)
DATA_FOLDER = "data"
RESULTS_FOLDER = "results"

from views import *

if __name__ == "__main__":
    app.run(debug=False)
