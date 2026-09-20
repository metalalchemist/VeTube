import wx

from . import utils
from .channel import get_channel, set_channel

# Una sola barra de progreso para toda la actualización (descarga, copia de
# seguridad, extracción): mientras exista, VeTube sigue siendo el programa en
# primer plano aunque sus ventanas estén escondidas, y el aviso final, que la
# tiene como madre, sale delante y el lector de pantalla lo lee. Si se
# destruyera entre fase y fase, Windows pasaría el primer plano a otro
# programa y los diálogos siguientes saldrían detrás (medido en el banc
# banc_updater_dialogos.py).
progress_dialog = None
_ventanas_ocultas: list = []
# La ventana que tenía el foco al empezar: vuelve al frente si la
# actualización falla, y es la dueña del aviso de fallo (al cerrarlo, el foco
# vuelve a ella y no a la ventana principal).
_ventana_activa = None
# Cuántas llamadas a ProgressDialog.Update() están en curso (anidadas, véase
# _actualizar_barra).
_updates_en_curso = 0


def _nombre_canal() -> str:
    """El canal, traducido y con la misma redacción que los botones del diálogo.

    get_channel() devuelve «stable» o «beta», en inglés y en minúsculas, y se
    estaba colando tal cual dentro de frases ya traducidas: «Ya tienes la
    última versión (v3.95), canal Stable», «канал Stable». Se reutilizan los
    mismos msgid que los botones de arriba, así que no hace falta traducir
    nada nuevo.
    """
    return _("Estable") if get_channel() == "stable" else _("Beta")


def channel_selection_dialog() -> bool:
    """Show a dialog for selecting the update channel (stable or beta).

    Returns:
        True if the user clicked OK, False if cancelled.
    """
    current = get_channel()

    dlg = wx.Dialog(None, title=_("Canal de actualizaciones"), size=(420, 260))
    vbox = wx.BoxSizer(wx.VERTICAL)

    header = wx.StaticText(dlg, label=_("Elige qué actualizaciones quieres recibir:"))
    header.SetFont(header.GetFont().Bold())
    vbox.Add(header, 0, wx.ALL | wx.EXPAND, 12)

    radio_stable = wx.RadioButton(dlg, label=_("Estable"), style=wx.RB_GROUP)
    vbox.Add(radio_stable, 0, wx.LEFT | wx.RIGHT, 24)
    desc_stable = wx.StaticText(
        dlg, label=_("Solo versiones oficiales. Lo recomendado para la mayoría.")
    )
    desc_stable.SetForegroundColour(wx.Colour(100, 100, 100))
    vbox.Add(desc_stable, 0, wx.LEFT | wx.BOTTOM, 24)

    radio_beta = wx.RadioButton(dlg, label=_("Beta"))
    vbox.Add(radio_beta, 0, wx.LEFT | wx.RIGHT, 24)
    desc_beta = wx.StaticText(
        dlg,
        label=_(
            "Incluye versiones previas y novedades tempranas. Puede ser inestable."
        ),
    )
    desc_beta.SetForegroundColour(wx.Colour(100, 100, 100))
    vbox.Add(desc_beta, 0, wx.LEFT | wx.BOTTOM, 24)

    if current == "beta":
        radio_beta.SetValue(True)
    else:
        radio_stable.SetValue(True)

    btn_sizer = dlg.CreateButtonSizer(wx.OK | wx.CANCEL)
    vbox.Add(btn_sizer, 0, wx.ALL | wx.ALIGN_CENTER, 12)

    dlg.SetSizer(vbox)

    if dlg.ShowModal() == wx.ID_OK:
        chosen = "beta" if radio_beta.GetValue() else "stable"
        set_channel(chosen)
        dlg.Destroy()
        return True

    dlg.Destroy()
    return False


def backup_progress_callback(current: int, total: int) -> None:
    """Muestra el avance de la copia de seguridad en la barra de la actualización.

    Args:
        current: Number of files processed so far.
        total: Total number of files to back up.
    """

    def _update():
        # El texto dice lo mismo que la barra (que nunca llega a 100).
        pct = min(int((current * 100) / max(total, 1)), 99)
        _actualizar_barra(pct, _("Creando la copia de seguridad... %d%%") % pct)

    wx.CallAfter(_update)


