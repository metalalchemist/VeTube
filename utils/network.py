import asyncio
import threading
import httpx
import wx

class NetworkManager:
    def __init__(self):
        self.loop = asyncio.new_event_loop()
        # Cliente centralizado con la configuración pactada
        self.client = httpx.AsyncClient(
            follow_redirects=False, 
            timeout=None,
            headers={'User-Agent': 'VeTube/3.6 (Universal Network Client)'}
        )
        # El único hilo "motor" de la aplicación
        self.thread = threading.Thread(target=self._run_loop, daemon=True)
        self.thread.start()

    def _run_loop(self):
        asyncio.set_event_loop(self.loop)
        self.loop.run_forever()

    def execute(self, coro, callback=None):
        """
        Envía una tarea (corrutina) al motor asíncrono.
        Si se proporciona un callback, se ejecutará en el hilo de la UI (wx)
        con el resultado de la tarea.
        """
        async def wrapped_coro():
            try:
                resultado = await coro
                if callback:
                    wx.CallAfter(callback, resultado)
            except Exception as e:
                if callback:
                    wx.CallAfter(callback, e)
                else:
                    print(f"Error en tarea asíncrona: {e}")
        
        return asyncio.run_coroutine_threadsafe(wrapped_coro(), self.loop)

    async def close(self):
        """Cierra el cliente y detiene el bucle."""
        await self.client.aclose()
        self.loop.stop()

# Instancia única para ser importada
network_manager = NetworkManager()
