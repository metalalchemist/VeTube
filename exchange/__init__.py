import os
import json
import time
from globals import data_store
from utils.network import network_manager

class Exchange:
    def __init__(self):
        self.base_currency = data_store.divisa
        self.rates = {}
        self.cache_dir = "divisas"
        self.cache_file = ""
        
        if not os.path.exists(self.cache_dir):
            try:
                os.makedirs(self.cache_dir)
            except Exception as e:
                print(f"Error al crear carpeta de divisas: {e}")
            
        if self.base_currency and self.base_currency != "Por defecto":
            # Si el formato es "Nombre (USD)", extraemos USD. Si ya es "USD", se mantiene.
            if "(" in self.base_currency and ")" in self.base_currency:
                self.base_currency = self.base_currency.split("(")[1].split(")")[0]
            
            self.cache_file = os.path.join(self.cache_dir, f"{self.base_currency}.json")
            self._initialize()

    def _initialize(self):
        if os.path.exists(self.cache_file):
            file_age = time.time() - os.path.getmtime(self.cache_file)
            if file_age < 86400: # 24 horas
                try:
                    with open(self.cache_file, 'r', encoding='utf-8') as f:
                        data = json.load(f)
                        self.rates = data.get('rates', {})
                    if self.rates:
                        return
                except Exception:
                    pass
            else:
                try:
                    os.remove(self.cache_file)
                except:
                    pass
        
        # Descarga asíncrona usando el network_manager del proyecto
        network_manager.execute(self._download_rates())

    async def _download_rates(self):
        url = f"https://open.er-api.com/v6/latest/{self.base_currency}"
        try:
            response = await network_manager.client.get(url)
            if response.status_code == 200:
                data = response.json()
                self.rates = data.get('rates', {})
                with open(self.cache_file, 'w', encoding='utf-8') as f:
                    json.dump(data, f)
            else:
                print(f"Error API Divisas: Código de estado {response.status_code}")
        except Exception as e:
            print(f"Error descargando divisas: {e}")

    def convert(self, amount, from_currency):
        """
        Convierte una cantidad desde 'from_currency' a la moneda base del usuario.
        Ejemplo: Si el usuario usa USD y llama convert(4000, 'COP'), 
        retornará el valor en USD.
        """
        if not self.rates:
            return amount
        
        from_currency = from_currency.upper()
        
        # Si la moneda de origen es la misma que la base, no hay conversión
        if from_currency == self.base_currency:
            return amount

        rate = self.rates.get(from_currency)
        if rate:
            # La API de Open ER da los ratios relativos a la base:
            # 1 unidad de base_currency = X unidades de from_currency
            return round(amount / rate, 2)
        
        return amount

    def from_usd(self, usd_amount):
        """Convierte una cantidad de USD a la moneda local del usuario."""
        return self.convert(usd_amount, "USD")

    def from_diamonds(self, count):
        """Convierte diamantes de TikTok (100 = 1 USD) a la moneda local."""
        return self.from_usd(count / 100)

    def from_bits(self, count):
        """Convierte bits de Twitch (100 = 1 USD) a la moneda local."""
        return self.from_usd(count / 100)

# Instancia por defecto para facilitar el acceso
exchange = Exchange()
