import wx

class ChatDialog(wx.Dialog):
    def __init__(self, parent, id=wx.ID_ANY, title="Chat Sessions", pos=wx.DefaultPosition, size=wx.DefaultSize, style=wx.DEFAULT_DIALOG_STYLE | wx.RESIZE_BORDER):
        super().__init__(parent, id=id, title=title, pos=pos, size=size, style=style)

        self.notebook = wx.Treebook(self, wx.ID_ANY, style=wx.NB_LEFT)
        
        sizer = wx.BoxSizer(wx.VERTICAL)
        sizer.Add(self.notebook, 1, wx.EXPAND | wx.ALL, 5)
        self.SetSizer(sizer)
        self.Layout()

    def add_chat_page(self, chat_panel, title):
        self.notebook.AddPage(chat_panel, title)
        page_index = self.notebook.GetPageCount() - 1
        self.notebook.SetSelection(page_index)
        return page_index

    def update_chat_page_title(self, page_index, new_title):
        self.notebook.SetPageText(page_index, new_title)

    def remove_page(self, page_index):
        self.notebook.DeletePage(page_index)

    def get_page_count(self):
        return self.notebook.GetPageCount()
