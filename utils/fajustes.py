import json

configuraciones ={
	"salir": True,
	"sistemaTTS": "auto",
	'voz': 0,
	"tono": 0,
	'tono_onecore': 0,
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
	'directorio':'default',
	'reproducir': False,
	'tiempo': 10,
	'volumen': 100,
	"cambiovolumen": 10,
	'interface': False,
	'discord_token': "",
	'idioma_traduccion': "",
	'leer_historial': True

}
actualizar_configuracion = False

def escribirConfiguracion():
	global configuraciones
	with open('data.json', 'w+') as file:
		json.dump(configuraciones, file, indent=4)

def guardarConfiguracion(configs):
	"""Guarda en data.json la configuración actual (no los valores por defecto)."""
	with open('data.json', 'w+', encoding='utf-8') as file:
		json.dump(configs, file, indent=4, ensure_ascii=False)

def leerConfiguracion():
	global configuraciones, actualizar_configuracion
	with open ("data.json") as file:
		configs = json.load(file)
	for clave, valor_pred in configuraciones.items():
		if clave not in configs:
			configs[clave] = valor_pred
			actualizar_configuracion = True
		elif isinstance(valor_pred, list) and isinstance(configs[clave], list) and len(configs[clave]) < len(valor_pred):
			# Completar listas que crecieron en versiones nuevas, conservando las preferencias existentes (evita IndexError)
			configs[clave] = configs[clave] + valor_pred[len(configs[clave]):]
			actualizar_configuracion = True
	# actualizar al archivo en caso de ser necesario:
	if actualizar_configuracion:
		with open('data.json', 'w+') as file:
			json.dump(configs, file, indent=4)
	return configs