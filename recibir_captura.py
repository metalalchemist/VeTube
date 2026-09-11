"""Modo de prueba manual del firmador local: mirar qué manda la extensión.

Levanta el mismo servidor local que usa VeTube (servicios/tiktok_interceptor) y
va contando lo que llega. Sirve para cerrar la parte del navegador sin tener que
abrir VeTube entera: si acá se ven tramas y parsean, la mitad Python funciona.

Imprime SOLO la forma de lo que llega, nunca su contenido: cuántas tramas, de
qué tipo, si parsean y qué clases de evento traen. Ni los mensajes del chat, ni
los nombres de la gente, ni las cookies, ni la query firmada del websocket, que
es justo lo que no debe salir de la máquina. Tampoco guarda nada en disco.

Cómo ejecutarlo (desde la carpeta de VeTube, con su venv):

    cd "C:\\Users\\phaza\\cosas github\\VeTube"
    .venv\\Scripts\\python.exe recibir_captura.py

Dejalo corriendo, abrí el directo en el navegador con la extensión puesta y
escuchá lo que va imprimiendo. Ctrl+C para salir.

La salida es texto lineal, una cosa por línea, sin tablas ni barras de progreso:
está pensada para leerse con lector de pantalla.
"""

import os
import sys
import time
from collections import Counter
from urllib.parse import parse_qs, urlparse

# Permite ejecutarlo aunque no estés justo en la carpeta de VeTube.
RAIZ_VETUBE = os.path.dirname(os.path.abspath(__file__))
if RAIZ_VETUBE not in sys.path:
    sys.path.insert(0, RAIZ_VETUBE)

from TikTokLive.client.ws.ws_utils import extract_webcast_push_frame  # noqa: E402

from servicios.tiktok_espejo import decodificar_trama  # noqa: E402
from servicios.tiktok_interceptor import (  # noqa: E402
    VERSION_CONTRATO,
    ServidorInterceptor,
)

PUERTO = 8790
# Cada cuánto se resume lo acumulado. Un resumen por segundo sería ilegible con
# lector de pantalla; cada diez da tiempo a escucharlo entero.
CADA_S = 10


class Cuenta:
    """Lo que se sabe de una sesión sin mirar dentro de los mensajes."""

    def __init__(self):
        self.tramas = 0
        self.con_eventos = 0
        self.transporte = 0
        self.ilegibles = 0
        self.menor = None
        self.mayor = None
        self.tipos = Counter()
        self.eventos = Counter()

    def anotar(self, crudo):
        self.tramas += 1
        largo = len(crudo)
        self.menor = largo if self.menor is None else min(self.menor, largo)
        self.mayor = largo if self.mayor is None else max(self.mayor, largo)
        try:
            tipo = extract_webcast_push_frame(crudo).payload_type or "(sin tipo)"
        except Exception:
            tipo = "(no parsea)"
        self.tipos[tipo] += 1

        respuesta = decodificar_trama(crudo)
        if respuesta is None:
            # Sin eventos: o es transporte (hb, ack) o la trama vino rota.
            if tipo == "msg":
                self.ilegibles += 1
            else:
                self.transporte += 1
            return
        self.con_eventos += 1
        for mensaje in respuesta.messages:
            # El nombre de la clase de evento es del protocolo, no del usuario.
            self.eventos[mensaje.method or "(sin nombre)"] += 1

    def lineas(self):
        yield (
            f"  tramas: {self.tramas}, con eventos: {self.con_eventos}, "
            f"de transporte: {self.transporte}, ilegibles: {self.ilegibles}."
        )
        if self.menor is not None:
            yield f"  tamaños: de {self.menor} a {self.mayor} bytes."
        if self.tipos:
            yield "  tipos de trama: " + ", ".join(
                f"{t} {n}" for t, n in sorted(self.tipos.items())
            ) + "."
        if self.eventos:
            yield "  eventos vistos: " + ", ".join(
                f"{e} {n}" for e, n in self.eventos.most_common(8)
            ) + "."
        else:
            yield "  eventos vistos: ninguno todavía."


