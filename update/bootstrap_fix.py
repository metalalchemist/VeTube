import sys
import shutil
import os
import subprocess
import time
import ctypes
import traceback

# Archivo de log en la carpeta temporal del usuario (ej. C:\Users\TuUsuario\AppData\Local\Temp\vetube_bootstrap_debug.txt)
LOG_FILE = os.path.join(os.environ.get('TEMP', os.path.expanduser('~')), 'vetube_bootstrap_debug.txt')

def log(msg):
    """Escribe un mensaje en el archivo de log."""
    try:
        with open(LOG_FILE, 'a', encoding='utf-8') as f:
            f.write(f"[{time.strftime('%H:%M:%S')}] {msg}\n")
    except Exception:
        pass

def kill_process(pid):
    """Mata el proceso con el PID dado usando la API de Windows."""
    log(f"Intentando matar proceso PID: {pid}")
    try:
        PROCESS_TERMINATE = 1
        handle = ctypes.windll.kernel32.OpenProcess(PROCESS_TERMINATE, False, pid)
        if handle:
            ctypes.windll.kernel32.TerminateProcess(handle, -1)
            ctypes.windll.kernel32.CloseHandle(handle)
            log("Proceso terminado exitosamente.")
        else:
            log("No se pudo obtener handle del proceso (¿ya estaba cerrado?).")
    except Exception as e:
        log(f"Error matando proceso: {e}")

def main():
    log("=== INICIO BOOTSTRAP ===")
    log(f"Argumentos recibidos: {sys.argv}")

    if len(sys.argv) < 5:
        log("ERROR: No hay suficientes argumentos.")
        sys.exit(1)

    try:
        pid = int(sys.argv[1])
        source = sys.argv[2]
        dest = sys.argv[3]
        exe_path = sys.argv[4]

        log(f"Config inicial -> Source: {source} | Dest: {dest} | Exe: {exe_path}")

        # --- CORRECCIÓN DE RUTA ---
        if os.path.basename(os.path.normpath(dest)) == "_internal":
            log("Detectado destino '_internal'. Corrigiendo a directorio padre.")
            dest = os.path.dirname(os.path.normpath(dest))
            log(f"Nuevo Destino: {dest}")
        # --------------------------

        # 1. Matar proceso
        time.sleep(1) 
        kill_process(pid)
        time.sleep(2)

        # 2. Mover archivos
        if os.path.exists(source) and os.path.exists(dest):
            log("Iniciando copia de archivos...")
            try:
                shutil.copytree(source, dest, dirs_exist_ok=True)
                log("Copia finalizada correctamente.")
            except Exception as e:
                log(f"ERROR copiando archivos: {e}")
                log(traceback.format_exc())
        else:
            log("ERROR: La carpeta source o dest no existen.")

        # 3. Ejecutar la nueva versión
        log("Intentando relanzar aplicación...")
        
        # Normalizar ruta del ejecutable
        exe_path = os.path.normpath(exe_path)
        log(f"Ruta exe original: {exe_path}")

        # Verificación inteligente de la ruta del ejecutable
        final_exe_path = exe_path
        if not os.path.exists(final_exe_path):
            log("El exe no existe en la ruta original. Buscando alternativas...")
            # 1. Buscar en la carpeta destino raíz
            candidate = os.path.join(dest, os.path.basename(exe_path))
            if os.path.exists(candidate):
                final_exe_path = candidate
                log(f"Encontrado en raíz destino: {final_exe_path}")
            else:
                # 2. Buscar quitando _internal si estaba
                clean_path = exe_path.replace("_internal\\", "").replace("_internal/", "")
                if os.path.exists(clean_path):
                    final_exe_path = clean_path
                    log(f"Encontrado limpiando ruta: {final_exe_path}")

        if os.path.exists(final_exe_path):
            working_dir = os.path.dirname(os.path.abspath(final_exe_path))
            log(f"Lanzando: {final_exe_path}")
            log(f"Directorio de trabajo (CWD): {working_dir}")
            
            os.chdir(working_dir)
            
            try:
                # Intento 1: DETACHED_PROCESS
                # Corregido: Quitamos CREATE_NEW_CONSOLE porque entraba en conflicto con DETACHED_PROCESS (Error 87)
                subprocess.Popen([final_exe_path], 
                                 creationflags=subprocess.DETACHED_PROCESS,
                                 cwd=working_dir,
                                 close_fds=False,
                                 shell=False)
                log("subprocess.Popen llamado con éxito (DETACHED).")
            except Exception as e:
                log(f"Fallo intento 1: {e}")
                # Intento 2: Shell básico
                log("Intentando fallback con shell=True...")
                # Usamos una f-string limpia para las comillas
                subprocess.Popen(f'"{final_exe_path}"', shell=True, cwd=working_dir)
        else:
            log(f"ERROR CRÍTICO: No se encontró el ejecutable en ninguna ruta probada. Última intentada: {final_exe_path}")

    except Exception as e:
        log(f"ERROR GLOBAL NO CONTROLADO: {e}")
        log(traceback.format_exc())
    
    log("=== FIN BOOTSTRAP ===")

if __name__ == "__main__":
    main()