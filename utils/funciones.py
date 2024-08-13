import  json
from . import fajustes
from urllib.parse import urlsplit
from os import  path
def retornarCategorias():
	config=fajustes.leerConfiguracion()
	categorias = [
		"Mensajes", "Miembros", "Donativos", "Moderadores", "Usuarios Verificados", "Favoritos"
	]
	lista = [[categoria] for i, categoria in enumerate(categorias) if i < len(config['categorias']) and config['categorias'][i]]
	lista.insert(0,['General'])
	return lista
def escribirJsonLista(arch,lista=[]):
	with open(arch, 'w+') as file: json.dump(lista, file)
def leerJsonLista(arch):
	if path.exists(arch):
		with open (arch) as file: return json.load(file)
	else: return []
def convertirLista(lista, val1, val2):
	if len(lista)<=0: return []
	else:
		newlista=[]
		for datos in lista: newlista.append(datos[val1]+': '+datos[val2])
		return newlista
def extract_urls(text):
	urls = []
	words = text.split()
	for word in words:
		parts = urlsplit(word)
		if parts.scheme and parts.netloc: urls.append(parts.geturl())
	return urls
def extractUser(url):
	start_index = url.find('@')
	end_index = url.find('/', start_index)
	if start_index == -1: 
		start_index = url.find('tv/')
		if start_index != -1: 
			start_index+=3
			end_index = url.find('/', start_index)
	return url[start_index:end_index] if end_index != -1 else url[start_index:]