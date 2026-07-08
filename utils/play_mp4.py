import yt_dlp

def extract_stream_url(youtube_url, format_preference='mp4'):
    """
    Usa yt-dlp para obtener la URL directa del stream.
    Devuelve la URL del stream o None si hay un error.
    """
    try:
        # Para directos, 'best' o 'bestaudio' suele resolver a un stream m3u8.
        # Para videos pasados, 'mp4' funciona como ya vimos.
        ydl_opts = {
            'format': format_preference,
            'quiet': True,
        }
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(youtube_url, download=False)
            return info.get('url')
    except Exception as e:
        print(f"Error al extraer la URL con yt-dlp: {e}")
        return None

def extract_live_viewers(url):
    """
    Usa yt-dlp para obtener la cantidad de espectadores concurrentes de un en vivo.
    Devuelve el número de espectadores (int) o None si no está disponible.
    """
    try:
        ydl_opts = {
            'quiet': True,
            'no_warnings': True,
            'skip_download': True,
        }
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=False)
            return info.get('concurrent_view_count')
    except Exception as e:
        print(f"Error al extraer espectadores con yt-dlp: {e}")
        return None