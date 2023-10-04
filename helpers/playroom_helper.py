import uiautomation
import win32gui
import win32process
import psutil
import ctypes


EnumWindows = ctypes.windll.user32.EnumWindows
EnumWindowsProc = ctypes.WINFUNCTYPE(ctypes.c_bool, ctypes.POINTER(ctypes.c_int), ctypes.POINTER(ctypes.c_int))
GetWindowText = ctypes.windll.user32.GetWindowTextW
GetWindowTextLength = ctypes.windll.user32.GetWindowTextLengthW
IsWindowVisible = ctypes.windll.user32.IsWindowVisible

def getProcessIDByName(process_name):
    playroom_pids = []

    for proc in psutil.process_iter():
        if process_name in proc.name():
            playroom_pids.append(proc.pid)

    return playroom_pids

def get_hwnds_for_pid(pid):
    def callback(hwnd, hwnds):
        _, found_pid = win32process.GetWindowThreadProcessId(hwnd)

        if found_pid == pid:
            hwnds.append(hwnd)
        return True
    hwnds = []
    win32gui.EnumWindows(callback, hwnds)
    return hwnds 

def getWindowTitleByHandle(hwnd):
    length = GetWindowTextLength(hwnd)
    buff = ctypes.create_unicode_buffer(length + 1)
    GetWindowText(hwnd, buff, length + 1)
    return buff.value

def get_playroom_handle():
    pids = getProcessIDByName('qcgc.exe')

    for i in pids:
        hwnds = get_hwnds_for_pid(i)
        for hwnd in hwnds:
            if IsWindowVisible(hwnd):
                return hwnd

class PlayroomHelper:
    textarea_handler = None
    doc_range = None
    username = ""

    def __init__(self):
        try:
            playroom_handle = get_playroom_handle()

            if playroom_handle is None:
                raise Exception('proceso playroom no abierto')

            playroom_controls = uiautomation.ControlFromHandle(playroom_handle)
            
            self.username = getWindowTitleByHandle(playroom_handle).split('[')[1].split(']')[0]

            self.textarea_handler: uiautomation.DocumentControl = playroom_controls.DocumentControl(ClassName='RICHEDIT50W')

            self.doc_range = self.textarea_handler.GetTextPattern().DocumentRange

        except Exception as e:
            raise e

    def get_new_lines(self):
        new_range = self.textarea_handler.GetTextPattern().DocumentRange
        new_range.MoveEndpointByRange(uiautomation.TextPatternRangeEndpoint.Start, self.doc_range, uiautomation.TextPatternRangeEndpoint.End)
        new_lines = new_range.GetText(-1).split('\r\n')

        if new_lines == []:
            print("empty")
        else:
            for line in new_lines: print("line " + line)

        self.doc_range = new_range
