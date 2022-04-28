#!/usr/bin/python
# -*- coding: <encoding name> -*-
import pytchat, json,wx,threading,keyboard,time,gettext,webbrowser
from playsound import playsound
from os import path
from accessible_output2.outputs import auto, sapi5
from youtube_dl import YoutubeDL
from pyperclip import copy
#pronto se dejará de usar pytchat
from chat_downloader import ChatDownloader
voz=0
configchat=1
tono=0
volume=100
mensajes=0
buffer=100
speed=0
sapy=True
todos=True
sonidos=True
idiomas = []
miembros=[]
leer=sapi5.SAPI5()
lector=auto.Auto()
lista=leer.list_voices()
t = gettext.translation('VeTube', 'locales',fallback=True,)
_ = t.gettext
def asignarBuffer():
	if mensajes==0 : buffer=100
	elif mensajes==1 : buffer=300
	elif mensajes==2 : buffer=500
	elif mensajes==3 : buffer=1000
def asignarConfiguracion():
    global voz,tono,volume,speed,configchat,sapy,mensajes,sonidos,buffer
    voz=0
    configchat=1
    tono=0
    volume=100
    speed=0
    sapy=True
    mensajes=0
    sonidos=True
    buffer=100
    leer.set_rate(speed)
    leer.set_pitch(tono)
    leer.set_voice(lista[voz])
    leer.set_volume(volume)
def escribirConfiguracion():
    data = {}
    data={'voz': voz,
"configchat": configchat,
"tono": tono,
"volume": volume,
"speed": speed,
'sapy':sapy,
'mensajes': mensajes,
'sonidos': sonidos}
    with open('data.json', 'w+') as file: json.dump(data, file)
def leerConfiguracion():
    if path.exists("data.json"):
        with open ("data.json") as file:
            resultado=json.load(file)
        global voz,configchat,tono,volume,speed,sapy,sonidos,mensajes
        voz=resultado['voz']
        configchat=resultado['configchat']
        tono=resultado['tono']
        volume=resultado['volume']
        speed=resultado['speed']
        sapy=resultado['sapy']
        mensajes=resultado['mensajes']
        sonidos=resultado['sonidos']
    else: escribirConfiguracion()