def contar_captura(captura):
    """La forma de una captura de la ruta A. Nunca su firma ni sus cookies."""
    partes = urlparse(captura.ws_url)
    parametros = sorted(parse_qs(partes.query))
    print()
    print("Captura de URL firmada recibida (ruta A):")
    print(f"  usuario: @{captura.unique_id or '(sin nombre)'}, sala: {captura.room_id}.")
    print(f"  host del websocket: {partes.hostname}.")
    print(f"  ruta: {partes.path}.")
    print(f"  ¿es el webcast?: {'webcast-ws.tiktok.com' in (partes.hostname or '')}.")
    print(f"  parámetros de la query: {len(parametros)}.")
    print("  nombres de los parámetros: " + (", ".join(parametros) or "ninguno") + ".")
    print("  nombres de las cookies: " + (", ".join(sorted(captura.cookies)) or "ninguna") + ".")
    print(f"  largo de la URL: {len(captura.ws_url)} caracteres (no se imprime).")


def main():
    # Puerto por argumento por si el 8790 ya lo tiene otra cosa (VeTube abierta,
    # u otra copia de este mismo receptor): el arranque falla claro, no en silencio.
    puerto = int(sys.argv[1]) if len(sys.argv) > 1 else PUERTO
    try:
        servidor = ServidorInterceptor(puerto=puerto)
    except OSError as e:
        print(f"No se pudo abrir el puerto {puerto}: {e}.")
        print("¿Hay otra copia de VeTube o de este receptor abierta?")
        print("Se puede probar en otro puerto, por ejemplo: recibir_captura.py 8791.")
        return
    servidor.iniciar()
    print(f"Receptor listo en http://127.0.0.1:{puerto}, contrato versión {VERSION_CONTRATO}.")
    print("Abrí el directo en el navegador con la extensión puesta.")
    print(f"Se resume lo que llegue cada {CADA_S} segundos. Ctrl+C para salir.")

    cuentas = {}
    capturas_vistas = set()
    estados_vistos = {}
    arranque = time.time()
    proximo_resumen = arranque + CADA_S

    try:
        while True:
            for captura in list(servidor.almacen._por_usuario.values()):
                if captura.ws_url in capturas_vistas:
                    continue
                capturas_vistas.add(captura.ws_url)
                contar_captura(captura)

            for sesion in list(servidor.sesiones._por_usuario.values()):
                nombre = sesion.unique_id or "(sin nombre)"
                if estados_vistos.get(nombre) != sesion.estado:
                    estados_vistos[nombre] = sesion.estado
                    print()
                    print(
                        f"El navegador dice que el directo de @{nombre} está "
                        f"{sesion.estado}. Sala: {sesion.room_id or 'sin informar'}. "
                        f"Host: {sesion.host_ws or 'sin informar'}."
                    )
                cuenta = cuentas.setdefault(nombre, Cuenta())
                # Se vacía la cola porque acá no hay ninguna VeTube esperándola.
                while True:
                    crudo = sesion.cola.siguiente(0.05)
                    if not isinstance(crudo, (bytes, bytearray)):
                        break  # SIN_TRAMA o el centinela de cierre
                    cuenta.anotar(bytes(crudo))

            if time.time() >= proximo_resumen:
                proximo_resumen = time.time() + CADA_S
                segundos = int(time.time() - arranque)
                if not cuentas:
                    print()
                    print(f"A los {segundos} segundos todavía no llegó nada.")
                for nombre, cuenta in cuentas.items():
                    sesion = servidor.sesiones.obtener(nombre)
                    print()
                    print(f"Resumen de @{nombre} a los {segundos} segundos:")
                    for linea in cuenta.lineas():
                        print(linea)
                    if sesion is not None:
                        print(
                            f"  huecos de secuencia: {sesion.huecos}. "
                            f"Descartadas por cola llena: {sesion.cola.descartadas}."
                        )
            time.sleep(0.2)
    except KeyboardInterrupt:
        print()
        print("Cerrando el receptor.")
        servidor.detener()


if __name__ == "__main__":
    main()
