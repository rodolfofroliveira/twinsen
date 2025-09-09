#!/bin/bash


# Define a timezone correta (horário do sistema)
timezone='America/Sao_Paulo'



# =============================================================================
# SCRIPT DE CONFIGURAÇÃO DE SERVIÇO SYSTEMD
# Propósito: Automatiza a criação e ativação de um serviço systemd para
#            executar o script init.py do projeto.
# =============================================================================

# --- INÍCIO DAS CONFIGURAÇÕES ---
# Ajuste estas variáveis para corresponder ao seu ambiente.

# 1. Nome do serviço systemd 
SERVICE_NAME="twinsen.service"

# 2. Usuário que executará o script. IMPORTANTE: Evite 'root'.
#    Use o seu nome de usuário regular (ex: 'pi' ou 'ubuntu').
USERNAME="ubuntu"

# 3. Caminho absoluto para o diretório raiz do seu projeto (onde está o init.py).
PROJECT_DIR="/twinsen"

# 4. Caminho para o executável Python.
#    Padrão do sistema: /usr/bin/python3
#    Se usar Virtual Environment (venv): $PROJECT_DIR/venv/bin/python3
#    Para descobrir o caminho correto (com venv ativado): which python3
PYTHON_EXEC_PATH="/usr/bin/python3"
# PYTHON_EXEC_PATH="$PROJECT_DIR/venv/bin/python3" # Exemplo com venv

# --- FIM DAS CONFIGURAÇÕES ---

# Cores para feedback
GREEN="\033[0;32m"
YELLOW="\033[1;33m"
RED="\033[0;31m"
NC="\033[0m" # No Color



# --- Validação de Root ---
if [ "$EUID" -ne 0 ]; then
  echo -e "${RED}ERRO: Este script precisa ser executado como root (use sudo).${NC}"
  echo "Exemplo: sudo ./setup_service.sh"
  exit 1
fi

#Configura o Timezone
timedatectl set-timezone $timezone


# --- Lógica de Criação do Serviço ---

echo -e "\n${GREEN}Passo 1: Parando serviço existente (se houver)...${NC}"
systemctl stop "$SERVICE_NAME" >/dev/null 2>&1 || true

echo -e "${GREEN}Passo 2: Criando arquivo de serviço em /etc/systemd/system/$SERVICE_NAME...${NC}"

# Usando 'cat << EOF' para criar o arquivo de serviço com as variáveis expandidas.
cat << EOF > "/etc/systemd/system/$SERVICE_NAME"
[Unit]
Description=Serviço de Lançamento do Projeto ($SERVICE_NAME)
Documentation=file://$PROJECT_DIR/README.md
After=network-online.target
Wants=network-online.target

[Service]
# Configurações de execução
User=$USERNAME
Group=$(id -gn "$USERNAME")
WorkingDirectory=$PROJECT_DIR
ExecStart=$PYTHON_EXEC_PATH $PROJECT_DIR/init.py

# Configurações de robustez
Restart=on-failure
RestartSec=10
KillSignal=SIGINT

[Install]
WantedBy=multi-user.target
EOF

# Verifica se o arquivo foi criado com sucesso
if [ ! -f "/etc/systemd/system/$SERVICE_NAME" ]; then
    echo -e "${RED}ERRO: Falha ao criar o arquivo de serviço. Verifique permissões e caminhos.${NC}"
    exit 1
fi

echo -e "${GREEN}Passo 3: Recarregando o daemon systemd...${NC}"
systemctl daemon-reload

echo -e "${GREEN}Passo 4: Habilitando o serviço para iniciar no boot...${NC}"
systemctl enable "$SERVICE_NAME"

echo -e "${GREEN}Passo 5: Iniciando o serviço...${NC}"
systemctl start "$SERVICE_NAME"

echo -e "\n${GREEN}--- Concluído! ---${NC}"
echo "Para verificar o status do serviço, execute:"
echo -e "${YELLOW}systemctl status $SERVICE_NAME${NC}"
echo "Para ver os logs em tempo real, execute:"
echo -e "${YELLOW}journalctl -u $SERVICE_NAME -f${NC}"