def rollback_notification(reason: str) -> None:
    """Avisa de que la actualización no se completó y VeTube sigue como estaba.

    Todo lo que falla en el proceso de VeTube (descarga, verificación, copia
    de seguridad, extracción, arranque del bootstrap) pasa antes de tocar la
    instalación, así que no hay «vuelta atrás»: la versión de siempre sigue
    ahí. El mensaje antiguo prometía un retorno que nunca ocurría.

    En el hilo de la interfaz (updater.py lo pide por _en_interfaz, DESPUÉS de
    mostrar_ventanas, para que el orden sea siempre ventanas → aviso).

    Args:
        reason: Description of why the update failed.
    """
    wx.MessageDialog(
        _ventana_activa if _ventana_activa else None,  # destruida = False
        _(
            "La actualización no se ha podido completar: %s\n\n"
            "VeTube sigue en la versión de siempre y tus datos están a salvo."
        )
        % reason,
        _("Error de actualización"),
        style=wx.OK | wx.ICON_WARNING,
    ).ShowModal()


def checking_updates_dialog() -> wx.ProgressDialog:
    """Create and show an indeterminate progress dialog for update checks.

    Returns:
        The dialog instance. Caller must call ``Destroy()`` when done.
    """
    dlg = wx.ProgressDialog(
        _("Comprobando actualizaciones"),
        _("Conectando con el servidor de actualizaciones..."),
        parent=None,
        style=wx.PD_APP_MODAL | wx.PD_AUTO_HIDE,
    )
    dlg.Pulse()
    dlg.Show()
    return dlg


def no_updates_dialog(version: str) -> None:
    """Inform the user they are running the latest version.

    Args:
        version: The current version string.
    """

    def _show():
        ch = _nombre_canal()
        wx.MessageDialog(
            None,
            _("Ya tienes la última versión (v%s), canal %s.") % (version, ch),
            _("No hay actualizaciones"),
            style=wx.OK | wx.ICON_INFORMATION,
        ).ShowModal()

    wx.CallAfter(_show)


def available_update_dialog(version, description):
    ch = _nombre_canal()
    dialog = wx.MessageDialog(
        None,
        _(
            "Hay una versión nueva en el canal %s.\n\n"
            "Versión de VeTube: %s\n\n"
            "¿Quieres descargarla ahora?\n\n"
            "Cambios:\n%s"
        )
        % (ch, version, description),
        _("Nueva versión de VeTube"),
        style=wx.YES | wx.NO | wx.ICON_WARNING,
    )
    if dialog.ShowModal() == wx.ID_YES:
        return True
    else:
        return False


def create_progress_dialog():
    # Sin PD_AUTO_HIDE (que viene por defecto): al llegar al 100 % de la
    # descarga la barra sigue viva para la copia de seguridad y para hacer de
    # madre del aviso final. Sin PD_CAN_ABORT: nadie lee la cancelación.
    return wx.ProgressDialog(
        _("Descarga en progreso"),
        _("Descargando la actualización"),
        parent=None,
        maximum=100,
        style=wx.PD_APP_MODAL,
    )


def _barra():
    """La barra de progreso de la actualización, creada si hace falta (hilo de la interfaz)."""
    global progress_dialog
    if progress_dialog is None:
        progress_dialog = create_progress_dialog()
        progress_dialog.Show()
    return progress_dialog


def cerrar_barra():
    """Destruye la barra de progreso (hilo de la interfaz, fuera de Update())."""
    global progress_dialog
    if progress_dialog is not None:
        progress_dialog.Destroy()
        progress_dialog = None


def _actualizar_barra(pct: int, mensaje: str) -> None:
    """Update() de la barra, contando cuántos están en curso.

    ProgressDialog.Update() procesa los eventos de interfaz pendientes antes
    de volver, y wxPython entrega los CallAfter como eventos de interfaz: todo
    lo que se pidió por CallAfter puede ejecutarse AQUÍ DENTRO, anidado, con
    la barra a medio actualizar. Mostrar ventanas o destruir la barra en ese
    momento revienta (violación de acceso medida en banc_updater_dialogos.py).
    Quien necesite hacerlo pregunta dentro_de_update() y espera (updater.py,
    _en_interfaz).
    """
    global _updates_en_curso
    _updates_en_curso += 1
    try:
        # Nunca el máximo: sin PD_AUTO_HIDE, al llegar a 100 Update() no
        # vuelve hasta que el usuario pulse Cerrar (medido en el banc), y la
        # misma barra sigue sirviendo para la fase siguiente.
        _barra().Update(min(pct, 99), mensaje)
    finally:
        _updates_en_curso -= 1


