#!/usr/bin/python
# -*- coding: <encoding name> -*-
import json,wx,threading,urllib.request,languageHandler,socket,os,time,restart,wx.adv
from keyboard_handler.wx_handler import WXKeyboardHandler
from playsound import playsound
from accessible_output2.outputs import auto, sapi5
from youtube_dl import YoutubeDL
from pyperclip import copy
from chat_downloader import ChatDownloader
voz=0
tono=0
volume=100
speed=0
sapi=True
sonidos=True
reader=True
idioma="system"
version="v2.1"
yt=0
favorite=[]
categ=[True,True,False,False,False]
listasonidos=[True,True,True,True,True,True,True,True]
rutasonidos=["sounds/chat.mp3","sounds/chatmiembro.mp3","sounds/miembros.mp3","sounds/donar.mp3","sounds/moderators.mp3","sounds/verified.mp3","sounds/abrirchat.wav","sounds/propietario.mp3"]
lector=auto.Auto()
leer=sapi5.SAPI5()
lista_voces=leer.list_voices()
db_fichero_complemento = os.path.join(os.getcwd(), 'vetube.zip')
def retornarCategorias():
    lista=[[_('General')]]
    if categ[0]: lista.append([_('Miembros')])
    if categ[1]: lista.append([_('Donativos')])
    if categ[2]: lista.append([_('Moderadores')])
    if categ[3]: lista.append([_('Usuarios Verificados')])
    if categ[4]: lista.append([_('Favoritos')])
    return lista
def escribirFavorito():
    with open('favoritos.json', 'w+') as file: json.dump(favorite, file)
def leerFavoritos():
    if os.path.exists("favoritos.json"):
        with open ("favoritos.json") as file:
            global favorite
            favorite=json.load(file)
    else: escribirFavorito()
def asignarConfiguracion():
    global voz,tono,volume,speed,sapi,sonidos,idioma,reader,categ,listasonidos
    voz=0
    tono=0
    volume=100
    speed=0
    sapi=True
    sonidos=True
    idioma="system"
    reader=True
    categ=[True,True,False,False,False]
    listasonidos=[True,True,True,True,True,True,True,True]
    leer.set_rate(speed)
    leer.set_pitch(tono)
    leer.set_voice(lista_voces[voz])
    leer.set_volume(volume)
def convertirFavoritos(lista):
    if len(lista)<=0: return[]
    else:
        newlista=[]
        for datos in lista: newlista.append(datos['titulo']+': '+datos['url'])
        return newlista
def escribirConfiguracion():
    data={'voz': voz,
"tono": tono,
"volume": volume,
"speed": speed,
'sapi':sapi,
'sonidos': sonidos,
'idioma': idioma,
'categorias': categ,
'listasonidos': listasonidos,
'reader': reader}
    with open('data.json', 'w+') as file: json.dump(data, file)
def leerConfiguracion():
    if os.path.exists("data.json"):
        with open ("data.json") as file:
            resultado=json.load(file)
        global voz,tono,volume,speed,sapi,sonidos,idioma,reader,categ,listasonidos
        voz=resultado['voz']
        tono=resultado['tono']
        volume=resultado['volume']
        speed=resultado['speed']
        sapi=resultado['sapi']
        sonidos=resultado['sonidos']
        idioma=resultado['idioma']
        reader=resultado['reader']
        categ=resultado['categorias']
        listasonidos=resultado['listasonidos']
    else: escribirConfiguracion()
def escribirTeclas():
    with open('keys.txt', 'w+') as arch: arch.write("""{"control+p": leer.silence,"alt+shift+up": self.elementoAnterior,"alt+shift+down": self.elementoSiguiente,"alt+shift+left": self.retrocederCategorias,"alt+shift+right": self.avanzarCategorias,"alt+shift+home": self.elementoInicial,"alt+shift+end": self.elementoFinal,"alt+shift+f": self.destacarMensaje,"alt+shift+c": self.copiar,"alt+shift+m": self.callar,"alt+shift+s": self.iniciarBusqueda,"alt+shift+v": self.mostrarMensaje,"alt+shift+d": self.borrarBuffer,"alt+shift+p": self.desactivarSonidos}""")
    leerTeclas()
def leerTeclas():
    if os.path.exists("keys.txt"):
        global mis_teclas
        with open ("keys.txt",'r') as arch:
            mis_teclas=arch.read()
    else: escribirTeclas()
pos=[]
leerConfiguracion()
leerFavoritos()
leer.set_rate(speed)
leer.set_pitch(tono)
leer.set_voice(lista_voces[voz])
leer.set_volume(volume)
favs=convertirFavoritos(favorite)
languageHandler.setLanguage(idioma)
idiomas = languageHandler.getAvailableLanguages()
langs = []
[langs.append(i[1]) for i in idiomas]
codes = []
[codes.append(i[0]) for i in idiomas]
mensaje_teclas=[_('Silencia la voz sapy'),_('Buffer anterior.'),_('Siguiente buffer.'),_('Mensaje anterior'),_('Mensaje siguiente'),_('Ir al comienzo del buffer'),_('Ir al final del buffer'),_('Copia el mensaje actual'),_('Activa o desactiva la lectura automática'),_('Muestra el mensaje actual en un cuadro de texto'),_('Busca una palabra en los mensajes actuales')]
mensajes_categorias=[_('Miembros'),_('Donativos'),_('Moderadores'),_('Usuarios Verificados'),_('Favoritos')]
mensajes_sonidos=[_('Sonido cuando llega un mensaje'),_('Sonido cuando habla un miembro'),_('Sonido cuando se conecta un miembro'),_('Sonido cuando llega un donativo'),_('Sonido cuando habla un moderador'),_('Sonido cuando habla un usuario verificado'),_('Sonido al ingresar al chat'),_('Sonido cuando habla el propietario del canal')]
codes.reverse()
langs.reverse()
lista=retornarCategorias()
for temporal in lista: pos.append(1)
class HiloActualizacionComplemento(threading.Thread):
    def __init__(self, frame):
        super(HiloActualizacionComplemento, self).__init__()
        self.frame = frame
        self.tiempo = 30
        self.daemon = True
        threading.Thread.__init__(self)
    def humanbytes(self, B): # Convierte bytes
        B = float(B)
        KB = float(1024)
        MB = float(KB ** 2) # 1,048,576
        GB = float(KB ** 3) # 1,073,741,824
        TB = float(KB ** 4) # 1,099,511,627,776
        if B < KB:
            return '{0} {1}'.format(B,'Bytes' if 0 == B > 1 else 'Byte')
        elif KB <= B < MB:
            return '{0:.2f} KB'.format(B/KB)
        elif MB <= B < GB:
            return '{0:.2f} MB'.format(B/MB)
        elif GB <= B < TB:
            return '{0:.2f} GB'.format(B/GB)
        elif TB <= B:
            return '{0:.2f} TB'.format(B/TB)
    def __call__(self, block_num, block_size, total_size):
        readsofar = block_num * block_size
        if total_size > 0:
            percent = readsofar * 1e2 / total_size
            wx.CallAfter(self.frame.next, percent)
            time.sleep(1 / 995)
            wx.CallAfter(self.frame.TextoRefresco, _("Espere por favor...\n") + _("Descargando: %s") % self.humanbytes(readsofar))
            if readsofar >= total_size: # Si queremos hacer algo cuando la descarga termina.
                pass
        else: # Si la descarga es solo el tamaño
            wx.CallAfter(self.frame.TextoRefresco, _("Espere por favor...\n") + _("Descargando: %s") % self.humanbytes(readsofar))
    def run(self):
        while self.tiempo==30:
            try:
                socket.setdefaulttimeout(self.tiempo) # Dara error si pasan 30 seg sin internet
                try:
                    req = urllib.request.Request(urlDescarga, headers={'User-Agent': 'Mozilla/5.0'})
                    obj = urllib.request.urlopen(req).geturl()
                    urllib.request.urlretrieve(obj, db_fichero_complemento, reporthook=self.__call__)
                except Exception as e:
                    urllib.request.urlretrieve(obj, db_fichero_complemento, reporthook=self.__call__)
                wx.CallAfter(self.frame.done, _("Se terminó la descarga de la nueva actualización.\nel programa se cerrará para que usted reemplase los archivos de la nueva actualización.\n¿disfrute!"))
                self.tiempo=0
            except:
                wx.CallAfter(self.frame.error, _("Algo salió mal.\nCompruebe que tiene conexión a internet y vuelva a intentarlo.\nel programa se  cerrará."))
                self.tiempo=0
