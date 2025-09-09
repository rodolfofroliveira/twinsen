# nivel6/app.py

import os
import yaml
import csv
import io # Usado para processar texto em memória
from flask import Flask, render_template, request, jsonify
from markupsafe import Markup
from collections import deque # Usado para ler as últimas linhas de um arquivo de forma eficiente
from datetime import datetime # Usado para processar timestamps

app = Flask(__name__)

# --- CONFIGURAÇÃO DE CAMINHOS ---
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
NIVEL4_PATH = os.path.join(BASE_DIR, '..', 'nivel4')

YAML_PATH = os.path.join(NIVEL4_PATH, 'configuracoes.yaml')
CSV_RAW_PATH = os.path.join(NIVEL4_PATH, 'dados_brutos_aplicacao.csv')
CSV_STATS_PATH = os.path.join(NIVEL4_PATH, 'estatisticas_aplicacao.csv')


# --- ROTA PRINCIPAL ---
@app.route('/')
def home():
    try:
        with open(YAML_PATH, 'r') as f:
            config_data = yaml.safe_load(f)
        initial_data = config_data.get('nivel6', {})
    except FileNotFoundError:
        return "Erro: O arquivo 'configuracoes.yaml' não foi encontrado!", 404
        
    try:
        svg_path = os.path.join(BASE_DIR, 'static', 'pk2.svg')
        with open(svg_path, 'r') as f:
            svg_content = f.read()
    except FileNotFoundError:
        svg_content = "<p>Erro: Arquivo 'pk2.svg' não encontrado.</p>"

    return render_template('index.html', 
                           svg_data=Markup(svg_content), 
                           initial_data=initial_data)


# --- API PARA DADOS DE LUMINOSIDADE (GRÁFICO) ---
@app.route('/api/luminosidade')
def get_luminosidade_data():
    try:
        with open(CSV_RAW_PATH, 'r', encoding='utf-8') as f:
            last_lines = deque(f, 30) 
        
        labels = []
        values = []
        latest_value = "N/A"

        for row in csv.reader(last_lines):
            if len(row) >= 2 and "Timestamp" not in row[0]:
                try:
                    dt_object = datetime.strptime(row[0], '%Y-%m-%d %H:%M:%S.%f')
                    labels.append(dt_object.strftime('%H:%M:%S'))
                    values.append(float(row[1]))
                except (ValueError, IndexError):
                    continue

        if values:
            latest_value = values[-1]
        
        return jsonify({'labels': labels, 'values': values, 'latest_value': latest_value})

    except FileNotFoundError:
        return jsonify(labels=[], values=[], latest_value="N/A", error="Arquivo não encontrado"), 200
    except Exception as e:
        return jsonify(labels=[], values=[], latest_value="N/A", error=str(e)), 200


# --- API PARA ATUALIZAR LIMIARES ---
@app.route('/update_thresholds', methods=['POST'])
def update_thresholds():
    data = request.get_json()
    if not data or 'limiar_atencao' not in data or 'limiar_critico' not in data:
        return jsonify(success=False, error="Dados inválidos"), 400
    
    try:
        with open(YAML_PATH, 'r') as f:
            config_data = yaml.safe_load(f)

        config_data['nivel6']['limiar_atencao'] = int(data['limiar_atencao'])
        config_data['nivel6']['limiar_critico'] = int(data['limiar_critico'])

        with open(YAML_PATH, 'w') as f:
            yaml.dump(config_data, f, default_flow_style=False, sort_keys=False)
            
        return jsonify(success=True, message="Limiares atualizados com sucesso!")
        
    except (ValueError, TypeError):
        return jsonify(success=False, error="Valores dos limiares devem ser números inteiros."), 400
    except Exception as e:
        return jsonify(success=False, error=str(e)), 500


# --- API PARA DADOS ESTATÍSTICOS (COM CORREÇÃO) ---
@app.route('/api/estatisticas')
def get_estatisticas_data():
    """Lê o YAML e a última linha do CSV, formatando os dados para exibição correta."""
    response_data = {}
    try:
        with open(YAML_PATH, 'r') as f:
            config = yaml.safe_load(f)
        response_data.update(config.get('nivel6', {}))
        response_data.update(config.get('nivel5', {}))
    except Exception as e:
        response_data['error_yaml'] = str(e)

    try:
        with open(CSV_STATS_PATH, 'r', encoding='utf-8') as f:
            header_str = f.readline()
            try:
                last_line_str = deque(f, 1)[0]
            except IndexError:
                return jsonify(response_data)

        header = next(csv.reader(io.StringIO(header_str)))
        last_line_data = next(csv.reader(io.StringIO(last_line_str)))
        latest_stats_raw = dict(zip(header, last_line_data))

        # --- INÍCIO DA MODIFICAÇÃO: Formatação de Saída ---
        # Converte valores numéricos para strings formatadas para evitar o problema do "zero falsy" no JavaScript.
        latest_stats_converted = {}
        for key, value in latest_stats_raw.items():
            try:
                numeric_value = float(value)
                
                # Formata os valores de estatística como texto
                if key == 'Luminosidade_Media':
                    latest_stats_converted[key] = f"{numeric_value:.2f}"
                elif key in ['Luminosidade_Min', 'Luminosidade_Max']:
                    latest_stats_converted[key] = f"{int(numeric_value)}"
                else:
                    # Mantém outros valores numéricos como estão (se houver)
                    latest_stats_converted[key] = numeric_value
                    
            except (ValueError, TypeError):
                # Mantém valores não numéricos (ex: Timestamp) como estão
                latest_stats_converted[key] = value
        
        response_data.update(latest_stats_converted)
        # --- FIM DA MODIFICAÇÃO ---
        
        return jsonify(response_data)

    except FileNotFoundError:
        response_data['error_csv'] = "Arquivo de estatísticas não encontrado."
        return jsonify(response_data), 200
    except Exception as e:
        response_data['error_csv'] = str(e)
        return jsonify(response_data), 500


if __name__ == '__main__':
    # Para um ambiente de produção, considere usar um servidor WSGI como waitress ou gunicorn
    app.run(host='0.0.0.0', port=5000, debug=False)