def dentro_de_update() -> bool:
    """True mientras un ProgressDialog.Update() esté en curso en este hilo."""
    return _updates_en_curso > 0


def progress_callback(total_downloaded, total_size):
    def update_ui():
        pct = int((total_downloaded * 100) / max(total_size, 1))
        _actualizar_barra(
            pct,
            _("Actualizando... %s de %s")
            % (
                str(utils.convert_bytes(total_downloaded)),
                str(utils.convert_bytes(total_size)),
            ),
        )

    wx.CallAfter(update_ui)


def iniciar_descarga():
    """Crea la barra de progreso y esconde el resto del programa.

    En el hilo de la interfaz. Primero la barra, después las ventanas: así el
    foco (y el lector de pantalla) pasa a la barra y no a otro programa. La
    barra es app-modal, así que sin esto la ventana principal quedaba visible
    pero deshabilitada durante toda la descarga.
    """
    # La ventana activa se lee ANTES de crear la barra: una vez creada, la
    # activa es ella (y GetActiveWindow no la devuelve, es nativa).
    activa = wx.GetActiveWindow()
    _barra()
    ocultar_ventanas(activa)


def ocultar_ventanas(activa=None):
    """Esconde las ventanas visibles del programa y las recuerda.

    Si la actualización sale bien no hace falta devolverlas: el bootstrap
    cierra VeTube. Si falla, mostrar_ventanas() las devuelve, ``activa`` (la
    que tenía el foco) al frente.
    """
    global _ventanas_ocultas, _ventana_activa
    _ventanas_ocultas = [
        ventana
        for ventana in wx.GetTopLevelWindows()
        if ventana.IsShown() and ventana is not progress_dialog
    ]
    # La que tenía el foco, primero: es la que se devuelve al frente.
    if activa in _ventanas_ocultas:
        _ventanas_ocultas.remove(activa)
        _ventanas_ocultas.insert(0, activa)
    _ventana_activa = _ventanas_ocultas[0] if _ventanas_ocultas else None
    for ventana in _ventanas_ocultas:
        ventana.Hide()


def mostrar_ventanas():
    """Devuelve las ventanas escondidas y cierra la barra (hilo de la interfaz).

    En ese orden: mientras la barra exista, el primer plano sigue siendo de
    VeTube, y al destruirla pasa a la ventana principal recién mostrada.
    """
    global _ventanas_ocultas
    vivas = [ventana for ventana in _ventanas_ocultas if ventana]  # destruida = False
    for ventana in vivas:
        ventana.Show()
        # La barra app-modal las dejó deshabilitadas y su Destroy() es
        # diferido (hasta el siguiente idle, DESPUÉS del aviso de fallo):
        # sin esto el lector de pantalla anuncia «VeTube, no disponible» al
        # volver (leído en el registro de NVDA).
        ventana.Enable()
    if vivas:
        vivas[0].Raise()
    _ventanas_ocultas = []
    cerrar_barra()
    if vivas:
        # Tras esconder/mostrar y el desactivador app-modal de la barra,
        # Windows a veces deja el teclado «en el aire»: foco explícito, como
        # al cerrar la última sesión de chat (PR #144).
        wx.CallAfter(vivas[0].SetFocus)


def aviso_descargada():
    """Avisa de que la actualización ya está descargada; con Aceptar se instala.

    Modal, en el hilo de la interfaz. El actualizador antiguo mostraba este
    aviso entre la extracción y el bootstrap; el nuevo lo llamaba DESPUÉS de
    lanzar el bootstrap, que mata a VeTube un segundo más tarde, así que nunca
    llegaba a verse.
    """
    dialogo = wx.MessageDialog(
        progress_dialog,
        _(
            "La actualización se ha descargado. Pulsa Aceptar para instalarla: "
            "Windows te pedirá permiso, VeTube se cerrará y se volverá a abrir solo."
        ),
        _("Actualización descargada"),
        style=wx.OK | wx.ICON_INFORMATION,
    )
    # El botón nativo se llama según el idioma de Windows, no el de VeTube:
    # con nombre propio, la frase y el botón dicen la misma palabra en los 7
    # idiomas (mismo gesto que donation() con SetYesNoLabels).
    dialogo.SetOKLabel(_("&Aceptar"))
    dialogo.ShowModal()