class ActualizacionDialogo(wx.Dialog):
    def __init__(self, frame):
        WIDTH = 550
        HEIGHT = 400
        super(ActualizacionDialogo, self).__init__(None, -1, title=_("Actualizando el programa..."), size = (WIDTH, HEIGHT))
        self.CenterOnScreen()
        self.frame = frame
        self.Panel = wx.Panel(self)
        self.progressBar=wx.Gauge(self.Panel, wx.ID_ANY, range=100, style = wx.GA_HORIZONTAL)
        self.textorefresco = wx.TextCtrl(self.Panel, wx.ID_ANY, style =wx.TE_MULTILINE|wx.TE_READONLY)
        self.textorefresco.Bind(wx.EVT_CONTEXT_MENU, self.skip)
        self.AceptarTRUE = wx.Button(self.Panel, wx.NewIdRef(), _("&Aceptar"))
        self.Bind(wx.EVT_BUTTON, self.onAceptarTRUE, id=self.AceptarTRUE.GetId())
        self.AceptarTRUE.Disable()
        self.AceptarFALSE = wx.Button(self.Panel, wx.NewIdRef(), _("&Cerrar"))
        self.Bind(wx.EVT_BUTTON, self.onAceptarFALSE, id=self.AceptarFALSE.GetId())
        self.AceptarFALSE.Disable()
        self.Bind(wx.EVT_CLOSE, self.onNull)
        sizer = wx.BoxSizer(wx.VERTICAL)
        sizer_botones = wx.BoxSizer(wx.HORIZONTAL)
        sizer.Add(self.progressBar, 0, wx.EXPAND)
        sizer.Add(self.textorefresco, 1, wx.EXPAND)
        sizer_botones.Add(self.AceptarTRUE, 2, wx.CENTER)
        sizer_botones.Add(self.AceptarFALSE, 2, wx.CENTER)
        sizer.Add(sizer_botones, 0, wx.EXPAND)
        self.Panel.SetSizer(sizer)
        self.textorefresco.SetFocus()
        global act
        act=HiloActualizacionComplemento(self)
        act.start()
    def skip(self, event):
        return
    def onNull(self, event):
        pass
    def next(self, event):
        self.progressBar.SetValue(event)
    def TextoRefresco(self, event):
        self.textorefresco.Clear()
        self.textorefresco.AppendText(event)
    def done(self, event):
        self.AceptarTRUE.Enable()
        self.textorefresco.Clear()
        self.textorefresco.AppendText(event)
        self.textorefresco.SetInsertionPoint(0) 
        act.join()
    def error(self, event):
        self.AceptarFALSE.Enable()
        self.textorefresco.Clear()
        self.textorefresco.AppendText(event)
        self.textorefresco.SetInsertionPoint(0) 
        act.join()
    def onAceptarTRUE(self, event):
        if self.IsModal():
            self.EndModal(event.EventObject.Id)
        else:
            self.Destroy()
        os.system("start update.bat")
    def onAceptarFALSE(self, event):
        if self.IsModal():
            self.EndModal(event.EventObject.Id)
        else:
            self.Destroy()
        os.system("start update.bat")
