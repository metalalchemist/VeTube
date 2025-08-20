import wx
from setup import reader
from ui.chat_ui import ChatDialog
from ui.menus.chat_item_menu import ChatItemMenu
from controller.menus.chat_item_controller import ChatItemController
from controller.menus.chat_menu_controller import ChatMenuController
from controller.menus.chat_filter_controller import ChatFilterController
from ui.dialog_response import response
from globals import data_store
from utils.estadisticas_manager import EstadisticasManager

class ChatController:
    def __init__(self, frame, servicio=None, plataforma=None):
        self.frame = frame
        self.servicio = servicio
        self.plataforma = plataforma
        self.ui = None
        self.menu_opciones_controller = None
        self.menu_filter_controller = None
        self.todos_los_eventos = []
        self.filtro_eventos = "todos"

    def _bind_events(self):
        self.ui.button_mensaje_detener.Bind(wx.EVT_BUTTON, self.on_close_dialog)
        self.ui.boton_opciones.Bind(wx.EVT_BUTTON, self.on_opciones_btn)
        
        if self.plataforma == 'TikTok' and hasattr(self.ui, 'boton_filtrar'):
            self.ui.boton_filtrar.Bind(wx.EVT_BUTTON, self.on_filter_btn)

        list_boxes = []
        if self.plataforma == 'La sala de juegos':
            if data_store.config['categorias'][0]: list_boxes.append(self.ui.list_box_general)
            if data_store.config['categorias'][2]: list_boxes.append(self.ui.list_box_miembros)
        elif self.plataforma == 'TikTok':
            if data_store.config['categorias'][0]: list_boxes.append(self.ui.list_box_general)
            if data_store.config['categorias'][1]: list_boxes.append(self.ui.list_box_eventos)
            if data_store.config['categorias'][2]: list_boxes.append(self.ui.list_box_miembros)
            if data_store.config['categorias'][3]: list_boxes.append(self.ui.list_box_donaciones)
        else:
            if data_store.config['categorias'][0]: list_boxes.append(self.ui.list_box_general)
            if data_store.config['categorias'][1]: list_boxes.append(self.ui.list_box_eventos)
            if data_store.config['categorias'][2]: list_boxes.append(self.ui.list_box_miembros)
            if data_store.config['categorias'][3]: list_boxes.append(self.ui.list_box_donaciones)
            if data_store.config['categorias'][4]: list_boxes.append(self.ui.list_box_moderadores)
            if data_store.config['categorias'][5]: list_boxes.append(self.ui.list_box_verificados)
        for lb in list_boxes:
            lb.Bind(wx.EVT_CONTEXT_MENU, self.on_context_menu)
            lb.Bind(wx.EVT_KEY_UP, self.on_listbox_keyup)

    def on_context_menu(self, event):
        list_box = event.GetEventObject()
        if list_box.GetSelection() == wx.NOT_FOUND: return
        
        menu = ChatItemMenu(self.ui)
        ChatItemController(menu, list_box)
        self.ui.PopupMenu(menu.menu)

    def on_opciones_btn(self, event):
        self.menu_opciones_controller.menu.popup(self.ui.boton_opciones)

    def on_filter_btn(self, event):
        self.menu_filter_controller.show_menu(self.ui.boton_filtrar)

    def on_listbox_keyup(self, event):
        event.Skip()
        if event.GetKeyCode() == 32:
            reader._leer.silence()
            list_box = event.GetEventObject()
            reader.leer_sapi(list_box.GetString(list_box.GetSelection()))

    def on_close_dialog(self, event):
        if response(_("¿Desea salir de esta ventana y detener la lectura de los mensajes?"), _("Atención:")) == wx.ID_YES:
            EstadisticasManager().resetear_estadisticas()
            self.servicio.detener()
            main_frame = self.ui.GetParent()
            self.ui.Destroy()
            reader._leer.silence()
            reader.leer_sapi(_("ha finalizado la lectura del chat."))
            main_frame.text_ctrl_1.SetValue("")
            main_frame.text_ctrl_1.SetFocus()
            main_frame.plataforma.SetSelection(0)

    def agregar_mensaje_general(self, mensaje): self.ui.list_box_general.Append(mensaje)
    def agregar_mensaje_evento(self, mensaje, tipo=None):
        if self.plataforma=='TikTok':
            self.todos_los_eventos.append((mensaje, tipo))
            if self.filtro_eventos == "todos" or self.filtro_eventos == tipo: self.ui.list_box_eventos.Append(mensaje)
        else: self.ui.list_box_eventos.Append(mensaje)
    def agregar_mensaje_miembro(self, mensaje): self.ui.list_box_miembros.Append(mensaje)
    def agregar_mensaje_donacion(self, mensaje): self.ui.list_box_donaciones.Append(mensaje)
    def agregar_mensaje_moderador(self, mensaje): self.ui.list_box_moderadores.Append(mensaje)
    def agregar_mensaje_verificado(self, mensaje): self.ui.list_box_verificados.Append(mensaje)
    def agregar_titulo(self, titulo): self.ui.label_dialog.SetLabel(titulo)

    def actualizar_filtro_eventos(self, filtro):
        self.filtro_eventos = filtro
        self.ui.list_box_eventos.Clear()
        for mensaje, tipo in self.todos_los_eventos:
            if self.filtro_eventos == "todos" or self.filtro_eventos == tipo:
                self.ui.list_box_eventos.Append(mensaje)

    def mostrar_dialogo(self):
        self.ui = ChatDialog(self.frame, self.plataforma)
        self.ui.actualizar_filtro_eventos = self.actualizar_filtro_eventos
        self.menu_opciones_controller = ChatMenuController(self.ui, self.plataforma, self)
        if self.plataforma == 'TikTok':
            self.menu_filter_controller = ChatFilterController(self)
        self._bind_events()
        self.ui.ShowModal()

    def buscar_mensajes(self):
        dialogo = wx.TextEntryDialog(self.ui, _("Introduce el criterio de búsqueda"), _("Buscar mensajes"))
        if dialogo.ShowModal() == wx.ID_OK:
            criterio = dialogo.GetValue()
            if not criterio: return

            resultados = []
            list_boxes = []
            if hasattr(self.ui, 'list_box_general'): list_boxes.append(self.ui.list_box_general)
            if hasattr(self.ui, 'list_box_eventos'): list_boxes.append(self.ui.list_box_eventos)
            if hasattr(self.ui, 'list_box_miembros'): list_boxes.append(self.ui.list_box_miembros)
            if hasattr(self.ui, 'list_box_donaciones'): list_boxes.append(self.ui.list_box_donaciones)
            if hasattr(self.ui, 'list_box_moderadores'): list_boxes.append(self.ui.list_box_moderadores)
            if hasattr(self.ui, 'list_box_verificados'): list_boxes.append(self.ui.list_box_verificados)

            for lb in list_boxes:
                for i in range(lb.GetCount()):
                    mensaje = lb.GetString(i)
                    if criterio.lower() in mensaje.lower(): resultados.append(mensaje)
            
            if resultados:
                list_box, page_index, close_button = self.ui.create_page_with_listbox(self.ui.treebook, name=criterio, add_close_button=True)
                list_box.Set(resultados)
                close_button.Bind(wx.EVT_BUTTON, self.cerrar_pestaña_busqueda)
                self.ui.treebook.SetSelection(page_index)
            else: wx.MessageBox(_("No se encontraron mensajes que coincidan con el criterio de búsqueda."), _("Búsqueda sin resultados"), wx.OK | wx.ICON_INFORMATION)
        dialogo.Destroy()

    def cerrar_pestaña_busqueda(self, event):
        button = event.GetEventObject()
        panel = button.GetParent()
        page_index = self.ui.treebook.FindPage(panel)
        if page_index != wx.NOT_FOUND: self.ui.treebook.DeletePage(page_index)
