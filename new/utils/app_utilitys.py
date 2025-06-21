# -*- coding: cp1252
from __future__ import unicode_literals
import sys, os

def restart_program():
    """ Function that restarts the application if is executed."""
    args = sys.argv[:]
    if not hasattr(sys, "frozen"):
        args.insert(0, sys.executable)
    if sys.platform == 'win32':
        args = ['"%s"' % arg for arg in args]
    pidpath = os.path.join(os.getenv("temp"), "{}.pid".format('VeTube'))
    if os.path.exists(pidpath):
        os.remove(pidpath)
    os.execv(sys.executable, args)
def porcentaje_a_escala(porcentaje): return 2.00 + (1 - ((porcentaje - -10) / (10 - -10))) * (0.50 - 2.00)