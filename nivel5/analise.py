# nivel5/analise.py - Versão com Escrita Segura preparada

import os
import time
from datetime import datetime
import yaml
import pandas as pd
from collections import deque
import io
import tempfile

# --- Configuração de Caminhos ---
CONFIG_PATH = os.path.join(os.path.dirname(__file__), '..', 'nivel4', 'configuracoes.yaml')

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


def carregar_configuracoes():
    """Lê e retorna as configurações do arquivo YAML."""
    try:
        with open(CONFIG_PATH, 'r') as f:
            return yaml.safe_load(f) or {}
    except FileNotFoundError:
        print(f"ERRO: Arquivo de configuração não encontrado em '{CONFIG_PATH}'. Verifique o caminho.")
        return None
    except yaml.YAMLError as e:
        print(f"ERRO: Formato inválido no arquivo YAML: {e}")
        return None


def read_last_lines_as_dataframe(file_path, num_lines_to_read):
    """
    Lê as últimas 'num_lines_to_read' linhas de um arquivo CSV e as carrega
    em um DataFrame do Pandas de forma eficiente.
    """
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            header = f.readline().strip()
            if num_lines_to_read <= 0:
                num_lines_to_read = 1 
            last_n_lines = deque(f, num_lines_to_read)
        
        if not last_n_lines:
            return pd.DataFrame(columns=header.split(','))

        csv_in_memory = header + "\n" + "\n".join(last_n_lines)
        return pd.read_csv(io.StringIO(csv_in_memory))
    
    except FileNotFoundError:
        raise FileNotFoundError(f"Arquivo não encontrado: {file_path}")
    except Exception as e:
        print(f"Aviso: Não foi possível processar {file_path}. Erro: {e}")
        return pd.DataFrame()


