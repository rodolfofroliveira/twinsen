#!/bin/bash

# =============================================================================
# SCRIPT DE CONFIGURAÇÃO DE SERVIÇO SYSTEMD TWINsen
# Propósito: Automatiza a criação e ativação de um serviço systemd para
#            executar o script init.py do Projeto TWINsen.
# =============================================================================

# --- INÍCIO DAS CONFIGURAÇÕES ---
# Ajuste estas variáveis para corresponder ao seu ambiente.

# 1. Nome do serviço systemd 
SERVICE_NAME="twinsen.service"

# 2. Usuário que executará o script. IMPORTANTE: Evite 'root'.
#    Use o seu nome de usuário regular (ex: 'pi' ou 'ubuntu').
USERNAME="twinsen"

# 3. Caminho absoluto para o diretório raiz do seu projeto (onde estão os arquivos do sistema).
PROJECT_DIR="/twinsen"

# 4. Caminho para o executável Python.
#    Padrão do sistema: /usr/bin/python3
#    Se usar Virtual Environment (venv): $PROJECT_DIR/venv/bin/python3
#    Para descobrir o caminho correto (com venv ativado): which python3
PYTHON_EXEC_PATH="/usr/bin/python3"
# PYTHON_EXEC_PATH="$PROJECT_DIR/venv/bin/python3" # Exemplo com venv

# Define a timezone correta (horário do sistema)
timezone='America/Sao_Paulo'


# Cores para feedback
GREEN="\033[0;32m"
YELLOW="\033[1;33m"
RED="\033[0;31m"
NC="\033[0m" # Sem cores

# --- FIM DAS CONFIGURAÇÕES ---


# --- Validação de Root ---
if [ "$EUID" -ne 0 ]; then
  echo -e "${RED}ERRO: Este script precisa ser executado como root (use sudo).${NC}"
  echo "Exemplo: sudo ./setup_service.sh"
  exit 1
fi

# --- 0. Validação de Usuário ---
echo -e "\n${GREEN}Verificando se o usuário '$USERNAME' existe...${NC}"
if ! id "$USERNAME" &>/dev/null; then
    echo -e "${RED}ERRO: O usuário '$USERNAME' não existe no sistema. Crie o usuário antes de continuar ou utilize outro usuário.${NC}"
    echo -e "${YELLOW}Exemplo para criar o usuário: sudo useradd -m $USERNAME${NC}"
    exit 1
fi

# --- 1. Configura o Timezone
echo -e "\n${GREEN}--- Configurando o timezone $timezone---${NC}"
timedatectl set-timezone $timezone


# --- 2. Instalação de Dependências Python ---
echo -e "\n${GREEN}Iniciando a instalação de dependências do sistema...${NC}"

# Passo 2.1: Atualizar a lista de pacotes
echo -e "\n${GREEN}Atualizando a lista de pacotes do sistema (apt update)...${NC}"
apt update

# Validação do apt update
if [ $? -ne 0 ]; then
    echo -e "${RED}ERRO: Falha ao atualizar a lista de pacotes (apt update).${NC}"
    echo -e "${YELLOW}Verifique sua conexão com a internet e as configurações do repositório.${NC}"
    exit 1
fi

# Passo 2.2: Instalar as bibliotecas Python
echo -e "\n${GREEN}Instalando as bibliotecas python3-yaml, python3-pandas e python3-flask...${NC}"
apt install -y python3-yaml python3-pandas python3-flask

# Validação do apt install
if [ $? -ne 0 ]; then
    echo -e "${RED}ERRO: Falha ao instalar uma ou mais bibliotecas Python via apt.${NC}"
    echo -e "${YELLOW}Verifique as mensagens de erro acima para identificar o pacote problemático.${NC}"
    exit 1
fi

echo -e "\n${GREEN}Dependências instaladas com sucesso!${NC}"



# --- 3. Cria o diretório da aplicação ---
echo -e "\n${GREEN}Criando diretório $PROJECT_DIR...${NC}"
mkdir -p $PROJECT_DIR

# Validação do comando mkdir
if [ $? -ne 0 ]; then
    echo -e "${RED}ERRO: Não foi possível criar o diretório $PROJECT_DIR. Verifique as permissões.${NC}"
    exit 1
fi

# --- 4. Copia o conteúdo da aplicação ---
echo -e "\n${GREEN}Copiando os arquivos para $PROJECT_DIR...${NC}"
cp -a . $PROJECT_DIR

# Validação da cópia
if [ $? -ne 0 ]; then
    echo -e "${RED}ERRO: Falha ao copiar os arquivos para $PROJECT_DIR .${NC}"
    exit 1
fi

# --- 5. Altera o dono e grupo do diretório do sistema ---
echo -e "\n${GREEN}Alterando as permissões de $PROJECT_DIR...${NC}"
chown -R $USERNAME:$USERNAME $PROJECT_DIR

# Validação do comando chown
if [ $? -ne 0 ]; then
    echo -e "${RED}ERRO: Não foi possível alterar o dono e o grupo do diretório $PROJECT_DIR. O usuário $USERNAME existe?${NC}"
    exit 1
fi



# --- 6. Criação do serviço ---

echo -e "\n${GREEN}Começando a instalação do serviço${NC}"

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

echo -e "\n${GREEN}--- Instalação do serviço concluído com sucesso!! ---${NC}"
echo "Para verificar o status do serviço, execute:"
echo -e "${YELLOW}systemctl status $SERVICE_NAME${NC}"
echo "Para ver os logs em tempo real, execute:"
echo -e "${YELLOW}journalctl -u $SERVICE_NAME -f${NC}"



