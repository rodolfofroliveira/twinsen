# base.py - Versão com Escrita Segura no YAML

import socket
import time
import os
import yaml
import csv
import tempfile
from datetime import datetime

# --- Funções Auxiliares---

def carregar_configuracoes(caminho_config):
    """Lê o arquivo de configuração YAML e retorna um dicionário."""
    try:
        with open(caminho_config, "r") as f:
            return yaml.safe_load(f)
    except FileNotFoundError:
        print(f"Erro: Arquivo de configuração não encontrado em '{caminho_config}'")
        return None
    except yaml.YAMLError as e:
        print(f"Erro ao ler o arquivo YAML: {e}")
        return None


def registrar_log_rede(caminho_log, timestamp, rssi, status):
    """Registra dados de rede (RSSI, status) em um arquivo CSV."""
    file_exists = os.path.isfile(caminho_log)
    try:
        with open(caminho_log, mode='a', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)
            if not file_exists:
                writer.writerow(["Timestamp", "RSSI_Downlink", "Status"]) # Cabeçalho
            writer.writerow([timestamp, rssi, status])
    except IOError as e:
        print(f"Erro de I/O ao escrever no log de rede: {e}")


def registrar_log_aplicacao(caminho_log, timestamp, luminosidade):
    """Registra dados de aplicação (luminosidade) em um arquivo CSV."""
    file_exists = os.path.isfile(caminho_log)
    try:
        with open(caminho_log, mode='a', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)
            if not file_exists:
                writer.writerow(["Timestamp", "Luminosidade"]) # Cabeçalho
            writer.writerow([timestamp, luminosidade])
    except IOError as e:
        print(f"Erro de I/O ao escrever no log de aplicação: {e}")


def salvar_yaml_seguro(caminho, dados):
    """Escreve o YAML de forma atômica para evitar corrupção."""
    dir_name = os.path.dirname(caminho)
    try:
        with tempfile.NamedTemporaryFile('w', dir=dir_name, delete=False, encoding="utf-8") as tmp:
            yaml.dump(dados, tmp, default_flow_style=False, sort_keys=False)
            temp_name = tmp.name
        os.replace(temp_name, caminho)
    except Exception as e:
        print(f"Erro ao salvar o YAML de forma segura: {e}")


def atualizar_status_yaml(caminho_yaml, novos_estados):
    """Lê o arquivo YAML, atualiza os estados no 'nivel6' e o reescreve de forma segura."""
    try:
        with open(caminho_yaml, 'r') as f:
            config_data = yaml.safe_load(f) or {}

        if 'nivel6' not in config_data:
            config_data['nivel6'] = {}

        config_data['nivel6']['led_verde'] = novos_estados.get('led_verde', config_data['nivel6'].get('led_verde'))
        config_data['nivel6']['led_amarelo'] = novos_estados.get('led_amarelo', config_data['nivel6'].get('led_amarelo'))
        config_data['nivel6']['led_vermelho'] = novos_estados.get('led_vermelho', config_data['nivel6'].get('led_vermelho'))
        config_data['nivel6']['buzzer'] = novos_estados.get('buzzer', config_data['nivel6'].get('buzzer'))

        if 'luminosidade' in novos_estados:
            config_data['nivel6']['luminosidade_atual'] = novos_estados['luminosidade']

        config_data['nivel6']['ultima_atualizacao'] = datetime.now().strftime('%Y-%m-%d %H:%M:%S')

        salvar_yaml_seguro(caminho_yaml, config_data)

    except Exception as e:
        print(f"Erro ao atualizar o arquivo YAML: {e}")

# =============================================================================

# --- Configuração de Caminhos ---
dir_atual = os.path.dirname(__file__) if '__file__' in locals() else os.getcwd()
caminho_nivel4 = os.path.abspath(os.path.join(dir_atual, '..', 'nivel4')) 

caminho_config_yaml = os.path.join(caminho_nivel4, 'configuracoes.yaml')
caminho_log_rede_csv = os.path.join(caminho_nivel4, 'dados_brutos_rede.csv')
caminho_log_aplicacao_csv = os.path.join(caminho_nivel4, 'dados_brutos_aplicacao.csv')

# --- Script Principal ---

