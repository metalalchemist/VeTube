import json
def escribirConfiguracion():
	data={
		"sistemaTTS": "auto",
		'voz': 0,
		"tono": 0,
		"volume": 100,
		"speed": 0,
		'sapi':True,
		'sonidos': True,
		'idioma': "system",
		'categorias': [True, True, False, False, False],
		'listasonidos': [True, True, True, True, True, True, True, True, True,True,True],
		'reader': True,
		'donations': True,
		'updates': True
	}
	with open('data.json', 'w+') as file: json.dump(data, file)
def leerConfiguracion():
	with open ("data.json") as file: return json.load(file)