leerConfiguracion()
asignarBuffer()
leer.set_rate(speed)
leer.set_pitch(tono)
leer.set_voice(lista[voz])
leer.set_volume(volume)
class MyFrame(wx.Frame):
    def __init__(self, *args, **kwds):
        self.contarmiembros=0
        self.contador=0
        self.dentro=False
        self.hilo1 = threading.Thread(target=self.capturarTeclas)
        self.hilo1.daemon = True
        self.hilo1.start()
        kwds["style"] = kwds.get("style", 0) | wx.DEFAULT_FRAME_STYLE
        wx.Frame.__init__(self, *args, **kwds)
        self.donar = wx.Dialog(self, wx.ID_ANY, _("información"))
        dlg = wx.MessageDialog(self.donar, _(u"Con tu apoyo contribuyes a que este programa siga siendo gratuito. ¿Te unes a nuestra causa?"), _(u"Atención:"), wx.YES_NO | wx.ICON_ASTERISK)
        dlg.SetYesNoLabels(_("&Aceptar"), _("&Cancelar"))
        if dlg.ShowModal()==wx.ID_YES:
            webbrowser.open('https://www.paypal.com/donate/?hosted_button_id=5ZV23UDDJ4C5U')
            self.donar.Destroy()
        else: self.donar.Destroy()
        self.SetSize((800, 600))
        self.SetTitle("VeTube")
        self.SetWindowStyle(wx.RESIZE_BORDER | wx.CAPTION | wx.CLOSE_BOX | wx.CLIP_CHILDREN)
        self.panel_1 = wx.Panel(self, wx.ID_ANY)
        sizer_1 = wx.BoxSizer(wx.VERTICAL)
        self.menu_1 = wx.Button(self.panel_1, wx.ID_ANY, _(u"&Más opciones"))
        self.menu_1.Bind(wx.EVT_BUTTON, self.opcionesMenu)
        self.menu_1.SetToolTip(_(u"Pulse alt para abrir el menú"))

        self.notebook_1 = wx.Notebook(self.panel_1, wx.ID_ANY)
        sizer_1.Add(self.notebook_1, 1, wx.EXPAND, 0)
        self.tap_1 = wx.Panel(self.notebook_1, wx.ID_ANY)
        self.notebook_1.AddPage(self.tap_1, _("Inicio"))

        sizer_2 = wx.BoxSizer(wx.VERTICAL)

        self.label_1 = wx.StaticText(self.tap_1, wx.ID_ANY, _("Escriba o pegue una URL de youtube"), style=wx.ALIGN_CENTER_HORIZONTAL)
        sizer_2.Add(self.label_1, 0, 0, 0)
        self.text_ctrl_1 = wx.TextCtrl(self.tap_1, wx.ID_ANY, "", style=wx.TE_AUTO_URL | wx.TE_CENTRE | wx.TE_PROCESS_ENTER)
        self.text_ctrl_1.SetToolTip(_("Escribe o pega una URL"))
        self.text_ctrl_1.Bind(wx.EVT_TEXT, self.mostrarBoton)
        self.text_ctrl_1.Bind(wx.EVT_TEXT_ENTER, self.acceder)
        self.text_ctrl_1.SetFocus()
        sizer_2.Add(self.text_ctrl_1, 0, wx.ALIGN_CENTER_HORIZONTAL, 0)
        self.button_1 = wx.Button(self.tap_1, wx.ID_ANY, _("&Acceder"))
        self.button_1.Bind(wx.EVT_BUTTON, self.acceder)
        self.button_1.Disable()
        sizer_2.Add(self.button_1, 0, 0, 0)
        self.button_2 = wx.Button(self.tap_1, wx.ID_ANY, _(u"Borrar"))
        self.button_2.Bind(wx.EVT_BUTTON, self.borrarContenido)
        self.button_2.Disable()
        sizer_2.Add(self.button_2, 0, 0, 0)
        self.tap_1.SetSizer(sizer_2)

        self.panel_1.SetSizer(sizer_1)
        self.Layout()
        self.Maximize()
        self.Centre()
        self.Show()
    # Evento que hace aparecer las opciones del menú
    def opcionesMenu(self, event):
        self.menu = wx.Menu()
        self.opciones = wx.Menu()
        
        self.menu.AppendSubMenu(self.opciones, _(u"&Opciones"))
        self.opcion_1 = self.opciones.Append(wx.ID_ANY, _(u"Configuración"))
        self.Bind(wx.EVT_MENU, self.appConfiguracion, self.opcion_1)
        self.opcion_2 = self.opciones.Append(wx.ID_ANY, _(u"Restablecer los ajustes"))
        self.Bind(wx.EVT_MENU, self.restaurar, self.opcion_2)
        self.acercade = self.menu.Append(wx.ID_ANY, _(u"Acerca de"))
        self.Bind(wx.EVT_MENU, self.infoApp, self.acercade)
        self.salir = self.menu.Append(wx.ID_EXIT)
        self.Bind(wx.EVT_MENU, self.cerrarVentana, self.salir)
        position = self.menu_1.GetPosition()
        self.PopupMenu(self.menu, position)
        pass

    def appConfiguracion(self, event):            
        self.dialogo_2 = wx.Dialog(self, wx.ID_ANY, _("Configuración"))

        sizer_5 = wx.BoxSizer(wx.VERTICAL)
        labelConfic = wx.StaticText(self.dialogo_2, -1, _("Categorías"))
        sizer_5.Add(labelConfic, 1, wx.EXPAND, 0)
        self.tree_1 = wx.Treebook(self.dialogo_2, wx.ID_ANY)
        sizer_5.Add(self.tree_1, 1, wx.EXPAND, 0)

        self.treeItem_1 = wx.Panel(self.tree_1, wx.ID_ANY)
        self.tree_1.AddPage(self.treeItem_1, _("General"))
        sizer_4 = wx.BoxSizer(wx.HORIZONTAL)
        box_1 = wx.StaticBox(self.treeItem_1, -1, _("Opciones de la app"))
        boxSizer_1 = wx.StaticBoxSizer(box_1,wx.VERTICAL)

        label_7 = wx.StaticText(self.treeItem_1, wx.ID_ANY, _("Modalidad del chat: "))
        boxSizer_1.Add(label_7)
        self.choice_3 = wx.Choice(self.treeItem_1, wx.ID_ANY, choices=[_("Todos los chats"), _("solo chats de miembros y donativos.")])
        self.choice_3.Bind(wx.EVT_CHOICE, self.cambiarModoChat)
        self.choice_3.SetSelection(configchat-1)
        boxSizer_1.Add(self.choice_3)
        label_3 = wx.StaticText(self.treeItem_1, wx.ID_ANY, _("tamaño del bufer de mensajes: "))
        boxSizer_1.Add(label_3)
        self.choice_4 = wx.Choice(self.treeItem_1, wx.ID_ANY, choices=["100","300","500","1000"])
        self.choice_4.Bind(wx.EVT_CHOICE, self.cambiarMensajes)
        self.choice_4.SetSelection(mensajes)
        boxSizer_1.Add(self.choice_4)
        self.check_2 = wx.CheckBox(self.treeItem_1, wx.ID_ANY, _("Reproducir sonidos."))
        self.check_2.SetValue(sonidos)
        self.check_2.Bind(wx.EVT_CHECKBOX, self.reproducirSonidos)
        boxSizer_1.Add(self.check_2)
        sizer_4.Add(boxSizer_1, 0, 0, 0)

        self.treeItem_2 = wx.Panel(self.tree_1, wx.ID_ANY)
        self.tree_1.AddPage(self.treeItem_2, _("Voz"))
        sizer_6 = wx.BoxSizer(wx.HORIZONTAL)
        box_2 = wx.StaticBox(self.treeItem_2, -1, _("Opciones del habla"))
        boxSizer_2 = wx.StaticBoxSizer(box_2,wx.VERTICAL)
        self.check_1 = wx.CheckBox(self.treeItem_2, wx.ID_ANY, _("Voz sapy"))
        self.check_1.SetValue(sapy)
        self.check_1.Bind(wx.EVT_CHECKBOX, self.checar)
        boxSizer_2.Add(self.check_1)

        label_6 = wx.StaticText(self.treeItem_2, wx.ID_ANY, _("Voz: "))
        boxSizer_2 .Add(label_6)

        self.choice_2 = wx.Choice(self.treeItem_2, wx.ID_ANY, choices=lista)
        self.choice_2.SetSelection(voz)
        self.choice_2.Bind(wx.EVT_CHOICE, self.cambiarVoz)
        boxSizer_2 .Add(self.choice_2)

        label_8 = wx.StaticText(self.treeItem_2, wx.ID_ANY, _("Tono: "))
        boxSizer_2 .Add(label_8)

        self.slider_1 = wx.Slider(self.treeItem_2, wx.ID_ANY, tono+10, 0, 20)
        self.slider_1.Bind(wx.EVT_SLIDER, self.cambiarTono)
        boxSizer_2 .Add(self.slider_1)

        label_9 = wx.StaticText(self.treeItem_2, wx.ID_ANY, _("Volumen: "))
        boxSizer_2 .Add(label_9)

        self.slider_2 = wx.Slider(self.treeItem_2, wx.ID_ANY, volume, 0, 100)
        self.slider_2.Bind(wx.EVT_SLIDER, self.cambiarVolumen)
        boxSizer_2 .Add(self.slider_2)

        label_10 = wx.StaticText(self.treeItem_2, wx.ID_ANY, _("Velocidad: "))
        boxSizer_2 .Add(label_10)

        self.slider_3 = wx.Slider(self.treeItem_2, wx.ID_ANY, speed+10, 0, 20)
        self.slider_3.Bind(wx.EVT_SLIDER, self.cambiarVelocidad)
        boxSizer_2 .Add(self.slider_3)
        self.boton_prueva = wx.Button(self.treeItem_2, wx.ID_ANY, _("&Reproducir prueba."))
        self.boton_prueva.Bind(wx.EVT_BUTTON, self.reproducirPrueva)
        boxSizer_2.Add(self.boton_prueva)
        sizer_6.Add(boxSizer_2, 0, 0, 0)

        self.button_cansel = wx.Button(self.dialogo_2, wx.ID_CLOSE, _("&Cancelar"))
        sizer_5.Add(self.button_cansel, 0, 0, 0)

        self.button_6 = wx.Button(self.dialogo_2, wx.ID_ANY, _("&Aceptar"))
        self.button_6.Bind(wx.EVT_BUTTON, self.guardar)
        sizer_5.Add(self.button_6, 0, 0, 0)

        self.treeItem_1.SetSizer(sizer_4)
        self.treeItem_2.SetSizer(sizer_6)
        self.dialogo_2.SetSizer(sizer_5)        
        self.dialogo_2.SetEscapeId(self.button_cansel.GetId())
        self.dialogo_2.Center()
        self.dialogo_2.ShowModal()
        self.dialogo_2.Destroy()
    # Fin de la ventana de configuración

    def reproducirPrueva(self, event):
        if leer.silence(): leer.silence()
        else: leer.speak(_("Hola, soy la voz que te acompañará de ahora en adelante a leer los mensajes de tus canales favoritos."))
    def infoApp(self, event):
        wx.MessageBox(_("Creadores del proyecto:")+"\nCésar Verástegui & Johan G.\n"+_("Descripción:\n Lee en voz alta los mensajes de los directos en youtube, ajusta tus preferencias como quieras y disfruta más tus canales favoritos."), _("Información"), wx.ICON_INFORMATION)
    def cambiarVelocidad(self, event):
        global speed
        value=self.slider_3.GetValue()-10
        leer.set_rate(value)
        speed=value
    def cambiarTono(self, event):
        global tono
        value=self.slider_1.GetValue()-10
        leer.set_pitch(value)
        tono=value
    def cambiarVolumen(self, event):
        global volume
        leer.set_volume(self.slider_2.GetValue())
        volume=self.slider_2.GetValue()
    def reproducirSonidos(self,event):
        global sonidos
        if event.IsChecked(): sonidos=True
        else: sonidos=False
    def checar(self, event):
        global sapy
        if event.IsChecked(): sapy=True
        else: sapy=False
    def cambiarMensajes(self, event):
        global mensajes,buffer
        mensajes=self.choice_4.GetSelection()
        buffer=int(self.choice_4.GetString(self.choice_4.GetSelection()))
    def acceder(self, event):
        if self.text_ctrl_1.GetValue() == "":
            wx.MessageBox(_("No se puede  acceder porque el campo de  texto está vacío, debe escribir  algo."), "error.", wx.ICON_ERROR)
            self.text_ctrl_1.SetFocus()
        else:
            try: chat = ChatDownloader().get_chat(self.text_ctrl_1.GetValue())
            except:                
                wx.MessageBox(_("¡Parece que el enlace al cual está intentando acceder no es un enlace válido."), "error.", wx.ICON_ERROR)
                return
            try:
                self.contador=0
                self.contarmiembros=0
                self.chat = pytchat.create(self.text_ctrl_1.GetValue(),interruptable=False)
                self.dentro=True
                self.dialog_mensaje = wx.Dialog(self, wx.ID_ANY, _("Chat en vivo"))
                sizer_mensaje_1 = wx.BoxSizer(wx.VERTICAL)
                self.label_dialog = wx.StaticText(self.dialog_mensaje, wx.ID_ANY, _("Lectura del chat en vivo..."))
                sizer_mensaje_1.Add(self.label_dialog, 0, 0, 0)
                sizer_mensaje_2 = wx.StdDialogButtonSizer()
                sizer_mensaje_1.Add(sizer_mensaje_2, 0, wx.ALIGN_RIGHT | wx.ALL, 4)
                self.label_mensaje = wx.StaticText(self.dialog_mensaje, wx.ID_ANY, _("historial  de mensajes: "))
                sizer_mensaje_2.Add(self.label_mensaje, 20, wx.ALIGN_CENTER_VERTICAL | wx.ALL, 0)
                self.list_box_1 = wx.ListBox(self.dialog_mensaje, wx.ID_ANY, choices=[])
                self.list_box_1.SetFocus()
                self.list_box_1.Bind(wx.EVT_KEY_UP, self.historialItemsTeclas)
                sizer_mensaje_2.Add(self.list_box_1, 20, wx.ALIGN_CENTER_VERTICAL | wx.ALL, 0)
                self.button_mensaje_anterior = wx.Button(self.dialog_mensaje, wx.ID_ANY, _("Limpiar historial"))
                self.button_mensaje_anterior.Bind(wx.EVT_BUTTON,self.borrarEnlace)
                sizer_mensaje_2.Add(self.button_mensaje_anterior, 5, wx.ALIGN_CENTER_VERTICAL | wx.LEFT, 0)
                self.button_mensaje_detener = wx.Button(self.dialog_mensaje, wx.ID_ANY, _("&Detener"))
                self.button_mensaje_detener.Bind(wx.EVT_BUTTON,self.detenerLectura)
                sizer_mensaje_2.Add(self.button_mensaje_detener, 10, wx.ALIGN_CENTER_VERTICAL | wx.ALL, 0)
                sizer_mensaje_2.Realize()
                self.dialog_mensaje.SetSizer(sizer_mensaje_1)
                sizer_mensaje_1.Fit(self.dialog_mensaje)
                self.dialog_mensaje.Centre()
                self.dialog_mensaje.SetEscapeId(self.button_mensaje_detener.GetId())
                leer.speak(_("Ingresando al chat."))
                self.hilo2 = threading.Thread(target=self.iniciarChat)
                self.hilo2.daemon = True
                self.hilo2.start()
                self.dialog_mensaje.ShowModal()
            except Exception as e:
                wx.MessageBox(_("¡Parece que el enlace al cual está intentando acceder no es un enlace válido."), "error.", wx.ICON_ERROR)
                self.text_ctrl_1.SetFocus()
    def borrarContenido(self, event): self.text_ctrl_1.SetValue("")
    def detenerLectura(self, event):
        dlg_mensaje = wx.MessageDialog(self.dialog_mensaje, _(u"¿Desea salir de esta ventana y detener la lectura de los mensajes?"), _(u"Atención:"), wx.YES_NO | wx.ICON_ASTERISK)
        if dlg_mensaje.ShowModal() == wx.ID_YES:
            self.dentro=False
            leer.silence()
            self.dialog_mensaje.Destroy()
            self.text_ctrl_1.SetFocus()
            leer.speak(_("ha finalizado la lectura del chat."))
    def guardar(self, event):
        escribirConfiguracion()
        self.dialogo_2.Close()
    def borrarEnlace(self,event):
        dlg_2 = wx.MessageDialog(self.dialog_mensaje, _(u"Está apunto de eliminar del historial aproximadamente ")+str(self.list_box_1.GetCount())+_(" elementos, ¿desea proceder? Esta acción no se puede desacer."), _(u"Atención:"), wx.YES_NO | wx.ICON_ASTERISK)
        dlg_2.SetYesNoLabels(_("&Eliminar"), _("&Cancelar"))
        if self.list_box_1.GetCount() <= 0: wx.MessageBox(_("No hay elementos que borrar"), "Error", wx.ICON_ERROR)
        elif dlg_2.ShowModal()==wx.ID_YES:
            self.list_box_1.Clear()
            self.list_box_1.SetFocus()
    def restaurar(self, event):
        self.dlg_3 = wx.MessageDialog(self, _(u"Estás apunto de reiniciar la configuración a sus valores predeterminados, ¿Deseas proceder?"), _(u"Atención:"), wx.YES_NO | wx.ICON_ASTERISK)
        if self.dlg_3.ShowModal()==wx.ID_YES:
            asignarConfiguracion()
            escribirConfiguracion()
    def mostrarBoton(self, event):
        if self.text_ctrl_1.GetValue() != "":
            self.button_1.Enable()
            self.button_2.Enable()
        else:
            self.button_1.Disable()
            self.button_2.Disable()
    def cambiarModoChat(self, event):
        global configchat
        if event.GetSelection()==0: configchat=1
        else: configchat=2
    def cambiarVoz(self, event):    
        global voz
        voz=event.GetSelection()
        leer.set_voice(lista[event.GetSelection()])
    def historialItemsTeclas(self, event):
        event.Skip()
        if event.GetKeyCode() == 127: self.list_box_1.Delete(self.list_box_1.GetSelection())
        if event.GetKeyCode() == 32:
            if leer.silence(): leer.silence()
            else: leer.speak(self.list_box_1.GetString(self.list_box_1.GetSelection()))
    def iniciarChat(self):
        ydlop = {'ignoreerrors': True, 'quiet': True}
        with YoutubeDL(ydlop) as ydl: info_dict = ydl.extract_info(self.text_ctrl_1.GetValue(), download=False)
        self.label_dialog.SetLabel(info_dict.get('title')+', '+str(info_dict["view_count"])+_(' reproducciones'))
        self.text_ctrl_1.SetValue("")
        while self.chat.is_alive():
            for c in self.chat.get().sync_items():
                if c.type == "superChat" or c.type == "superSticker":
                    miembros.append(f"{c.currency}{c.amountString}, {c.author.name}: {c.message}")
                    self.list_box_1.Append(f"{c.currency}{c.amountString}, {c.author.name}: {c.message}")
                    if sonidos: playsound("sounds/donar.mp3",False)
                    if sapy: leer.speak(f"{c.currency}{c.amountString}, {c.author.name}: {c.message}")
                elif c.type == "newSponsor":
                    miembros.append(_("Nuevo Miembro: %s")%c.author.name)
                    self.list_box_1.Append(_("Nuevo Miembro: %s")%c.author.name)
                    if sonidos: playsound("sounds/miembros.mp3",False)
                    if sapy: leer.speak(_("Nuevo Miembro: %s")%c.author.name)
                elif c.author.isChatSponsor:
                    miembros.append(_("Miembro %s: %s")%(c.author.name,c.message))
                    self.list_box_1.Append(_("Miembro %s: %s")%(c.author.name,c.message))
                    if sapy: leer.speak(_("Miembro %s: %s")%(c.author.name,c.message))
                else:
                    if self.dentro: self.list_box_1.Append(f"{c.author.name}: {c.message}")
                    else:
                        exit()
                        self.hilo2.join()
                    if configchat==1:
                        if sapy: leer.speak(f"{c.author.name}: {c.message}")
                if self.list_box_1.GetCount()> buffer: self.list_box_1.Delete(0)
                if len(miembros)> buffer: miembros.pop(0)
    def elementoAnterior(self):
        if self.dentro:
            if todos:
                if self.list_box_1.GetCount() <= 0: lector.speak(_("no hay elementos en el historial"))
                else:
                    if self.contador>0: self.contador-=1
                    lector.speak(self.list_box_1.GetString(self.contador))
            else:
                if len(miembros) <= 0: lector.speak(_("no hay elementos en el historial"))
                else:
                    if self.contarmiembros>0: self.contarmiembros-=1
                    lector.speak(miembros[self.contarmiembros])
    def elementoSiguiente(self):
        if self.dentro:
            if todos:
                if self.list_box_1.GetCount() <= 0: lector.speak(_("no hay elementos en el historial"))
                else:
                    if self.contador<self.list_box_1.GetCount()-1: self.contador+=1
                    lector.speak(self.list_box_1.GetString(self.contador))
            else:
                if len(miembros) <= 0: lector.speak(_("no hay elementos en el historial"))
                else:
                    if self.contarmiembros<len(miembros)-1: self.contarmiembros+=1
                    lector.speak(miembros[self.contarmiembros])
    def copiar(self):
        if self.dentro:
            if todos:
                if self.list_box_1.GetCount() <= 0: lector.speak(_("no hay elementos en el historial"))
                else:
                    copy(self.list_box_1.GetString(self.contador))
                    lector.speak(_("¡Copiado!"))
            else:
                if len(miembros) <= 0: lector.speak(_("no hay elementos en el historial"))
                else:
                    copy(miembros[self.contarmiembros])
                    lector.speak(_("¡Copiado!"))
    def elementoInicial(self):
        if self.dentro:
            if todos:
                if self.list_box_1.GetCount() <= 0: lector.speak(_("no hay elementos en el historial"))
                else:
                    lector.speak(self.list_box_1.GetString(self.contador))
            else:
                if len(miembros) <= 0: lector.speak(_("no hay elementos en el historial"))
                else:
                    self.contarmiembros=0
                    lector.speak(miembros[self.contarmiembros])
    def elementoFinal(self):
        if self.dentro:
            if todos:
                if self.list_box_1.GetCount() <= 0: lector.speak(_("no hay elementos en el historial"))
                else:
                    self.contador=self.list_box_1.GetCount()-1
                    lector.speak(self.list_box_1.GetString(self.contador))
            else:
                if len(miembros) <= 0: lector.speak(_("no hay elementos en el historial"))
                else:
                    self.contarmiembros=len(miembros)-1
                    lector.speak(miembros[self.contarmiembros])
    def cambiarHistorial(self):
        global todos,configchat
        if todos:
            todos=False
            configchat=2
        else:
            todos=True
            configchat=1
        lector.speak(_("Todos los chats.") if todos else _("Miembros y donativos."))
    def callar(self):
        global sapy
        if sapy:
            sapy=False
            leer.silence()
        else: sapy=True
        lector.speak(_("Voz activada.")if sapy else _("Voz desactivada."))
    def capturarTeclas(self):
        keyboard.add_hotkey('alt+shift+up',self.elementoAnterior)
        keyboard.add_hotkey('alt+shift+down',self.elementoSiguiente)
        keyboard.add_hotkey('alt+shift+left',self.cambiarHistorial)
        keyboard.add_hotkey('alt+shift+right',self.cambiarHistorial)
        keyboard.add_hotkey('alt+shift+home',self.elementoInicial)
        keyboard.add_hotkey('alt+shift+end',self.elementoFinal)
        keyboard.add_hotkey('alt+shift+c',self.copiar)
        keyboard.add_hotkey('alt+shift+m',self.callar)
        keyboard.add_hotkey('alt+shift+v',wx.CallAfter,args=(self.mostrarMensaje,))
        keyboard.add_hotkey('control',leer.silence)
        keyboard.wait()
    def cerrarVentana(self, event):
        dialogo_cerrar = wx.MessageDialog(self, _(u"¿está seguro que desea salir del programa?"), _(u"¡atención!:"), wx.YES_NO | wx.ICON_ASTERISK)
        if dialogo_cerrar.ShowModal()==wx.ID_YES:
            self.Close()
    def retornarMensaje(self):
        if self.list_box_1.GetCount()>0 and todos: return self.list_box_1.GetString(self.contador)
        elif todos==False and len(miembros)>0: return miembros[self.contarmiembros]
    def mostrarMensaje(self):
        if self.dentro and self.retornarMensaje():
            my_dialog = wx.Dialog(self, wx.ID_ANY, _("mensaje"))
            sizer_mensaje = wx.BoxSizer(wx.HORIZONTAL)
            text_box = wx.TextCtrl(my_dialog, wx.ID_ANY, self.retornarMensaje(), style=wx.TE_CENTRE | wx.TE_READONLY)
            sizer_mensaje.Add(text_box, 0, 0, 0)
            cancelar = wx.Button(my_dialog, wx.ID_CLOSE, _("&Cerrar"))
            sizer_mensaje.Add(cancelar,0,0,0)
            my_dialog.SetSizer(sizer_mensaje)
            sizer_mensaje.Fit(my_dialog)
            my_dialog.Centre()
            my_dialog.SetEscapeId(cancelar.GetId())
            my_dialog.ShowModal()
class MyApp(wx.App):
    def OnInit(self):
        self.frame = MyFrame(None, wx.ID_ANY, "")
        self.SetTopWindow(self.frame)
        self.frame.Show()
        return True
# end of class MyApp
app = MyApp(0)
app.MainLoop()