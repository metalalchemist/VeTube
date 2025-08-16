import json

class EstadisticasManager:
    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(EstadisticasManager, cls).__new__(cls)
            cls._instance.usuarios = []
            cls._instance.mensajes_por_usuario = []
        return cls._instance

    def agregar_mensaje(self, autor):
        """
        Registra un mensaje de un autor. Si el autor es nuevo, lo agrega.
        Si ya existe, incrementa su contador de mensajes.
        """
        if autor not in self.usuarios:
            self.usuarios.append(autor)
            self.mensajes_por_usuario.append(1)
            # Línea de depuración para nuevos autores
        else:
            index = self.usuarios.index(autor)
            self.mensajes_por_usuario[index] += 1
            # Línea de depuración para autores existentes
            count = self.mensajes_por_usuario[index]

    def resetear_estadisticas(self):
        """Reinicia todas las estadísticas a cero."""
        self.usuarios = []
        self.mensajes_por_usuario = []

    def obtener_estadisticas(self):
        """Devuelve un diccionario con los datos sin ordenar."""
        return dict(zip(self.usuarios, self.mensajes_por_usuario))

    def obtener_estadisticas_ordenadas(self, descendente=True):
        """
        Devuelve una lista de tuplas (usuario, mensajes) ordenada por el número de mensajes.
        """
        stats = list(zip(self.usuarios, self.mensajes_por_usuario))
        # Ordenar la lista de tuplas. El segundo elemento (x[1]) es el número de mensajes.
        stats.sort(key=lambda x: x[1], reverse=descendente)
        return stats

    def guardar_en_archivo(self, file_path="data.json", ordenar=True):
        """
        Guarda las estadísticas en un archivo JSON.
        Por defecto, las guarda ordenadas de mayor a menor.
        """
        if ordenar:
            # El método de ordenación devuelve una lista de tuplas, ideal para JSON
            stats_ordenadas = self.obtener_estadisticas_ordenadas()
            # Convertimos la lista de tuplas a un diccionario para un formato JSON más legible
            stats_a_guardar = {usuario: mensajes for usuario, mensajes in stats_ordenadas}
        else:
            stats_a_guardar = self.obtener_estadisticas()

        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump(stats_a_guardar, f, ensure_ascii=False, indent=4)
        print(f"Estadísticas guardadas en {file_path}")