def analisar_e_registrar(config):
    """
    Função principal otimizada para ler apenas as caudas dos arquivos de dados brutos,
    com acesso seguro às configurações e tratamento de casos extremos.
    """
    print(f"[{datetime.now().strftime('%H:%M:%S')}] Executando análise...")

    # --- Leitura Segura das Configurações ---
    nivel4_config = config.get('nivel4', {})
    nivel5_config = config.get('nivel5', {})

    try:
        dir_logs_name = nivel4_config.get('diretorio_logs', 'nivel4')
        dir_dados = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', dir_logs_name))
        
        path_rede_bruto = os.path.join(dir_dados, nivel4_config.get('nome_arquivo_rede', 'dados_brutos_rede.csv'))
        path_app_bruto = os.path.join(dir_dados, nivel4_config.get('nome_arquivo_aplicacao', 'dados_brutos_aplicacao.csv'))
        path_rede_stats = os.path.join(dir_dados, nivel4_config.get('nome_arquivo_stats_rede', 'estatisticas_rede.csv'))
        path_app_stats = os.path.join(dir_dados, nivel4_config.get('nome_arquivo_stats_aplicacao', 'estatisticas_aplicacao.csv'))

        janela_rede = int(nivel5_config.get('janela_rede', 10))
        janela_app = int(nivel5_config.get('janela_aplicacao', 10))
    
    except (ValueError, TypeError) as e:
        print(f"ERRO CRÍTICO: Configuração de janela ou caminho inválida no YAML. Erro: {e}")
        return
    # --- Fim Leitura Segura ---

    # --- 1. Análise dos Dados de Rede ---
    try:
        buffer_multiplier = 3 
        linhas_a_ler_rede = janela_rede * buffer_multiplier
        df_rede = read_last_lines_as_dataframe(path_rede_bruto, linhas_a_ler_rede)

        if not df_rede.empty:
            df_rede_ok = df_rede[df_rede['Status'] == 'Sucesso'].copy()
            df_janela_rede = df_rede_ok.tail(janela_rede).copy()

            if not df_janela_rede.empty:
                df_janela_rede['RSSI_Downlink'] = pd.to_numeric(df_janela_rede['RSSI_Downlink'], errors='coerce')
                df_janela_rede.dropna(subset=['RSSI_Downlink'], inplace=True) 

                if not df_janela_rede.empty:
                    stats_rede = {
                        'Timestamp': datetime.now().strftime('%d-%m-%Y %H:%M:%S'),
                        'RSSI_Downlink_Media': df_janela_rede['RSSI_Downlink'].mean(),
                        'RSSI_Downlink_Min': df_janela_rede['RSSI_Downlink'].min(),
                        'RSSI_Downlink_Max': df_janela_rede['RSSI_Downlink'].max(),
                    }
                    file_exists = os.path.exists(path_rede_stats)
                    with open(path_rede_stats, 'a', newline='') as f:
                        writer = pd.DataFrame([stats_rede])
                        writer.to_csv(f, sep=',', header=not file_exists, index=False, float_format='%.2f')
                    print("  - Estatísticas de rede salvas.")

    except FileNotFoundError:
        print(f"  - Aviso: Arquivo de dados brutos da rede '{path_rede_bruto}' ainda não existe.")
    except Exception as e:
        print(f"  - ERRO inesperado ao analisar dados da rede: {e}")

    # --- 2. Análise dos Dados de Aplicação ---
    try:
        buffer_multiplier_app = 3
        linhas_a_ler_app = janela_app * buffer_multiplier_app
        df_app = read_last_lines_as_dataframe(path_app_bruto, linhas_a_ler_app)
        
        if not df_app.empty:
            df_janela_app = df_app.tail(janela_app).copy()

            if not df_janela_app.empty:
                df_janela_app['Luminosidade'] = pd.to_numeric(df_janela_app['Luminosidade'], errors='coerce')
                df_janela_app.dropna(subset=['Luminosidade'], inplace=True)

                if not df_janela_app.empty:
                    if (df_janela_app['Luminosidade'] == 0).all():
                        stats_app = {
                            'Timestamp': datetime.now().strftime('%d-%m-%Y %H:%M:%S'),
                            'Luminosidade_Media': 0.0,
                            'Luminosidade_Min': 0.0,
                            'Luminosidade_Max': 0.0,
                        }
                    else:
                        stats_app = {
                            'Timestamp': datetime.now().strftime('%d-%m-%Y %H:%M:%S'),
                            'Luminosidade_Media': df_janela_app['Luminosidade'].mean(),
                            'Luminosidade_Min': df_janela_app['Luminosidade'].min(),
                            'Luminosidade_Max': df_janela_app['Luminosidade'].max(),
                        }
                    
                    file_exists = os.path.exists(path_app_stats)
                    with open(path_app_stats, 'a', newline='') as f:
                        writer = pd.DataFrame([stats_app])
                        writer.to_csv(f, sep=',', header=not file_exists, index=False, float_format='%.2f')
                    print("  - Estatísticas de aplicação salvas.")

    except FileNotFoundError:
        print(f"  - Aviso: Arquivo de dados brutos da aplicação '{path_app_bruto}' ainda não existe.")
    except Exception as e:
        print(f"  - ERRO inesperado ao analisar dados da aplicação: {e}")


def main():
    """Função principal que executa o loop de análise."""
    while True:
        config = carregar_configuracoes()
        if config and config.get('nivel5', {}).get('ativado', False):
            try:
                analisar_e_registrar(config)
                intervalo = config.get('nivel5', {}).get('intervalo_analise_s', 10)
            except Exception as e:
                print(f"ERRO fatal não esperado na função analisar_e_registrar: {e}")
                intervalo = 10 
        else:
            if config is None:
                print("Análise pausada: não foi possível carregar o arquivo de configuração.", end="\r")
            else:
                print("Análise pausada via arquivo de configuração (ativado: False).", end="\r")
            intervalo = 5
        
        try:
            time.sleep(float(intervalo))
        except ValueError:
            print(f"ERRO: Intervalo de análise '{intervalo}' não é um número válido. Usando padrão 10s.")
            time.sleep(10)
        except KeyboardInterrupt:
            print("\nScript de análise encerrado pelo usuário.")
            break

if __name__ == "__main__":
    main()

