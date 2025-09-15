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
