# Voice-API
Voice service API available at https://voice-cloning-api.herokuapp.com/

## Setup
1. Clone this repository
2. Install [Python3](https://www.python.org/)
3. Run `pip install -r requirements.txt`
4. Create a folder called `data` inside the repo
5. Add each voice model to the `data` folder in the format `firstname_lastname.pt` (i.e. David_Attenborough.pt)

## Request Format
Make a GET request to the root URL with the name of the voice & given text to synthesise.
For example: `https://voice-cloning-api.herokuapp.com/?name=David Attenborough&text=Some sample text`

This returns a JSON response with the URL for the generated audio and graph.
For example: `{"audio":"results/1234.wav","graph":"results/1234.png"}`

These can then be fetched from the given URLS.
i.e.  `https://voice-cloning-api.herokuapp.com/results/1234.wav`

## Voice list
The list of available voices can be fetched from `https://voice-cloning-api.herokuapp.com/voices`
