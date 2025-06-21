	def createEditor(self,event=None):
		try: self.key_config.mis_teclas=eval(self.key_config.mis_teclas)
		except TypeError: pass
		if not self.dentro: self.handler_keyboard.register_keys(self.key_config.mis_teclas)
		self.dlg_teclado = wx.Dialog(None, wx.ID_ANY, _("Editor de combinaciones de teclado para Vetube"))
		sizer = wx.BoxSizer(wx.VERTICAL)
		label_editor = wx.StaticText(self.dlg_teclado, wx.ID_ANY, _("&Selecciona la combinación de teclado a editar"))
		self.combinaciones= wx.ListCtrl(self.dlg_teclado, wx.ID_ANY, style=wx.LC_REPORT)
		self.combinaciones.InsertColumn(0, _("acción: "))
		self.combinaciones.InsertColumn(1, _("combinación de teclas: "))
		for i in range(len(mensaje_teclas)): self.combinaciones.InsertItem(i, mensaje_teclas[i])
		c=0
		for valor in self.key_config.mis_teclas:
			self.combinaciones.SetItem(c, 1, valor)
			c+=1
		self.combinaciones.Bind(wx.EVT_LIST_ITEM_ACTIVATED, self.editarTeclas)
		self.combinaciones.Focus(0)
		self.combinaciones.SetFocus()
		editar= wx.Button(self.dlg_teclado, -1, _(u"&Editar"))
		editar.Bind(wx.EVT_BUTTON, self.editarTeclas)
		editar.SetDefault()
		restaurar=wx.Button(self.dlg_teclado, -1, _(u"&restaurar combinaciones por defecto"))
		restaurar.Bind(wx.EVT_BUTTON, self.restaurarTeclas)
		close = wx.Button(self.dlg_teclado, wx.ID_CANCEL, _(u"&Cerrar"))
		close.Bind(wx.EVT_BUTTON,self.cierraEditor)
		firstSizer = wx.BoxSizer(wx.HORIZONTAL)
		firstSizer.Add(label_editor, 0, wx.ALL, 5)
		firstSizer.Add(self.combinaciones, 0, wx.ALL, 5)
		secondSizer = wx.BoxSizer(wx.HORIZONTAL)
		secondSizer.Add(editar, 0, wx.ALL, 5)
		secondSizer.Add(restaurar, 0, wx.ALL, 5)
		secondSizer.Add(close, 0, wx.ALL, 5)
		sizer.Add(firstSizer, 0, wx.ALL, 5)
		sizer.Add(secondSizer, 0, wx.ALL, 5)
		self.dlg_teclado.SetSizerAndFit(sizer)
		self.dlg_teclado.Centre()
		self.dlg_teclado.ShowModal()
		self.dlg_teclado.Destroy()
		wx.CallLater(100,self.comprobar)
	def comprobar(self):
		if bool(self.dlg_teclado): self.dlg_teclado.Destroy()
	def editarTeclas(self, event):
		indice=self.combinaciones.GetFocusedItem()
		if not self.nueva_combinacion: self.texto=self.combinaciones.GetItem(indice,1).GetText()
		self.dlg_editar_combinacion = wx.Dialog(self.dlg_teclado, wx.ID_ANY, _("Editando la combinación de teclas para %s") % mensaje_teclas[indice])
		sizer = wx.BoxSizer(wx.VERTICAL)
		firstSizer = wx.BoxSizer(wx.HORIZONTAL)
		sizer_check = wx.BoxSizer(wx.HORIZONTAL)
		# el sizer para los botones
		sizer_buttons = wx.BoxSizer(wx.HORIZONTAL)
		groupbox = wx.StaticBox(self.dlg_editar_combinacion, wx.ID_ANY, _("Selecciona las teclas que quieres usar"))
		# el sizer para el agrupamiento
		sizer_groupbox = wx.StaticBoxSizer(groupbox, wx.VERTICAL)
		self.check_ctrl = wx.CheckBox(self.dlg_editar_combinacion, wx.ID_ANY, _("&Control"))
		if 'control' in self.texto: self.check_ctrl.SetValue(True)
		self.check_alt = wx.CheckBox(self.dlg_editar_combinacion, wx.ID_ANY, _("&Alt"))
		if 'alt' in self.texto: self.check_alt.SetValue(True)
		self.check_shift = wx.CheckBox(self.dlg_editar_combinacion, wx.ID_ANY, _("&Shift"))
		if 'shift' in self.texto: self.check_shift.SetValue(True)
		self.check_win = wx.CheckBox(self.dlg_editar_combinacion, wx.ID_ANY, _("&Windows"))
		if 'win' in self.texto: self.check_win.SetValue(True)
		self.teclas = ["return", "tab", "space", "back", "delete", "home", "end", "pageup", "pagedown", "up", "down", "left", "right", "f1", "f2", "f3", "f4", "f5", "f6", "f7", "f8", "f9", "f10", "f11", "f12", "0", "1", "2", "3", "4", "5", "6", "7", "8", "9", "a", "b", "c", "d", "e", "f", "g", "h", "i", "j", "k", "l", "m", "n", "o", "p", "q", "r", "s", "t", "u", "v", "w", "x", "y", "z"]
		label_tecla = wx.StaticText(self.dlg_editar_combinacion, wx.ID_ANY, _("&Selecciona una tecla para la combinación"))
		self.combo_tecla = wx.ComboBox(self.dlg_editar_combinacion, wx.ID_ANY, choices=self.teclas, style=wx.CB_DROPDOWN|wx.CB_READONLY)
		texto=self.texto.split('+')
		self.combo_tecla.SetValue(texto[-1])
		self.editar= wx.Button(self.dlg_editar_combinacion, -1, _(u"&Aplicar nueva combinación de teclado"))
		self.editar.Bind(wx.EVT_BUTTON, self.editarTeclas2)
		self.editar.SetDefault()
		close = wx.Button(self.dlg_editar_combinacion, wx.ID_CANCEL, _(u"&Cerrar"))
		close.Bind(wx.EVT_BUTTON,self.berifica)
		sizer_check.Add(self.check_ctrl, 0, wx.ALL, 5)
		sizer_check.Add(self.check_alt, 0, wx.ALL, 5)
		sizer_check.Add(self.check_shift, 0, wx.ALL, 5)
		sizer_check.Add(self.check_win, 0, wx.ALL, 5)
		sizer_groupbox.Add(sizer_check, 0, wx.ALL, 5)
		sizer.Add(sizer_groupbox, 0, wx.ALL, 5)
		firstSizer.Add(label_tecla, 0, wx.ALL, 5)
		firstSizer.Add(self.combo_tecla, 0, wx.ALL, 5)
		sizer_buttons.Add(self.editar, 0, wx.ALL, 5)
		sizer_buttons.Add(close, 0, wx.ALL, 5)
		sizer.Add(firstSizer, 0, wx.ALL, 5)
		sizer.Add(sizer_buttons, 0, wx.ALL, 5)
		self.dlg_editar_combinacion.SetSizerAndFit(sizer)
		self.dlg_editar_combinacion.Centre()
		self.dlg_editar_combinacion.ShowModal()
		self.dlg_editar_combinacion.Destroy()
	def editarTeclas2(self, event):
		indice=self.combinaciones.GetFocusedItem()
		texto=self.combinaciones.GetItem(indice,1).GetText()
		tecla=self.combo_tecla.GetValue()
		ctrl=self.check_ctrl.GetValue()
		alt=self.check_alt.GetValue()
		shift=self.check_shift.GetValue()
		win=self.check_win.GetValue()
		self.nueva_combinacion=tecla
		if shift: self.nueva_combinacion="shift+"+self.nueva_combinacion
		if alt: self.nueva_combinacion="alt+"+self.nueva_combinacion
		if ctrl: self.nueva_combinacion="control+"+self.nueva_combinacion
		if win: self.nueva_combinacion="win+"+self.nueva_combinacion
		if not ctrl and not alt and not win and not shift:
			wx.MessageBox(_("Debe escoger al menos una tecla de las casillas de berificación"), "error.", wx.ICON_ERROR)
			return
		for busc in range(self.combinaciones.GetItemCount()):
			if busc== indice: continue
			if self.nueva_combinacion == self.combinaciones.GetItem(busc,1).GetText():
				wx.MessageBox(_("esta combinación ya está siendo usada en la función %s") % mensaje_teclas[busc], "error.", wx.ICON_ERROR)
				return
		if self.texto in self.handler_keyboard.active_keys:
			self.handler_keyboard.unregister_key(self.combinaciones.GetItem(indice,1).GetText(),self.key_config.mis_teclas[self.combinaciones.GetItem(indice,1).GetText()])
			self.handler_keyboard.register_key(self.nueva_combinacion,self.key_config.mis_teclas[self.combinaciones.GetItem(indice,1).GetText()])
		self.dlg_editar_combinacion.Destroy()
		wx.CallAfter(self.correccion)
	def correccion(self):
		if self.nueva_combinacion not in self.handler_keyboard.active_keys:
			wx.MessageBox(_("esa combinación está siendo usada por el sistema"), "error.", wx.ICON_ERROR)
			self.handler_keyboard.register_key(self.texto,self.key_config.mis_teclas[self.combinaciones.GetItem(self.combinaciones.GetFocusedItem(),1).GetText()])
		else:
			self.texto=self.nueva_combinacion
			self.nueva_combinacion=""
		self.key_config.leerTeclas()
		self.key_config.mis_teclas=self.key_config.mis_teclas.replace(self.combinaciones.GetItem(self.combinaciones.GetFocusedItem(),1).GetText(),self.texto)
		with open("keys.txt", "w") as fichero: fichero.write(self.key_config.mis_teclas)
		self.key_config.mis_teclas=eval(self.key_config.mis_teclas)
		self.combinaciones.SetItem(self.combinaciones.GetFocusedItem(), 1, self.texto)
		self.combinaciones.SetFocus()
	def berifica(self, event):
		self.nueva_combinacion=""
		self.dlg_editar_combinacion.Destroy()
	def restaurarTeclas(self,event):
		if dialog_response.response(_("Está apunto de restaurar las combinaciones a sus valores por defecto, ¿desea proceder? Esta acción no se puede desacer."), _("Atención:"))==wx.ID_YES:
			remove("keys.txt")
			self.key_config.leerTeclas()
			self.key_config.mis_teclas=eval(self.key_config.mis_teclas)
			c=0
			for valor in self.key_config.mis_teclas:
				self.combinaciones.SetItem(c, 1, valor)
				c+=1
			self.combinaciones.Focus(0)
			self.combinaciones.SetFocus()
			self.handler_keyboard.unregister_all_keys()
			self.handler_keyboard.register_keys(self.key_config.mis_teclas)
