import wx

# crear una clase de accesibilidad
class Accesible(wx.Accessible):
	def __init__(self, window):
		wx.Accessible.__init__(self)
		self.window = window
		self.tooltip = wx.ToolTip("Menú de opciones")
		self.tooltip.SetDelay(0)
		self.window.Bind(wx.EVT_SET_FOCUS, self.OnSetFocus)
	def GetRole(self, childId):
		return (wx.ACC_OK, wx.ROLE_SYSTEM_BUTTONMENU)
	def GetState(self, childId):
		return (wx.ACC_OK, wx.ACC_STATE_SYSTEM_FOCUSABLE | wx.ACC_STATE_SYSTEM_FOCUSED)
	def GetDefaultAction(self, childId):
		return (wx.ACC_OK, "Abrir menú")

	# el evento de foco para mostrar el tooltip
	def OnSetFocus(self, event):
		self.window.SetToolTip(self.tooltip)
		event.Skip()
