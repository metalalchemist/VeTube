import json

configuraciones ={
	"salir": True,
	"sistemaTTS": "auto",
	'voz': 0,
	"tono": 0,
	"volume": 100,
	"speed": 0,
	'sapi':True,
	'dispositivo': 1,
	'sonidos': True,
	'idioma': "system",
	'categorias': [True,True,True, True, False, False, False],
	'listasonidos': [True, True, True, True, True, True, True, True,True,True,True,True,True],
	'eventos': [True,True,True,True,True,True,True,True,True,True],
	'unread': [True,True,True,True,True,True,True,True,True,True],
	'reader': True,
	'donations': True,
	'updates': True,
	'traducir': False,
	'directorio':'default'
}
actualizar_configuracion = False

def escribirConfiguracion():
	global configuraciones
	with open('data.json', 'w+') as file:
		json.dump(configuraciones, file, indent=4)

def leerConfiguracion():
	global configuraciones, actualizar_configuracion
	with open ("data.json") as file:
		configs = json.load(file)
	for clave, valor_pred in configuraciones.items():
		if clave not in configs:
			configs[clave] = valor_pred
			actualizar_configuracion = True
	# actualizar al archivo en caso de ser necesario:
	if actualizar_configuracion:
		with open('data.json', 'w+') as file:
			json.dump(configs, file, indent=4)
	return configs