class MyFrame(wx.Frame):
    def __init__(self, *args, **kwds):
        self.name = 'vetube-%s'.format(wx.GetUserId())
        self.instance = wx.SingleInstanceChecker(self.name)
        if self.instance.IsAnotherRunning():
            wx.MessageBox(_('VeTube ya se encuentra en ejecución. Cierra la otra instancia antes de iniciar esta.'), 'Error', wx.ICON_ERROR)
            return False
        dlg = wx.MessageDialog(None, _("Con tu apoyo contribuyes a que este programa siga siendo gratuito. ¿Te unes a nuestra causa?"), _("Atención:"), wx.YES_NO | wx.ICON_ASTERISK)
        dlg.SetYesNoLabels(_("&Aceptar"), _("&Cancelar"))
        if dlg.ShowModal()==wx.ID_YES:
            wx.LaunchDefaultBrowser('https://www.paypal.com/donate/?hosted_button_id=5ZV23UDDJ4C5U')
            dlg.Destroy()
        else: dlg.Destroy()
        self.contador=0
        self.dentro=False
        kwds["style"] = kwds.get("style", 0) | wx.DEFAULT_FRAME_STYLE
        wx.Frame.__init__(self, *args, **kwds)
        self.updater()
        self.SetSize((800, 600))
        self.SetTitle("VeTube")
        self.SetWindowStyle(wx.RESIZE_BORDER | wx.CAPTION | wx.CLOSE_BOX | wx.CLIP_CHILDREN)
        self.handler_keyboard = WXKeyboardHandler(self)
        self.panel_1 = wx.Panel(self, wx.ID_ANY)
        sizer_1 = wx.BoxSizer(wx.VERTICAL)
        self.menu_1 = wx.Button(self.panel_1, wx.ID_ANY, _("&Más opciones"))
        self.menu_1.Bind(wx.EVT_BUTTON, self.opcionesMenu)
        self.menu_1.SetToolTip(_(u"Pulse alt para abrir el menú"))
        self.notebook_1 = wx.Notebook(self.panel_1, wx.ID_ANY)
        sizer_1.Add(self.notebook_1, 1, wx.EXPAND, 0)
        self.tap_1 = wx.Panel(self.notebook_1, wx.ID_ANY)
        self.notebook_1.AddPage(self.tap_1, _("Inicio"))
        sizer_2 = wx.BoxSizer(wx.VERTICAL)
        self.tap_2 = wx.Panel(self.notebook_1, wx.ID_ANY)
        self.notebook_1.AddPage(self.tap_2, _("Favoritos"))
        sizer_favoritos = wx.BoxSizer(wx.VERTICAL)
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
        self.button_2 = wx.Button(self.tap_1, wx.ID_ANY, _("Borrar"))
        self.button_2.Bind(wx.EVT_BUTTON, self.borrarContenido)
        self.button_2.Disable()
        sizer_2.Add(self.button_2, 0, 0, 0)
        self.tap_1.SetSizer(sizer_2)
        label_favoritos = wx.StaticText(self.tap_2, wx.ID_ANY, _("Tus favoritos: "))
        sizer_favoritos.Add(label_favoritos)
        self.list_favorite = wx.ListBox(self.tap_2, wx.ID_ANY, choices=favs)
        self.list_favorite.Bind(wx.EVT_KEY_UP, self.favoritoTeclas)
        sizer_favoritos.Add(self.list_favorite)
        self.button_borrar_favoritos = wx.Button(self.tap_2, wx.ID_ANY, _("&Borrar favorito"))
        self.button_borrar_favoritos.Bind(wx.EVT_BUTTON, self.borrarFavorito)
        sizer_favoritos.Add(self.button_borrar_favoritos,0,0,0)
        self.tap_2.SetSizer(sizer_favoritos)
        self.panel_1.SetSizer(sizer_1)
        self.Layout()
        self.Maximize()
        self.Centre()
        self.Show()
    # Evento que hace aparecer las opciones del menú
    def opcionesMenu(self, event):
        self.menu = wx.Menu()
        self.opciones = wx.Menu()
        self.ayuda = wx.Menu()
        self.menu.AppendSubMenu(self.opciones, _(u"&Opciones"))
        self.opcion_1 = self.opciones.Append(wx.ID_ANY, _("Configuración"))
        self.Bind(wx.EVT_MENU, self.appConfiguracion, self.opcion_1)
        self.opcion_2 = self.opciones.Append(wx.ID_ANY, _("Restablecer los ajustes"))
        self.Bind(wx.EVT_MENU, self.restaurar, self.opcion_2)
        self.menu.AppendSubMenu(self.ayuda, _("&Ayuda"))
        self.apoyo = self.ayuda.Append(wx.ID_ANY, _("Únete a nuestra &causa"))
        self.Bind(wx.EVT_MENU, self.donativo, self.apoyo)
        self.itemPageMain = self.ayuda.Append(wx.ID_ANY, _("&Visita nuestra página de github"))
        self.Bind(wx.EVT_MENU, self.pageMain, self.itemPageMain)
        self.actualizador = self.ayuda.Append(wx.ID_ANY, _("&buscar actualizaciones"))
        self.Bind(wx.EVT_MENU, self.updater, self.actualizador)
        self.acercade = self.menu.Append(wx.ID_ANY, _("Acerca de"))
        self.Bind(wx.EVT_MENU, self.infoApp, self.acercade)
        self.salir = self.menu.Append(wx.ID_EXIT)
        self.Bind(wx.EVT_MENU, self.cerrarVentana, self.salir)
        position = self.menu_1.GetPosition()
        self.PopupMenu(self.menu, position)
        pass
    def pageMain(self, evt): wx.LaunchDefaultBrowser('https://github.com/metalalchemist/VeTube')
    def donativo(self, evt): wx.LaunchDefaultBrowser('https://www.paypal.com/donate/?hosted_button_id=5ZV23UDDJ4C5U')
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
        label_language = wx.StaticText(self.treeItem_1, wx.ID_ANY, _("Idioma de VeTube (Requiere reiniciar)"))
        boxSizer_1.Add(label_language)
        self.choice_language = wx.Choice(self.treeItem_1, wx.ID_ANY, choices=langs)
        self.choice_language.SetSelection(codes.index(idioma))
        boxSizer_1.Add(self.choice_language)
        sizer_4.Add(boxSizer_1, 0, 0, 0)
        self.treeItem_2 = wx.Panel(self.tree_1, wx.ID_ANY)
        self.tree_1.AddPage(self.treeItem_2, _("Voz"))
        sizer_6 = wx.BoxSizer(wx.HORIZONTAL)
        box_2 = wx.StaticBox(self.treeItem_2, -1, _("Opciones del habla"))
        boxSizer_2 = wx.StaticBoxSizer(box_2,wx.VERTICAL)
        self.check_1 = wx.CheckBox(self.treeItem_2, wx.ID_ANY, _("Usar voz sapi en lugar de lector de pantalla."))
        self.check_1.SetValue(sapi)
        self.check_1.Bind(wx.EVT_CHECKBOX, self.checar)
        boxSizer_2.Add(self.check_1)
        self.chk1 = wx.CheckBox(self.treeItem_2, wx.ID_ANY, _("Activar lectura de mensajes automática"))
        self.chk1.SetValue(reader)
        self.chk1.Bind(wx.EVT_CHECKBOX, self.checar1)
        boxSizer_2.Add(self.chk1)
        label_6 = wx.StaticText(self.treeItem_2, wx.ID_ANY, _("Voz: "))
        boxSizer_2 .Add(label_6)
        self.choice_2 = wx.Choice(self.treeItem_2, wx.ID_ANY, choices=lista_voces)
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
        self.boton_prueva = wx.Button(self.treeItem_2, wx.ID_ANY, label=_("&Reproducir prueba."))
        self.boton_prueva.Bind(wx.EVT_BUTTON, self.reproducirPrueva)
        boxSizer_2.Add(self.boton_prueva)
        sizer_6.Add(boxSizer_2, 0, 0, 0)
        self.treeItem_3 = wx.Panel(self.tree_1, wx.ID_ANY)
        self.categoriza=wx.ListCtrl(self.treeItem_3, wx.ID_ANY)
        self.categoriza.EnableCheckBoxes()
        for contador in range(5):
            self.categoriza.InsertItem(contador,mensajes_categorias[contador])
            self.categoriza.CheckItem(contador,check=categ[contador])
        self.categoriza.Focus(0)
        sizer_categoriza = wx.BoxSizer()
        sizer_categoriza.Add(self.categoriza, 1, wx.EXPAND)
        self.treeItem_3.SetSizer(sizer_categoriza)
        self.tree_1.AddPage(self.treeItem_3, _('Categorías'))
        self.treeItem_4 = wx.Panel(self.tree_1, wx.ID_ANY)
        self.check_2 = wx.CheckBox(self.treeItem_4, wx.ID_ANY, _("Reproducir sonidos."))
        self.check_2.SetValue(sonidos)
        self.check_2.Bind(wx.EVT_CHECKBOX, self.mostrarSonidos)
        self.soniditos=wx.ListCtrl(self.treeItem_4, wx.ID_ANY)
        self.soniditos.EnableCheckBoxes()
        for contador in range(len(listasonidos)):
            self.soniditos.InsertItem(contador,mensajes_sonidos[contador])
            self.soniditos.CheckItem(contador,check=listasonidos[contador])
        self.soniditos.Focus(0)
        if sonidos: self.soniditos.Enable()
        else: self.soniditos.Disable()
        sizer_soniditos = wx.BoxSizer()
        sizer_soniditos.Add(self.check_2)
        sizer_soniditos.Add(self.soniditos, 1, wx.EXPAND)
        self.reproducir= wx.Button(self.treeItem_4, wx.ID_ANY, _("&Reproducir"))
        self.reproducir.Bind(wx.EVT_BUTTON, self.reproducirSonidos)
        if sonidos: self.reproducir.Enable()
        else: self.reproducir.Disable()
        sizer_soniditos.Add(self.reproducir)
        self.treeItem_4.SetSizer(sizer_soniditos)
        self.tree_1.AddPage(self.treeItem_4, _('Sonidos'))
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
        leer.silence()
        leer.speak(_("Hola, soy la voz que te acompañará de ahora en adelante a leer los mensajes de tus canales favoritos."))
    def infoApp(self, event): wx.MessageBox(_("Creadores del proyecto:")+"\nCésar Verástegui & Johan G.\n"+_("Descripción:\n Lee en voz alta los mensajes de los directos en youtube, ajusta tus preferencias como quieras y disfruta más tus canales favoritos."), _("Información"), wx.ICON_INFORMATION)
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
    def mostrarSonidos(self,event):
        global sonidos
        if event.IsChecked():
            sonidos=True
            self.soniditos.Enable()
            self.reproducir.Enable()
        else:
            sonidos=False
            self.soniditos.Disable()
            self.reproducir.Disable()
    def checar(self, event):
        global sapi
        if event.IsChecked(): sapi=True
        else: sapi=False
    def checar1(self, event):
        global reader
        if event.IsChecked(): reader=True
        else: reader=False
    def acceder(self, event=None,url=""):
        if not url: url=self.text_ctrl_1.GetValue()
        if url:
            if 'studio' in url:
                pag=url
                pag=pag.split("/")
                pag=pag[-2]
                url="https://www.youtube.com/watch?v="+pag
            try:
                if 'yout' in url: self.chat=ChatDownloader().get_chat(url,message_groups=["messages", "superchat"])
                elif 'twitch' in url: self.chat=ChatDownloader().get_chat(url,message_groups=["messages", "bits","subscriptions","upgrades"])
                else:
                    wx.MessageBox(_("¡Parece que el enlace al cual está intentando acceder no es un enlace válido."), "error.", wx.ICON_ERROR)
                    return
                self.text_ctrl_1.SetValue(url)
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
                self.button_favoritos = wx.Button(self.dialog_mensaje, wx.ID_ANY, _("Añadir a &favoritos"))
                self.button_favoritos.Bind(wx.EVT_BUTTON, self.addFavoritos)
                if self.chat.status=="upcoming": self.button_favoritos.Disable()
                sizer_mensaje_2.Add(self.button_favoritos, 15, wx.ALIGN_CENTER_VERTICAL | wx.ALL, 0)
                sizer_mensaje_2.Realize()
                self.dialog_mensaje.SetSizer(sizer_mensaje_1)
                sizer_mensaje_1.Fit(self.dialog_mensaje)
                self.dialog_mensaje.Centre()
                self.dialog_mensaje.SetEscapeId(self.button_mensaje_detener.GetId())
                if sonidos and listasonidos[6]: wx.adv.Sound(rutasonidos[6]).Play(wx.adv.SOUND_ASYNC)
                leer.speak(_("Ingresando al chat."))
                self.hilo2 = threading.Thread(target=self.iniciarChat)
                self.hilo2.daemon = True
                self.hilo2.start()
                self.dialog_mensaje.ShowModal()
            except Exception as e:
                wx.MessageBox(_("¡Parece que el enlace al cual está intentando acceder no es un enlace válido."), "error.", wx.ICON_ERROR)
                self.text_ctrl_1.SetFocus()
        else:
            wx.MessageBox(_("No se puede  acceder porque el campo de  texto está vacío, debe escribir  algo."), "error.", wx.ICON_ERROR)
            self.text_ctrl_1.SetFocus()
    def borrarContenido(self, event):
        self.text_ctrl_1.SetValue("")
        self.text_ctrl_1.SetFocus()
    def detenerLectura(self, event):
        global yt,pos
        dlg_mensaje = wx.MessageDialog(self.dialog_mensaje, _("¿Desea salir de esta ventana y detener la lectura de los mensajes?"), _("Atención:"), wx.YES_NO | wx.ICON_ASTERISK)
        if dlg_mensaje.ShowModal() == wx.ID_YES:
            self.dentro=False
            self.contador=0
            yt=0
            pos=[]
            for temporal in lista: pos.append(1)
            leer.silence()
            leer.speak(_("ha finalizado la lectura del chat."))
            self.text_ctrl_1.SetValue("")
            self.text_ctrl_1.SetFocus()
            self.dialog_mensaje.Destroy()
            self.text_ctrl_1.SetFocus()
            self.handler_keyboard.unregister_all_keys()
    def guardar(self, event):
        global idioma, rest,categ,lista,listasonidos
        rest=False
        categ=[]
        listasonidos=[]
        for contador in range(len(mensajes_categorias)):
            if self.categoriza.IsItemChecked(contador): categ.append(True)
            else: categ.append(False)
        for contador in range(len(mensajes_sonidos)):
            if self.soniditos.IsItemChecked(contador): listasonidos.append(True)
            else: listasonidos.append(False)
        lista=retornarCategorias()
        if idioma!=codes[self.choice_language.GetSelection()]:
            idioma=codes[self.choice_language.GetSelection()]
            rest=True
        escribirConfiguracion()
        if rest:
            dlg = wx.MessageDialog(None, _("Es necesario reiniciar el programa para aplicar el nuevo idioma. ¿desea reiniciarlo ahora?"), _("Atención:"), wx.YES_NO | wx.ICON_ASTERISK)
            if dlg.ShowModal()==wx.ID_YES: restart.restart_program()
            else: dlg.Destroy()
        self.dialogo_2.Close()
    def borrarEnlace(self,event):
        dlg_2 = wx.MessageDialog(self.dialog_mensaje, _("Está apunto de eliminar del historial aproximadamente ")+str(self.list_box_1.GetCount())+_(" elementos, ¿desea proceder? Esta acción no se puede desacer."), _("Atención:"), wx.YES_NO | wx.ICON_ASTERISK)
        dlg_2.SetYesNoLabels(_("&Eliminar"), _("&Cancelar"))
        if self.list_box_1.GetCount() <= 0: wx.MessageBox(_("No hay elementos que borrar"), "Error", wx.ICON_ERROR)
        elif dlg_2.ShowModal()==wx.ID_YES:
            self.list_box_1.Clear()
            self.list_box_1.SetFocus()
    def restaurar(self, event):
        global lista
        self.dlg_3 = wx.MessageDialog(self, _("Estás apunto de reiniciar la configuración a sus valores predeterminados, ¿Deseas proceder?"), _("Atención:"), wx.YES_NO | wx.ICON_ASTERISK)
        if self.dlg_3.ShowModal()==wx.ID_YES:
            lista=[]
            asignarConfiguracion()
            escribirConfiguracion()
            lista=retornarCategorias()
    def mostrarBoton(self, event):
        if self.text_ctrl_1.GetValue() != "":
            self.button_1.Enable()
            self.button_2.Enable()
        else:
            self.button_1.Disable()
            self.button_2.Disable()
    def cambiarVoz(self, event):    
        global voz
        voz=event.GetSelection()
        leer.set_voice(lista_voces[event.GetSelection()])
    def historialItemsTeclas(self, event):
        event.Skip()
        if event.GetKeyCode() == 127: self.list_box_1.Delete(self.list_box_1.GetSelection())
        if event.GetKeyCode() == 32:
            leer.silence()
            leer.speak(self.list_box_1.GetString(self.list_box_1.GetSelection()))
    def iniciarChat(self):
        global info_dict
        ydlop = {'ignoreerrors': True, 'extract_flat': 'in_playlist', 'dump_single_json': True, 'quiet': True}
        with YoutubeDL(ydlop) as ydl: info_dict = ydl.extract_info(self.text_ctrl_1.GetValue(), download=False)
        try: self.label_dialog.SetLabel(info_dict.get('title')+', '+str(info_dict["view_count"])+_(' reproducciones'))
        except: pass
        if 'yout' in self.text_ctrl_1.GetValue(): self.recibirYT()
        elif 'twitch' in self.text_ctrl_1.GetValue(): self.recibirTwich()
        self.registrarTeclas()
    def elementoAnterior(self):
        global pos
        if self.dentro:
            if lista[yt][0]=='General':
                if self.list_box_1.GetCount() <= 0: lector.speak(_("no hay elementos en el historial"))
                else:
                    if self.contador>0: self.contador-=1
                    lector.speak(self.list_box_1.GetString(self.contador))
            else:
                if len(lista[yt]) <= 1: lector.speak(_("no hay elementos en el historial"))
                else:
                    if pos[yt]>1: pos[yt]-=1
                    lector.speak(lista[yt][pos[yt]])
        if sonidos: self.reproducirMsg()
    def elementoSiguiente(self):
        global pos
        if self.dentro:
            if lista[yt][0]=='General':
                if self.list_box_1.GetCount() <= 0: lector.speak(_("no hay elementos en el historial"))
                else:
                    if self.contador<self.list_box_1.GetCount()-1: self.contador+=1
                    lector.speak(self.list_box_1.GetString(self.contador))
            else:
                if len(lista[yt]) <= 1: lector.speak(_("no hay elementos en el historial"))
                else:
                    if pos[yt]<len(lista[yt])-1: pos[yt]+=1
                    lector.speak(lista[yt][pos[yt]])
        if sonidos: self.reproducirMsg()
    def copiar(self):
        if self.dentro:
            if lista[yt][0]=='General':
                if self.list_box_1.GetCount() <= 0: lector.speak(_("no hay elementos en el historial"))
                else:
                    copy(self.list_box_1.GetString(self.contador))
                    lector.speak(_("¡Copiado!"))
            else:
                if len(lista[yt]) <= 1: lector.speak(_("no hay elementos en el historial"))
                else:
                    copy(lista[yt][pos[yt]])
                    lector.speak(_("¡Copiado!"))
    def elementoInicial(self):
        global pos
        if self.dentro:
            if lista[yt][0]=='General':
                if self.list_box_1.GetCount() <= 0: lector.speak(_("no hay elementos en el historial"))
                else:
                    self.contador=0
                    lector.speak(self.list_box_1.GetString(self.contador))
            else:
                if len(lista[yt]) <= 1: lector.speak(_("no hay elementos en el historial"))
                else:
                    pos[yt]=1
                    lector.speak(lista[yt][pos[yt]])
        if sonidos: self.reproducirMsg()
    def elementoFinal(self):
        global pos
        if self.dentro:
            if lista[yt][0]=='General':
                if self.list_box_1.GetCount() <= 0: lector.speak(_("no hay elementos en el historial"))
                else:
                    self.contador=self.list_box_1.GetCount()-1
                    lector.speak(self.list_box_1.GetString(self.contador))
            else:
                if len(lista[yt]) <= 1: lector.speak(_("no hay elementos en el historial"))
                else:
                    pos[yt]=len(lista[yt])-1
                    lector.speak(lista[yt][pos[yt]])
        if sonidos: self.reproducirMsg()
    def callar(self):
        global reader
        if reader:
            reader=False
            leer.silence()
        else: reader=True
        lector.speak(_("Lectura automática activada.")if reader else _("Lectura automática  desactivada."))
    def cerrarVentana(self, event):
        dialogo_cerrar = wx.MessageDialog(self, _("¿está seguro que desea salir del programa?"), _("¡atención!:"), wx.YES_NO | wx.ICON_ASTERISK)
        if dialogo_cerrar.ShowModal()==wx.ID_YES: self.Destroy()
    def retornarMensaje(self):
        if self.list_box_1.GetCount()>0 and lista[yt][0]=='General': return self.list_box_1.GetString(self.contador)
        if lista[yt][0]!='General' and len(lista[yt])>0: return lista[yt][pos[yt]]
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
    def reproducirMsg(self):
        if lista[yt][0]=='General':
            if self.contador==0 or self.contador==self.list_box_1.GetCount()-1: playsound("sounds/orilla.mp3",False)
            else: playsound("sounds/msj.mp3",False)
        else:
            if pos[yt]<=1 or pos[yt]==len(lista[yt])-1: playsound("sounds/orilla.mp3",False)
            else: playsound("sounds/msj.mp3",False)
    def addFavoritos(self, event):
        if len(favorite)<=0:
            self.list_favorite.Append(info_dict.get('title')+': '+self.text_ctrl_1.GetValue())
            favorite.append({'titulo': info_dict.get('title'), 'url': self.text_ctrl_1.GetValue()})
            escribirFavorito()
            lector.speak("Se a añadido el elemento a favoritos")
        else:
            encontrado=False
            for dato in favorite:
                if dato['titulo']==info_dict.get('title'):
                    encontrado=True
                    break
            if encontrado: wx.MessageBox(_("al parecer ya tienes ese enlace en tus favoritos"), "error.", wx.ICON_ERROR)
            else:
                self.list_favorite.Append(info_dict.get('title')+': '+self.text_ctrl_1.GetValue())
                favorite.append({'titulo': info_dict.get('title'), 'url': self.text_ctrl_1.GetValue()})
                escribirFavorito()
                lector.speak(_("Se a añadido el elemento a favoritos"))
    def updater(self,event=None):
        r = urllib.request.urlopen('https://api.github.com/repos/metalalchemist/VeTube/releases').read()
        gitJson = json.loads(r.decode('utf-8'))
        if gitJson[0]["tag_name"] != version:
            dlg = wx.MessageDialog(None, _("Una nueva  versión de VeTube está disponible. ¿desea descargarla aora?"), _("Atención:"), wx.YES_NO | wx.ICON_ASTERISK)
            if dlg.ShowModal()==wx.ID_YES:
                global urlDescarga
                urlDescarga = gitJson[0]['body']
                urlDescarga=urlDescarga.split('](')
                urlDescarga=urlDescarga[1]
                urlDescarga=urlDescarga.split(')')
                urlDescarga=urlDescarga[0]
                dlg.Destroy
                dlg = ActualizacionDialogo(self)
                result = dlg.ShowModal()
            else: dlg.Destroy()
        else:
            if self.GetTitle(): wx.MessageBox(_("Al parecer tienes la última versión del programa"), _("Información"), wx.ICON_INFORMATION)
    def borrarFavorito(self, event=None):
        if self.list_favorite.GetCount() <= 0: wx.MessageBox(_("No hay elementos que borrar"), "Error", wx.ICON_ERROR)
        else:
            favorite.pop(self.list_favorite.GetSelection())
            self.list_favorite.Delete(self.list_favorite.GetSelection())
            escribirFavorito()
    def favoritoTeclas(self,event):
        event.Skip()
        if event.GetKeyCode() == 32: self.acceder(url=favorite[self.list_favorite.GetSelection()]['url'])
    def recibirYT(self):
        global lista
        for message in self.chat:
            if message['message_type']=='paid_message' or message['message_type']=='paid_sticker':
                if message['message']!=None:
                    if categ[1]:
                        for contador in range(len(lista)):
                            if lista[contador][0]=='Donativos':
                                lista[contador].append(str(message['money']['amount'])+message['money']['currency']+ ', '+message['author']['name'] +': ' +message['message'])
                                break
                        if sonidos and self.chat.status!="past" and listasonidos[3]: playsound(rutasonidos[3],False)
                    self.list_box_1.Append(str(message['money']['amount'])+message['money']['currency']+ ', '+message['author']['name'] +': ' +message['message'])
                    if lista[yt][0]=='Donativos':
                        if reader:
                            if sapi: leer.speak(str(message['money']['amount'])+message['money']['currency']+ ', '+message['author']['name'] +': ' +message['message'])
                            else: lector.speak(str(message['money']['amount'])+message['money']['currency']+ ', '+message['author']['name'] +': ' +message['message'])
                else:
                    if categ[1]:
                        for contador in range(len(lista)):
                            if lista[contador][0]=='Donativos':
                                lista[contador].append(str(message['money']['amount'])+message['money']['currency']+ ', '+message['author']['name'])
                                break
                        if sonidos and self.chat.status!="past" and listasonidos[3]: playsound(rutasonidos[3],False)
                    self.list_box_1.Append(str(message['money']['amount'])+message['money']['currency']+ ', '+message['author']['name'])
                    if lista[yt][0]=='Donativos':
                        if reader:
                            if sapi: leer.speak(str(message['money']['amount'])+message['money']['currency']+ ', '+message['author']['name'])
                            else: lector.speak(str(message['money']['amount'])+message['money']['currency']+ ', '+message['author']['name'])
            if 'header_secondary_text' in message:
                for t in message['author']['badges']:
                    if categ[0]:
                        for contador in range(len(lista)):
                            if lista[contador][0]=='Miembros':
                                lista[contador].append(message['author']['name']+ _(' se a conectado al chat. ')+t['title'])
                                break
                        if sonidos and self.chat.status!="past" and listasonidos[2]: playsound(rutasonidos[2],False)
                    self.list_box_1.Append(message['author']['name']+ _(' se a conectado al chat. ')+t['title'])
                if lista[yt][0]=='Miembros':
                    if reader:
                        if sapi: leer.speak(message['author']['name']+ _(' se a conectado al chat. ')+t['title'])
                        else: lector.speak(message['author']['name']+ _(' se a conectado al chat. ')+t['title'])
            if 'badges' in message['author']:
                for t in message['author']['badges']:
                    if 'Owner' in t['title']:
                        if categ[2]:
                            for contador in range(len(lista)):
                                if lista[contador][0]=='Moderadores':
                                    lista[contador].append(message['author']['name'] +': ' +message['message'])
                                    break
                            if sonidos and self.chat.status!="past" and listasonidos[4]: playsound(rutasonidos[7],False)
                        self.list_box_1.Append(_('Propietario ')+message['author']['name'] +': ' +message['message'])
                        if lista[yt][0]=='Moderadores':
                            if reader:
                                if sapi: leer.speak(message['author']['name'] +': ' +message['message'])
                                else: lector.speak(message['author']['name'] +': ' +message['message'])
                    if 'Moderator' in t['title']:
                        if categ[2]:
                            for contador in range(len(lista)):
                                if lista[contador][0]=='Moderadores':
                                    lista[contador].append(message['author']['name'] +': ' +message['message'])
                                    break
                            if sonidos and self.chat.status!="past" and listasonidos[4]: playsound(rutasonidos[4],False)
                        self.list_box_1.Append(_('Moderador ')+message['author']['name'] +': ' +message['message'])
                        if lista[yt][0]=='Moderadores':
                            if reader:
                                if sapi: leer.speak(message['author']['name'] +': ' +message['message'])
                                else: lector.speak(message['author']['name'] +': ' +message['message'])
                    if 'Member' in t['title']:
                        if message['message'] == None: pass
                        else:
                            if categ[0]:
                                for contador in range(len(lista)):
                                    if lista[contador][0]=='Miembros':
                                        lista[contador].append(message['author']['name'] +': ' +message['message'])
                                        break
                                if sonidos and self.chat.status!="past" and listasonidos[1]: playsound(rutasonidos[1],False)
                            self.list_box_1.Append(_('Miembro ')+message['author']['name'] +': ' +message['message'])
                            if lista[yt][0]=='Miembros':
                                if reader:
                                    if sapi: leer.speak(message['author']['name'] +': ' +message['message'])
                                    else: lector.speak(message['author']['name'] +': ' +message['message'])
                    if 'Verified' in t['title']:
                        if categ[3]:
                            for contador in range(len(lista)):
                                if lista[contador][0]=='Usuarios Verificados':
                                    lista[contador].append(message['author']['name'] +': ' +message['message'])
                                    break
                            if sonidos and self.chat.status!="past" and listasonidos[5]: playsound(rutasonidos[5],False)
                        self.list_box_1.Append(message['author']['name'] +_(' (usuario verificado): ') +message['message'])
                        if lista[yt][0]=='Usuarios Verificados':
                            if reader:
                                if sapi: leer.speak(message['author']['name'] +': ' +message['message'])
                                else: lector.speak(message['author']['name'] +': ' +message['message'])
            else:
                if message['message_type']=='paid_message' or message['message_type']=='paid_sticker': pass
                else:
                    if self.dentro:
                        if lista[yt][0]=='General':
                            if reader:
                                if sapi: leer.speak(message['author']['name'] +': ' +message['message'])
                                else: lector.speak(message['author']['name'] +': ' +message['message'])
                        if sonidos and self.chat.status!="past" and listasonidos[0]: playsound(rutasonidos[0],False)
                        self.list_box_1.Append(message['author']['name'] +': ' +message['message'])
                    else:
                        exit()
                        self.hilo2.join()
    def recibirTwich(self):
        for message in self.chat:
            anadido=False
            if 'Cheer' in message['message'] and not anadido:
                divide=message['message'].split()
                dinero=divide[0]
                divide=" ".join(divide[1:])
                if categ[1]:
                    for contador in range(len(lista)):
                        if lista[contador][0]=='Donativos':
                            lista[contador].append(dinero+', '+message['author']['name']+': '+divide)
                            break
                    if sonidos and self.chat.status!="past" and listasonidos[3]: playsound(rutasonidos[3],False)
                self.list_box_1.Append(dinero+', '+message['author']['name']+': '+divide)
                if lista[yt][0]=='Donativos':
                    if reader:
                        if sapi: leer.speak(dinero+', '+message['author']['name']+': '+divide)
                        else: lector.speak(dinero+', '+message['author']['name']+': '+divide)
                anadido=True
            if message['message_type']=='subscription' and not anadido:
                if categ[0]:
                    for contador in range(len(lista)):
                        if lista[contador][0]=='Miembros':
                            lista[contador].append(message['author']['name']+_(' se ha suscrito en el nivel ')+message['subscription_plan_name']+_(' por ')+str(message['cumulative_months'])+_(' meses!'))
                            break
                    if sonidos and self.chat.status!="past" and listasonidos[2]: playsound(rutasonidos[2],False)
                self.list_box_1.Append(message['author']['name']+_(' se ha suscrito en el nivel ')+message['subscription_plan_name']+_(' por ')+str(message['cumulative_months'])+_(' meses!'))
                if lista[yt][0]=='Miembros':
                    if reader:
                        if sapi: leer.speak(message['author']['name']+_(' se ha suscrito en el nivel ')+message['subscription_plan_name']+_(' por ')+str(message['cumulative_months'])+_(' meses!'))
                        else: lector.speak(message['author']['name']+_(' se ha suscrito en el nivel ')+message['subscription_plan_name']+_(' por ')+str(message['cumulative_months'])+_(' meses!'))
                anadido=True
            if message['message_type']=='mystery_subscription_gift' and not anadido:
                if categ[0]:
                    for contador in range(len(lista)):
                        if lista[contador][0]=='Miembros':
                            lista[contador].append(message['author']['name']+_(' regaló una suscripción de nivel ')+message['subscription_type']+_(' a la  comunidad, ha regalado un total de ')+str(message['sender_count'])+_(' suscripciones!'))
                            break
                    if sonidos and self.chat.status!="past" and listasonidos[2]: playsound(rutasonidos[2],False)
                self.list_box_1.Append(message['author']['name']+_(' regaló una suscripción de nivel ')+message['subscription_type']+_(' a la  comunidad, ha regalado un total de ')+str(message['sender_count'])+_(' suscripciones!'))
                if lista[yt][0]=='Miembros':
                    if reader:
                        if sapi: leer.speak(message['author']['name']+_(' regaló una suscripción de nivel ')+message['subscription_type']+_(' a la  comunidad, ha regalado un total de ')+str(message['sender_count'])+_(' suscripciones!'))
                        else: lector.speak(message['author']['name']+_(' regaló una suscripción de nivel ')+message['subscription_type']+_(' a la  comunidad, ha regalado un total de ')+str(message['sender_count'])+_(' suscripciones!'))
                anadido=True
            if message['message_type']=='subscription_gift' and not anadido:
                if categ[0]:
                    for contador in range(len(lista)):
                        if lista[contador][0]=='Miembros':
                            lista[contador].append(message['author']['name']+_(' a regalado una suscripción a ')+message['gift_recipient_display_name']+_(' en el nivel ')+message['subscription_plan_name']+_(' por ')+str(message['number_of_months_gifted'])+_(' meses!'))
                            break
                    if sonidos and self.chat.status!="past" and listasonidos[2]: playsound(rutasonidos[2],False)
                self.list_box_1.Append(message['author']['name']+_(' a regalado una suscripción a ')+message['gift_recipient_display_name']+_(' en el nivel ')+message['subscription_plan_name']+_(' por ')+str(message['number_of_months_gifted'])+_(' meses!'))
                if lista[yt][0]=='Miembros':
                    if reader:
                        if sapi: leer.speak(message['author']['name']+_(' a regalado una suscripción a ')+message['gift_recipient_display_name']+_(' en el nivel ')+message['subscription_plan_name']+_(' por ')+str(message['number_of_months_gifted'])+_(' meses!'))
                        else: lector.speak(message['author']['name']+_(' a regalado una suscripción a ')+message['gift_recipient_display_name']+_(' en el nivel ')+message['subscription_plan_name']+_(' por ')+str(message['number_of_months_gifted'])+_(' meses!'))
                anadido=True
            if message['message_type']=='resubscription' and not anadido:
                mssg=message['message'].split('! ')
                mssg=str(mssg[1:])
                if categ[0]:
                    for contador in range(len(lista)):
                        if lista[contador][0]=='Miembros':
                            lista[contador].append(message['author']['name']+_(' ha renovado su suscripción en el nivel ')+message['subscription_plan_name']+_('. lleva suscrito por')+str(message['cumulative_months'])+_(' meses! ')+mssg)
                            break
                    if sonidos and self.chat.status!="past" and listasonidos[2]: playsound(rutasonidos[2],False)
                self.list_box_1.Append(message['author']['name']+_(' ha renovado su suscripción en el nivel ')+message['subscription_plan_name']+_('. lleva suscrito por')+str(message['cumulative_months'])+_(' meses! ')+mssg)
                if lista[yt][0]=='Miembros':
                    if reader:
                        if sapi: leer.speak(message['author']['name']+_(' ha renovado su suscripción en el nivel ')+message['subscription_plan_name']+_('. lleva suscrito por')+str(message['cumulative_months'])+_(' meses!')+mssg)
                        else: lector.speak(message['author']['name']+_(' ha renovado su suscripción en el nivel ')+message['subscription_plan_name']+_('. lleva suscrito por')+str(message['cumulative_months'])+_(' meses!')+mssg)
                anadido=True
            if 'badges' in message['author']:
                for t in message['author']['badges']:
                    if 'Moderator' in t['title']:
                        if categ[2]:
                            for contador in range(len(lista)):
                                if lista[contador][0]=='Moderadores':
                                    lista[contador].append(message['author']['name'] +': ' +message['message'])
                                    break
                            if sonidos and self.chat.status!="past" and listasonidos[4]: playsound(rutasonidos[4],False)
                        self.list_box_1.Append(_('Moderador ')+message['author']['name'] +': ' +message['message'])
                        if lista[yt][0]=='Moderadores':
                            if reader:
                                if sapi: leer.speak(message['author']['name'] +': ' +message['message'])
                                else: lector.speak(message['author']['name'] +': ' +message['message'])
                    elif 'Subscriber' in t['title'] and not anadido:
                        if categ[0]:
                            for contador in range(len(lista)):
                                if lista[contador][0]=='Miembros':
                                    lista[contador].append(message['author']['name'] +': ' +message['message'])
                                    break
                            if sonidos and self.chat.status!="past" and listasonidos[1]: playsound(rutasonidos[1],False)
                        self.list_box_1.Append(_('Miembro ')+message['author']['name'] +': ' +message['message'])
                        if lista[yt][0]=='Miembros':
                            if reader:
                                if sapi: leer.speak(message['author']['name'] +': ' +message['message'])
                                else: lector.speak(message['author']['name'] +': ' +message['message'])
                    elif 'Verified' in t['title']:
                        if categ[3]:
                            for contador in range(len(lista)):
                                if lista[contador][0]=='Usuarios Verificados':
                                    lista[contador].append(message['author']['name'] +': ' +message['message'])
                                    break
                            if sonidos and self.chat.status!="past" and listasonidos[5]: playsound(rutasonidos[5],False)
                        self.list_box_1.Append(message['author']['name'] +_(' (usuario verificado): ') +message['message'])
                        if lista[yt][0]=='Usuarios Verificados':
                            if reader:
                                if sapi: leer.speak(message['author']['name'] +': ' +message['message'])
                                else: lector.speak(message['author']['name'] +': ' +message['message'])
                    else:
                        if lista[yt][0]=='General':
                            if reader:
                                if sapi: leer.speak(message['author']['name'] +': ' +message['message'])
                                else: lector.speak(message['author']['name'] +': ' +message['message'])
                            if sonidos and self.chat.status!="past" and listasonidos[0]: playsound(rutasonidos[0],False)
                        self.list_box_1.Append(message['author']['name'] +': ' +message['message'])
            else:
                if self.dentro:
                    if lista[yt][0]=='General':
                        if reader:
                            if sapi: leer.speak(message['author']['name'] +': ' +message['message'])
                            else: lector.speak(message['author']['name'] +': ' +message['message'])
                        if sonidos and self.chat.status!="past" and listasonidos[0]: playsound(rutasonidos[0],False)
                    self.list_box_1.Append(message['author']['name'] +': ' +message['message'])
                else:
                    exit()
                    self.hilo2.join()
    def avanzarCategorias(self):
        global yt
        if yt<len(lista)-1: yt+=1
        else: yt=0
        lector.speak(lista[yt][0])
    def retrocederCategorias(self):
        global yt
        if yt<=0: yt=len(lista)-1
        else: yt-=1
        lector.speak(lista[yt][0])
    def destacarMensaje(self):
        global lista,pos
        encontrado=False
        contador=0
        for coso in lista:
            if coso[0]=='Favoritos': encontrado=True
        if not encontrado: lista.append([_('Favoritos')])
        for contador in range(len(lista)):
            if lista[contador]=='Favoritos': break
        if lista[yt][0]=='General': lista[contador].append(self.list_box_1.GetString(self.contador))
        else: lista[contador].append(lista[yt][pos[yt]])
        lector.speak(_('Se agregó el elemento a la lista de favoritos...'))
    def reproducirSonidos(self,event): playsound(rutasonidos[self.soniditos.GetFocusedItem()], False)
    def iniciarBusqueda(self):
        self.my_dialog = wx.Dialog(self, wx.ID_ANY, _("escriba el término de su búsqueda"))
        sizer_mensaje = wx.BoxSizer(wx.HORIZONTAL)
        self.text_box = wx.TextCtrl(self.my_dialog, wx.ID_ANY,"", style=wx.TE_CENTRE | wx.TE_PROCESS_ENTER)
        self.text_box.Bind(wx.EVT_TEXT, self.mostrarBuscar)
        self.text_box.Bind(wx.EVT_TEXT_ENTER, self.buscar)
        sizer_mensaje.Add(self.text_box, 0, 0, 0)
        self.buttonbuscar = wx.Button(self.my_dialog, wx.ID_ANY, _("&Buscar"))
        self.buttonbuscar.Bind(wx.EVT_BUTTON,self.buscar)
        sizer_mensaje.Add(self.buttonbuscar,0,0,0)
        cancelar = wx.Button(self.my_dialog, wx.ID_CLOSE, _("&Cerrar"))
        sizer_mensaje.Add(cancelar,0,0,0)
        self.my_dialog.SetSizer(sizer_mensaje)
        sizer_mensaje.Fit(self.my_dialog)
        self.my_dialog.Centre()
        self.my_dialog.SetEscapeId(cancelar.GetId())
        self.my_dialog.ShowModal()
    def mostrarBuscar(self, event):
        if self.text_box.GetValue() != "": self.buttonbuscar.Enable()
        else: self.buttonbuscar.Disable()
    def buscar(self, event):
        if self.text_box.GetValue():
            lista.append([self.text_box.GetValue()])
            pos.append(1)
            self.my_dialog.Close()
            for busqueda in range(self.list_box_1.GetCount()):
                if self.text_box.GetValue() in self.list_box_1.GetString(busqueda).lower(): lista[-1].append(self.list_box_1.GetString(busqueda))
        else:
            wx.MessageBox(_("No hay nada que buscar porque el campo de  texto está vacío, debe escribir  algo."), "error.", wx.ICON_ERROR)
            self.text_box.SetFocus()
    def borrarBuffer(self):
        if lista[yt][0]!='General' and lista[yt][0]!='Miembros' and lista[yt][0]!='Donativos' and lista[yt][0]!='Moderadores' and lista[yt][0]!='Usuarios Verificados':
            lista.pop()
            pos.pop()
            lector.speak(_('Se eliminó el buffer'))
        else: lector.speak(_('No es posible borrar este buffer'))
    def desactivarSonidos(self):
        global sonidos
        sonidos=False if sonidos else True
        lector.speak(_("Sonidos activados.") if sonidos else _("Sonidos desactivados"))
    def registrarTeclas(self):
        leerTeclas()
        try: self.handler_keyboard.register_keys(eval(mis_teclas))
        except: lector.speak(_("hubo un error al registrar los atajos de teclado globales."))
class MyApp(wx.App):
    def OnInit(self):
        self.frame = MyFrame(None, wx.ID_ANY, "")
        self.SetTopWindow(self.frame)
        self.frame.Show()
        return True
app = MyApp(0)
app.MainLoop()