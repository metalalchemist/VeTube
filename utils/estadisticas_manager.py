import json

class EstadisticasManager:
    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(EstadisticasManager, cls).__new__(cls)
            cls._instance.usuarios = []
            cls._instance.mensajes_por_usuario = []
            cls._instance.unidos = 0
            cls._instance.seguidores = 0
            cls._instance.megusta = 0
            cls._instance.compartidas = 0
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

    def agregar_unido(self):
        self.unidos += 1

    def agregar_seguidor(self):
        self.seguidores += 1

    def actualizar_megusta(self, total_likes):
        self.megusta = total_likes

    def agregar_compartida(self):
        self.compartidas += 1

    def resetear_estadisticas(self):
        """Reinicia todas las estadísticas a cero."""
        self.usuarios = []
        self.mensajes_por_usuario = []
        self.unidos = 0
        self.seguidores = 0
        self.megusta = 0
        self.compartidas = 0

    def obtener_estadisticas(self):
        """Devuelve un diccionario con los datos sin ordenar."""
        return dict(zip(self.usuarios, self.mensajes_por_usuario))

    def obtener_estadisticas_tiktok(self):
        return {
            "unidos": self.unidos,
            "seguidores": self.seguidores,
            "megusta": self.megusta,
            "compartidas": self.compartidas
        }

    def obtener_estadisticas_ordenadas(self, descendente=True):
        """
        Devuelve una lista de tuplas (usuario, mensajes) ordenada por el número de mensajes.
        """
        stats = list(zip(self.usuarios, self.mensajes_por_usuario))
        # Ordenar la lista de tuplas. El segundo elemento (x[1]) es el número de mensajes.
        stats.sort(key=lambda x: x[1], reverse=descendente)
        return stats

    def guardar_en_archivo(self, file_path="data.json", ordenar=True, plataforma=None):
        """
        Guarda las estadísticas en un archivo JSON.
        Si la plataforma es TikTok, añade estadísticas adicionales.
        Por defecto, las guarda ordenadas de mayor a menor.
        """
        if ordenar:
            stats_ordenadas = self.obtener_estadisticas_ordenadas()
            stats_a_guardar = {"usuarios": {usuario: mensajes for usuario, mensajes in stats_ordenadas}}
        else:
            stats_a_guardar = {"usuarios": self.obtener_estadisticas()}

        if plataforma and plataforma.lower() == 'tiktok':
            tiktok_stats = self.obtener_estadisticas_tiktok()
            # Filtramos las estadísticas de TikTok para no guardar las que son 0
            tiktok_stats_filtradas = {k: v for k, v in tiktok_stats.items() if v > 0}
            if tiktok_stats_filtradas:
                stats_a_guardar['tiktok'] = tiktok_stats_filtradas

        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump(stats_a_guardar, f, ensure_ascii=False, indent=4)
        print(f"Estadísticas guardadas en {file_path}")


    def total_mensajes(self):
        """Devuelve el número total de mensajes."""
        return sum(self.mensajes_por_usuario)

    def total_usuarios(self):
        """Devuelve el número total de usuarios únicos."""
        return len(self.usuarios)