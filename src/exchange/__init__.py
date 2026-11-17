import json
import os
import threading
import time
from logging import getLogger

from globals import data_store
from utils.network import network_manager

logger = getLogger(__name__)


class Exchange:
    # open.er-api.com es la fuente principal. Si falla (error de red, codigo != 200
    # o respuesta sin tasas), se intenta AllRatesToday, que devuelve el mismo formato
    # JSON (tasas de referencia del BCE, ~30 divisas). Si una divisa no esta en la
    # respuesta, convert() devuelve None y la donación se anuncia tal como llegó.
    RATE_SOURCES = (
        "https://open.er-api.com/v6/latest/{base}",
        "https://allratestoday.com/api/open/latest/{base}",
    )
    # El cliente compartido no tiene tiempo de espera: sin este, una fuente que
    # acepta la conexión y no contesta dejaría la descarga colgada para siempre y
    # la de respaldo no se intentaría nunca.
    TIMEOUT = 15

    def __init__(self):
        self.cache_dir = "divisas"
        # La divisa del usuario y sus tasas van SIEMPRE juntas en una sola tupla:
        # quien convierte las lee de una vez y nunca mezcla las tasas de una divisa
        # con el nombre de otra (los ajustes la cambian desde otro hilo).
        self._tabla = (None, {})
        self._candado = threading.Lock()

        if not os.path.exists(self.cache_dir):
            try:
                os.makedirs(self.cache_dir)
            except Exception as e:
                logger.warning("No se pudo crear la carpeta de divisas: %s", e)

        self.set_base_currency(data_store.divisa)

    @property
    def base_currency(self):
        """Código de la divisa a la que se convierte, o None si no se convierte."""
        return self._tabla[0]

    @property
    def rates(self):
        """Tasas cargadas para base_currency (vacío mientras no llegan)."""
        return self._tabla[1]

    def set_base_currency(self, divisa):
        """
        Elige la divisa a la que se convierten las donaciones y carga sus tasas.

        Hay que llamarla cada vez que el usuario cambia la divisa en los ajustes:
        este objeto nace al importar el módulo, cuando todavía no hay ninguna
        elegida, y sin este aviso no cargaría nunca las tasas. «Por defecto» (o
        nada) significa no convertir. La caché se lee en el acto; la descarga, si
        hace falta, va por el hilo de red.
        """
        base = None
        if divisa and divisa != "Por defecto":
            # Si el formato es "Nombre (USD)", extraemos USD. Si ya es "USD", se mantiene.
            if "(" in divisa and ")" in divisa:
                divisa = divisa.split("(")[1].split(")")[0]
            base = divisa.strip().upper()

        with self._candado:
            actual, tasas = self._tabla
            if base == actual and (tasas or base is None):
                return
            # Sin tasas hasta que lleguen las de la nueva divisa: mientras tanto
            # convert() devuelve None y las donaciones se anuncian sin convertir.
            self._tabla = (base, {})
        if base is None:
            return

        tasas = self._read_cache(base)
        if tasas:
            self._set_rates(base, tasas)
        else:
            # Descarga asíncrona usando el network_manager del proyecto
            network_manager.execute(self._download_rates(base))

    def _set_rates(self, base, rates):
        """Publica las tasas solo si `base` sigue siendo la divisa elegida."""
        with self._candado:
            if self._tabla[0] == base:
                self._tabla = (base, rates)

    def _cache_file(self, base):
        return os.path.join(self.cache_dir, f"{base}.json")

    def _read_cache(self, base):
        cache_file = self._cache_file(base)
        if not os.path.exists(cache_file):
            return {}
        if time.time() - os.path.getmtime(cache_file) >= 86400:  # 24 horas
            try:
                os.remove(cache_file)
            except OSError:
                pass
            return {}
        try:
            with open(cache_file, "r", encoding="utf-8") as f:
                return self._valid_rates(json.load(f), base)
        except Exception:
            return {}

    @staticmethod
    def _valid_rates(data, base):
        """
        Las tasas utilizables de una respuesta, o {} si no es de fiar.

        Tiene que ser una tabla relativa a la divisa pedida (base -> 1, como la
        dan las dos fuentes): con una tabla en otra base las cantidades saldrían
        falsas sin ningún error.
        """
        rates = data.get("rates") if isinstance(data, dict) else None
        if not isinstance(rates, dict) or rates.get(base) != 1:
            return {}
        return {
            codigo: tasa
            for codigo, tasa in rates.items()
            if isinstance(tasa, (int, float)) and tasa > 0
        }

    async def _download_rates(self, base):
        for template in self.RATE_SOURCES:
            url = template.format(base=base)
            try:
                response = await network_manager.client.get(url, timeout=self.TIMEOUT)
                if response.status_code != 200:
                    logger.warning(
                        "Divisas: %s respondió con el código %s",
                        url,
                        response.status_code,
                    )
                    continue
                data = response.json()
                rates = self._valid_rates(data, base)
                if not rates:
                    logger.warning("Divisas: respuesta sin tasas válidas de %s", url)
                    continue
            except Exception as e:
                logger.warning("Divisas: error al descargar de %s: %s", url, e)
                continue

            self._set_rates(base, rates)
            logger.info("Divisas: %d tasas para %s desde %s", len(rates), base, url)
            # La caché es solo un ahorro: si no se puede escribir, las tasas ya
            # están en memoria y no hay que pasar a la fuente de respaldo.
            try:
                with open(self._cache_file(base), "w", encoding="utf-8") as f:
                    json.dump(data, f)
            except OSError as e:
                logger.warning(
                    "Divisas: no se pudo guardar la caché de %s: %s", base, e
                )
            return

        logger.warning(
            "Divisas: ninguna fuente dio tasas para %s; las donaciones se anuncian "
            "sin convertir",
            base,
        )

    def convert(self, amount, from_currency):
        """
        Convierte una cantidad desde 'from_currency' a la divisa del usuario.

        Devuelve (cantidad, divisa), listo para anunciar, o None si no se puede
        convertir: ninguna divisa elegida, tasas sin cargar o divisa de origen
        desconocida. Con None hay que anunciar la donación tal como llegó:
        ponerle la divisa del usuario a una cantidad sin convertir es dar un
        importe falso.
        Ejemplo: con USD elegido, convert(4000, 'COP') devuelve (1.22, 'USD').
        """
        base, rates = self._tabla
        # Nunca una excepción: aquí se llega desde el bucle que recibe el chat, y
        # un error en una donación rara lo cortaría entero.
        if (
            base is None
            or not isinstance(from_currency, str)
            or not isinstance(amount, (int, float))
        ):
            return None

        from_currency = from_currency.strip().upper()

        # Si la moneda de origen es la misma que la base, no hay conversión
        if from_currency == base:
            return amount, base

        rate = rates.get(from_currency)
        if not rate:
            return None

        # La API de Open ER da los ratios relativos a la base:
        # 1 unidad de base_currency = X unidades de from_currency
        return round(amount / rate, 2), base

    def from_usd(self, usd_amount):
        """Convierte una cantidad de USD a la divisa del usuario (ver convert)."""
        return self.convert(usd_amount, "USD")

    def from_diamonds(self, count):
        """Convierte diamantes de TikTok (100 = 1 USD) a la divisa del usuario."""
        return self.from_usd(count / 100)

    def from_bits(self, count):
        """Convierte bits de Twitch (100 = 1 USD) a la divisa del usuario."""
        return self.from_usd(count / 100)


# Instancia por defecto para facilitar el acceso
exchange = Exchange()
