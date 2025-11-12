mensaje_teclas=[
	_('iniciar/cancelar la captura de otro en vivo'),
	_('Silencia la voz sapy'),
	_('Mensaje anterior.'),
	_('Mensaje siguiente'),
	_('Buffer anterior'),
	_('Siguiente Buffer'),
	_('Ir al comienzo del buffer'),
	_('Ir al final del buffer'),
	_('Destaca un mensaje en el buffer de  favoritos'),
	_('Copia el mensaje actual'),
	_('Activa o desactiva la lectura automática'),
	_('Busca una palabra en los mensajes actuales'),
	_('Muestra el mensaje actual en un cuadro de texto'),
	_('borra el buffer seleccionado'),
	_('activa o desactiva los sonidos del programa'),
	_('Invocar el editor de combinaciones de teclado'),
	_('Archivar un mensaje'),
	_('Pausar o reanudar el reproductor'),
	_('Adelantar la reproducción'),
	_('Atrasar la reproducción'),
	_('Sube el volumen del reproductor'),
	_('Baja el volumen del reproductor'),
	_('Detener y liberar el reproductor'),
	_('ir al Siguiente en vivo'),
	_('ir al en vivo anterior')
]

mensajes_categorias = [
    _('Mensajes'), _('eventos'), _('Miembros'), _('Donativos'), _('Moderadores'),
    _('Usuarios Verificados'), _('Favoritos')
]

mensajes_sonidos = [
    _('Sonido cuando llega un mensaje'),
    _('Sonido cuando habla un miembro'),
    _('Sonido cuando se conecta un miembro o cuando alguien se une a tu en vivo en tiktok'),
    _('Sonido cuando llega un donativo'),
    _('Sonido cuando habla un moderador'),
    _('Sonido cuando habla un usuario verificado'),
    _('Sonido al ingresar al chat'),
    _('Sonido cuando habla el propietario del canal'),
    _('sonido al terminar la búsqueda de mensajes'),
    _('sonido cuando le dan me gusta al en vivo (solo para tiktok)'),
    _('Sonido cuando alguien empieza a seguirte en tiktok'),
    _('Sonido cuando alguien comparte el enlace de tu envivo en  tiktok'),
    _('Sonido cuando alguien envía un cofre  en tiktok')
]

eventos_lista = [
    _('Cuando llega un mensaje'),
    _('Cuando habla un miembro'),
    _('Cuando se conecta un miembro o cuando alguien se une a tu en vivo en tiktok'),
    _('Cuando llega un donativo'),
    _('Cuando habla un moderador'),
    _('Cuando habla un usuario verificado'),
    _('Cuando le dan me gusta al en vivo (solo para tiktok)'),
    _('Cuando alguien empieza a seguirte en tiktok'),
    _('Cuando alguien comparte el enlace de tu envivo en  tiktok'),
    _('Cuando alguien envía un cofre  en tiktok')
]

comandos_ordenados = [
    'chat_dialog.toggle_chat_window_visibility',
    'reader._leer.silence',
    'chat.elementoAnterior',
    'chat.elementoSiguiente',
    'chat.retrocederCategorias',
    'chat.avanzarCategorias',
    'chat.elemento_inicial',
    'chat.elemento_final',
    'chat.agregar_mensajes_favoritos',
    'chat.copiarMensajeActual',
    'chat.toggle_lectura_automatica',
    'chat.buscar_mensajes',
    'chat.mostrar_mensaje_actual',
    'chat.borrar_pagina_actual',
    'chat.toggle_sounds',
    'chat.mostrar_editor_combinaciones',
    'chat.archivar_mensaje',
    'chat_dialog.toggle_global_media_pause',
    'media_player.adelantar',
    'media_player.atrasar',
    'media_player.volume_up',
    'media_player.volume_down',
    'media_player.release',
    'chat_dialog.next_session',
    'chat_dialog.previous_session'
]

comandos_a_descripcion = dict(zip(comandos_ordenados, mensaje_teclas))