# init.py (Versão Corrigida com modo "unbuffered")

import subprocess
import threading
import sys
import os
import time

# --- Bloco de Compatibilidade de Cores para Windows ---
if sys.platform == "win32":
    os.system('')

# --- Configuração dos Scripts a Serem Executados ---
SCRIPTS = [
    {
        "name": "NIVEL 3 (Base)",
        "path": "base.py",
        "cwd": "nivel3",
        "color": "\033[94m"
    },
    {
        "name": "NIVEL 5 (Análise)",
        "path": "analise.py",
        "cwd": "nivel5",
        "color": "\033[92m"
    },
    {
        "name": "NIVEL 6 (WebApp)",
        "path": "app.py",
        "cwd": "nivel6",
        "color": "\033[93m"
    }
]

# (O restante do script, incluindo a função stream_reader, permanece o mesmo)
RESET_COLOR = "\033[0m"

def stream_reader(stream, prefix, color):
    try:
        for line in iter(stream.readline, ''):
            print(f"{color}[{prefix}]{RESET_COLOR} {line.strip()}")
            sys.stdout.flush()
    except Exception as e:
        print(f"Erro ao ler o stream de {prefix}: {e}")
    finally:
        stream.close()

def main():
    processes = []
    print("=" * 50)
    print("INICIANDO TODOS OS SCRIPTS DO PROJETO...")
    print("Pressione Ctrl+C para encerrar todos os processos.")
    print("=" * 50)

    for script_info in SCRIPTS:
        script_path = script_info["path"]
        script_name = script_info["name"]
        script_color = script_info["color"]
        script_cwd = script_info["cwd"]
        
        full_script_path = os.path.join(script_cwd, script_path)
        if not os.path.exists(full_script_path):
            print(f"{script_color}[{script_name}]{RESET_COLOR} ERRO: Script não encontrado em '{full_script_path}'. Pulando.")
            continue
            
        print(f"{script_color}[{script_name}]{RESET_COLOR} Iniciando script em '{script_cwd}'...")

        try:
            # =============================== A MUDANÇA ESTÁ AQUI ===============================
            # Adicionamos a flag "-u" para forçar o modo "unbuffered" (sem buffer de saída).
            # Isso garante que cada 'print' nos scripts filhos apareça imediatamente.
            command = [sys.executable, "-u", script_path]
            # =====================================================================================

            process = subprocess.Popen(
                command, # <--- Usando o novo comando com a flag -u
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                bufsize=1,
                cwd=script_cwd
            )
            processes.append((process, script_name, script_color))

            stdout_thread = threading.Thread(target=stream_reader, args=(process.stdout, script_name, script_color))
            stdout_thread.daemon = True
            stdout_thread.start()
            
            stderr_thread = threading.Thread(target=stream_reader, args=(process.stderr, f"{script_name} ERRO", "\033[91m"))
            stderr_thread.daemon = True
            stderr_thread.start()
            
        except Exception as e:
            print(f"{script_color}[{script_name}]{RESET_COLOR} ERRO ao iniciar o script: {e}")

    # (O restante do script para monitoramento e encerramento permanece o mesmo)
    try:
        while True:
            active_processes = []
            for p_tuple in processes:
                process, name, color = p_tuple
                if process.poll() is None:
                    active_processes.append(p_tuple)
                else:
                    print(f"{color}[{name}]{RESET_COLOR} ATENÇÃO: O processo encerrou inesperadamente com código {process.poll()}.")
            
            processes = active_processes
            if not processes:
                print("Todos os processos foram encerrados. Finalizando o launcher.")
                break
            time.sleep(5)

    except KeyboardInterrupt:
        print("\n" + "=" * 50)
        print("Recebido sinal de interrupção (Ctrl+C). Encerrando todos os scripts...")
        
        for process, name, color in processes:
            print(f"{color}[{name}]{RESET_COLOR} Enviando sinal de encerramento...")
            process.terminate()
        
        time.sleep(2)
        
        for process, name, color in processes:
            if process.poll() is None:
                print(f"{color}[{name}]{RESET_COLOR} Processo não encerrou, forçando...")
                process.kill()
                
        print("Todos os scripts foram encerrados.")
        print("=" * 50)

if __name__ == "__main__":
    main()