def main():
    """Função principal que executa o loop de comunicação com reconfiguração dinâmica."""
    
    config_inicial = carregar_configuracoes(caminho_config_yaml)
    if not config_inicial:
        print(f"Verifique o caminho para configuracoes.yaml: {caminho_config_yaml}")
        return

    # --- Configuração Inicial do Socket ---
    current_ip = config_inicial['nivel1']['ip']
    current_port = config_inicial['nivel1']['porta']
    HOST_LOCAL = ''
    
    udp_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    udp_socket.settimeout(2.0)
    try:
        udp_socket.bind((HOST_LOCAL, current_port))
    except OSError as e:
        print(f"Erro ao fazer bind na porta {current_port}: {e}.")
        return

    print(f"Servidor UDP escutando na porta {current_port}")
    print(f"Monitorando e configurando o Nó Sensor em {current_ip}")
    print("Pressione Ctrl+C para encerrar.")

    pkt_down_counter = 0

    try:
        while True:
            config = carregar_configuracoes(caminho_config_yaml)
            if not config:
                print("Falha ao recarregar configurações. Aguardando...")
                time.sleep(5)
                continue

            if not config.get('nivel3', {}).get('ligado', False):
                print("Coleta de dados pausada via arquivo de configuração (ligado: False).   ", end="\r")
                time.sleep(5)
                continue
            
            print("                                                                          ", end="\r")
            intervalo = config['nivel3']['intervalo_medicoes']

            # --- Início da Modificação: Reconfiguração Dinâmica de Rede ---
            new_ip = config['nivel1']['ip']
            new_port = config['nivel1']['porta']

            if new_port != current_port:
                print(f"\n[INFO] Detectada mudança de porta. Reiniciando socket de {current_port} para {new_port}...")
                try:
                    udp_socket.close()
                    udp_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
                    udp_socket.settimeout(2.0)
                    udp_socket.bind((HOST_LOCAL, new_port))
                    current_port = new_port
                    print(f"[INFO] Socket reconfigurado com sucesso para porta {current_port}.")
                except OSError as e:
                    print(f"[ERRO] Falha ao reconfigurar para porta {new_port}: {e}. Tentando novamente no próximo ciclo.")
                    time.sleep(intervalo)
                    continue

            current_ip = new_ip
            ENDERECO_SENSOR = (current_ip, current_port)
            # --- Fim da Modificação ---

            # --- Preparação do Pacote de Saída ---
            PacoteTX = [0] * 52
            pkt_down_counter = (pkt_down_counter + 1) % 256
            PacoteTX[12] = pkt_down_counter
            PacoteTX[8] = 1 
            PacoteTX[10] = 0 

            try:
                limiar_para_envio_1 = int(config['nivel6']['limiar_atencao'])
                limiar_para_envio_2 = int(config['nivel6']['limiar_critico'])
            except (KeyError, TypeError, ValueError):
                limiar_para_envio_1 = 0
                limiar_para_envio_2 = 0

            PacoteTX[16] = limiar_para_envio_1 // 256
            PacoteTX[17] = limiar_para_envio_1 % 256
            PacoteTX[18] = limiar_para_envio_2 // 256
            PacoteTX[19] = limiar_para_envio_2 % 256
            # --- Fim do Empacotamento ---

            # --- Envio e Recepção ---
            udp_socket.sendto(bytes(PacoteTX), ENDERECO_SENSOR)

            try:
                Pacote_RX, cliente = udp_socket.recvfrom(1024)
                if len(Pacote_RX) == 52:
                    timestamp_recebido = datetime.now().strftime('%Y-%m-%d %H:%M:%S.%f')[:-3]
                    
                    byte2 = Pacote_RX[2]
                    rssi_dl = ((byte2 - 256) / 2.0) - 74 if byte2 > 128 else (byte2 / 2.0) - 74
                    luminosidade_calculada = Pacote_RX[17] * 256 + Pacote_RX[18]
                    
                    led_verde_status = bool(Pacote_RX[34])
                    led_amarelo_status = bool(Pacote_RX[37])
                    led_vermelho_status = bool(Pacote_RX[40])
                    buzzer_status = bool(Pacote_RX[43])

                    print(f"[{timestamp_recebido}] Sincronizado! RSSI: {rssi_dl:.2f} dBm, Luminosidade: {luminosidade_calculada}, Status LED Vd:{led_verde_status}, Am:{led_amarelo_status}, Vm:{led_vermelho_status}")
                    
                    registrar_log_rede(caminho_log_rede_csv, timestamp_recebido, f"{rssi_dl:.2f}", "Sucesso")
                    registrar_log_aplicacao(caminho_log_aplicacao_csv, timestamp_recebido, luminosidade_calculada)

                    novos_estados = {
                        'led_verde': led_verde_status, 
                        'led_amarelo': led_amarelo_status,
                        'led_vermelho': led_vermelho_status, 
                        'buzzer': buzzer_status,
                        'luminosidade': luminosidade_calculada
                    }
                    atualizar_status_yaml(caminho_config_yaml, novos_estados)

                else:
                    timestamp_falha = datetime.now().strftime('%Y-%m-%d %H:%M:%S.%f')[:-3]
                    print(f"[{timestamp_falha}] Erro: Pacote recebido com tamanho inesperado ({len(Pacote_RX)} bytes).")
                    registrar_log_rede(caminho_log_rede_csv, timestamp_falha, "N/A", "Falha (Tamanho Incorreto)")
            
            except socket.timeout:
                timestamp_falha = datetime.now().strftime('%Y-%m-%d %H:%M:%S.%f')[:-3]
                print(f"[{timestamp_falha}] Timeout: Nenhuma resposta recebida do sensor.")
                registrar_log_rede(caminho_log_rede_csv, timestamp_falha, "N/A", "Falha (Timeout)")
            
            time.sleep(float(intervalo))

    except KeyboardInterrupt:
        print("\nExecução interrompida pelo usuário.")
    except Exception as e:
        print(f"Erro inesperado no loop principal: {e}")
    finally:
        udp_socket.close()
        print("Socket fechado. Fim da execução.")

if __name__ == "__main__":
    main()

