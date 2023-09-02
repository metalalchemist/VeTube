import  json
from urllib.parse import urlsplit
from os import  path
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