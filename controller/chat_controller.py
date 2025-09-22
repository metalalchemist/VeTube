import wx,wx.adv, configparser
from globals import data_store, resources
from pyperclip import copy
from setup import reader, player
from ui.chat_ui import ChatDialog
from ui.menus.chat_item_menu import ChatItemMenu
from ui.show_comment import ShowCommentDialog
from controller.menus.chat_item_controller import ChatItemController
from controller.menus.chat_menu_controller import ChatMenuController
from controller.menus.chat_filter_controller import ChatFilterController
from controller.editor_controller import EditorController
from ui.dialog_response import response
from servicios.estadisticas_manager import EstadisticasManager
from utils.funciones import escribirJsonLista, extractUser
from helpers.keyboard_handler.wx_handler import WXKeyboardHandler

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
        self.keyboard_handler = None
        self.chat_shortcuts = {}
        self.media_controller = None

    def set_active_service(self, service_instance):
        self.servicio = service_instance

    def set_media_controller(self, controller):
        self.media_controller = controller
        self.reload_shortcuts()

    def _bind_events(self):
        self.ui.button_mensaje_detener.Bind(wx.EVT_BUTTON, self.on_close_dialog)
        self.ui.boton_opciones.Bind(wx.EVT_BUTTON, self.on_opciones_btn)
        self.ui.boton_eliminar.Bind(wx.EVT_BUTTON, self.on_eliminar_pestaña)
        if self.plataforma == 'TikTok' and hasattr(self.ui, 'boton_filtrar'): self.ui.boton_filtrar.Bind(wx.EVT_BUTTON, self.on_filter_btn)
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
        if data_store.config['categorias'][6]: list_boxes.append(self.ui.list_box_favoritos)
        for lb in list_boxes:
            lb.Bind(wx.EVT_CONTEXT_MENU, self.on_context_menu)
            lb.Bind(wx.EVT_KEY_UP, self.on_listbox_keyup)

    def on_context_menu(self, event):
        list_box = event.GetEventObject()
        if list_box.GetSelection() == wx.NOT_FOUND: return
        
        menu = ChatItemMenu(self.ui)
        ChatItemController(menu, list_box, self.plataforma, self.ui.label_dialog)
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
            reader.leer_auto(list_box.GetString(list_box.GetSelection()))

    def on_close_dialog(self, event):
        if response(_("¿Desea salir de esta ventana y detener la lectura de los mensajes?"), _("Atención:")) == wx.ID_YES:
            if self.keyboard_handler:
                self.keyboard_handler.unregister_all_keys()
            EstadisticasManager().resetear_estadisticas()
            self.servicio.detener()
            main_frame = self.ui.GetParent()
            self.ui.Destroy()
            reader._leer.silence()
            reader.leer_sapi(_("ha finalizado la lectura del chat."))
            main_frame.text_ctrl_1.SetValue("")
            main_frame.text_ctrl_1.SetFocus()
            main_frame.plataforma.SetSelection(0)

    def on_eliminar_pestaña(self, event):
        page_index = self.ui.treebook.GetSelection()
        if page_index == wx.NOT_FOUND: return
        self.ui.treebook.DeletePage(page_index)
        self.actualizar_estado_boton_eliminar()

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

    def actualizar_estado_boton_eliminar(self):
        if self.ui.treebook.GetPageCount() <= 1:
            self.ui.boton_eliminar.Hide()
        else:
            self.ui.boton_eliminar.Show()
        self.ui.Layout()

    def mostrar_dialogo(self):
        self.ui = ChatDialog(self.frame, self.plataforma)
        self.keyboard_handler = WXKeyboardHandler(self.ui)
        self._load_and_register_shortcuts() # Activado para carga inicial de atajos
        self.ui.actualizar_filtro_eventos = self.actualizar_filtro_eventos
        self.menu_opciones_controller = ChatMenuController(self.ui, self.plataforma, self)
        if self.plataforma == 'TikTok':
            self.menu_filter_controller = ChatFilterController(self)
        self._bind_events()
        self.actualizar_estado_boton_eliminar()

    def show(self):
        self.ui.ShowModal()

    def buscar_mensajes(self):
        dialogo = wx.TextEntryDialog(self.ui, _("Introduce el criterio de búsqueda"), _("Buscar mensajes"))
        dialogo.Raise()
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
                list_box, page_index= self.ui.create_page_with_listbox(self.ui.treebook, name=criterio)
                list_box.Set(resultados)
                self.ui.treebook.SetSelection(page_index)
                self.actualizar_estado_boton_eliminar()
                if data_store.config['sonidos'] and data_store.config['listasonidos'][8]: player.playsound(resources.rutasonidos[8],False)
            else: wx.MessageBox(_("No se encontraron mensajes que coincidan con el criterio de búsqueda."), _("Búsqueda sin resultados"), wx.OK | wx.ICON_INFORMATION)
        dialogo.Destroy()

    @property
    def current_listbox(self):
        if not self.ui: return None
        page = self.ui.treebook.GetCurrentPage()
        if not page:
            return None
        for child in page.GetChildren():
            if isinstance(child, wx.ListBox):
                return child
        return None

    def avanzarCategorias(self):
        if not self.ui: return
        current_selection = self.ui.treebook.GetSelection()
        page_count = self.ui.treebook.GetPageCount()
        if page_count == 0: return
        next_selection = current_selection + 1
        if next_selection >= page_count:
            next_selection = 0
        self.ui.treebook.SetSelection(next_selection)
        self.ui.treebook.SetFocus()
        reader.leer_auto(self.ui.treebook.GetPageText(next_selection))

    def retrocederCategorias(self):
        if not self.ui: return
        current_selection = self.ui.treebook.GetSelection()
        page_count = self.ui.treebook.GetPageCount()
        if page_count == 0: return
        next_selection = current_selection - 1
        if next_selection < 0:
            next_selection = page_count - 1
        self.ui.treebook.SetSelection(next_selection)
        self.ui.treebook.SetFocus()
        reader.leer_auto(self.ui.treebook.GetPageText(next_selection))

    def elementoAnterior(self):
        listbox = self.current_listbox
        if not listbox or listbox.GetCount() == 0: return
        selection = listbox.GetSelection()
        if selection == wx.NOT_FOUND:
            selection = 0
        elif selection > 0:
            selection -= 1
        listbox.SetSelection(selection)
        self.reproducirMsg()
        reader.leer_auto(listbox.GetString(selection))

    def elementoSiguiente(self):
        listbox = self.current_listbox
        if not listbox or listbox.GetCount() == 0: return
        selection = listbox.GetSelection()
        if selection == wx.NOT_FOUND:
            selection = 0
        elif selection < listbox.GetCount() - 1:
            selection += 1
        listbox.SetSelection(selection)
        self.reproducirMsg()
        reader.leer_auto(listbox.GetString(selection))

    def reproducirMsg(self):
        listbox = self.current_listbox
        if not listbox:
            return
        selection = listbox.GetSelection()
        if selection == 0 or selection == listbox.GetCount() - 1:
            player.playsound(f"sounds/{data_store.config['directorio']}/orilla.mp3", False)
        else:
            player.playsound(f"sounds/{data_store.config['directorio']}/msj.mp3", False)

    def elemento_inicial(self):
        listbox = self.current_listbox
        if not listbox or listbox.GetCount() == 0: return
        listbox.SetSelection(0)
        self.reproducirMsg()
        reader.leer_auto(listbox.GetString(0))

    def elemento_final(self):
        listbox = self.current_listbox
        if not listbox or listbox.GetCount() == 0: return
        last_index = listbox.GetCount() - 1
        listbox.SetSelection(last_index)
        self.reproducirMsg()
        reader.leer_auto(listbox.GetString(last_index))

    def copiarMensajeActual(self):
        listbox = self.current_listbox
        if not listbox or listbox.GetSelection() == wx.NOT_FOUND: return
        selected_text = listbox.GetString(listbox.GetSelection())
        copy(selected_text)
        reader.leer_auto(_("Mensaje copiado"))

    def mostrar_mensaje_actual(self):
        listbox = self.current_listbox
        if not listbox or listbox.GetSelection() == wx.NOT_FOUND: return
        selected_text = listbox.GetString(listbox.GetSelection())
        dialog = ShowCommentDialog(self.ui, selected_text)
        dialog.ShowModal()
        dialog.Destroy()

    def agregar_mensajes_favoritos(self):
        listbox = self.current_listbox
        if not listbox or listbox.GetSelection() == wx.NOT_FOUND:
            return
        mensaje = listbox.GetString(listbox.GetSelection())
        if not hasattr(self.ui, 'list_box_favoritos'):
            self.ui.list_box_favoritos, self.ui.page_index_favoritos = self.ui.create_page_with_listbox(self.ui.treebook, _(u"Favoritos"))
            self.ui.list_box_favoritos.Bind(wx.EVT_CONTEXT_MENU, self.on_context_menu)
            self.ui.list_box_favoritos.Bind(wx.EVT_KEY_UP, self.on_listbox_keyup)
        if mensaje in self.ui.list_box_favoritos.GetStrings():
            reader.leer_auto(_("Este mensaje ya se encuentra en favoritos"))
            return
        self.ui.list_box_favoritos.Append(mensaje)
        reader.leer_auto(_("Mensaje agregado a favoritos"))

    def archivar_mensaje(self):
        listbox = self.current_listbox
        if not listbox or listbox.GetSelection() == wx.NOT_FOUND: return
        
        mensaje = listbox.GetString(listbox.GetSelection())
        if not mensaje: return # Evitar archivar mensajes vacíos

        main_frame = self.ui.GetParent()
        list_mensajes = main_frame.list_mensajes

        if list_mensajes.GetCount() > 0 and list_mensajes.GetStrings()[0] == _("Tus mensajes archivados aparecerán aquí"):
            list_mensajes.Delete(0)
        
        ya_archivado = any(mensaje == d.get('mensaje', '') for d in data_store.mensajes_destacados)
        if not ya_archivado:
            # Determinar el título
            if self.plataforma == 'TikTok':
                titulo = extractUser(main_frame.text_ctrl_1.GetValue())
            else:
                titulo = self.ui.label_dialog.GetLabelText()

            # Añadir a la lista de la UI y al almacenamiento de datos
            list_mensajes.Append(f"{mensaje}: {titulo}")
            data_store.mensajes_destacados.append({'mensaje': mensaje, 'titulo': titulo})
            
            escribirJsonLista('mensajes_destacados.json', data_store.mensajes_destacados)
            reader.leer_auto(_("El mensaje ha sido archivado correctamente."))
        else: 
            reader.leer_auto(_("Este mensaje ya está en la lista de archivados."))

    def borrar_pagina_actual(self):
        page_index = self.ui.treebook.GetSelection()
        page_count = self.ui.treebook.GetPageCount()

        if page_count <= 1:
            reader.leer_auto(_("No se puede borrar la última página."))
            return

        self.ui.treebook.DeletePage(page_index)
        reader.leer_auto(_("Página borrada."))
        self.actualizar_estado_boton_eliminar()

    def mostrar_editor_combinaciones(self):
        editor = EditorController(self.ui, self)
        editor.ShowModal()

    def _load_and_register_shortcuts(self):
        if self.keyboard_handler:
            self.keyboard_handler.unregister_all_keys()
        
        self.chat_shortcuts = {}
        command_objects = {'chat': self, 'reader': reader}
        if self.media_controller:
            command_objects['media_player'] = self.media_controller
            command_objects['player'] = self.media_controller

        config = configparser.ConfigParser(interpolation=None)
        config.read("keymaps/keys.txt")

        for section in ['atajos_chat', 'atajos_player']:
            if section in config:
                for key, command_str in config[section].items():
                    try:
                        obj_name, method_path = command_str.split('.', 1)
                        if obj_name in command_objects:
                            target_obj = command_objects[obj_name]
                            attrs = method_path.split('.')
                            final_callable = target_obj
                            for attr in attrs:
                                final_callable = getattr(final_callable, attr)
                            if callable(final_callable):
                                self.chat_shortcuts[key] = final_callable
                    except Exception as e:
                        print(f"Error parsing shortcut {key}={command_str}: {e}")
        
        if self.keyboard_handler:
            self.keyboard_handler.register_keys(self.chat_shortcuts)

    def reload_shortcuts(self):
        self._load_and_register_shortcuts()

    def toggle_lectura_automatica(self):
        if data_store.config['reader']:
            reader._leer.silence()
            data_store.config['reader'] = False
        else: data_store.config['reader'] = True
        reader.leer_auto(_("Lectura automática activada.") if data_store.config['reader'] else _("Lectura automática  desactivada."))
    def toggle_sounds(self):
        if data_store.config['sonidos']: data_store.config['sonidos'] = False
        else: data_store.config['sonidos'] = True
        reader.leer_auto(_("sonidos activados.") if data_store.config['reader'] else _("sonidos desactivados."))
