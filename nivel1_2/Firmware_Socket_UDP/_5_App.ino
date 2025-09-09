/**
 * @file _5_App.ino
 * @brief Implementação da Camada de Aplicação.
 * Contém a lógica de controle autônomo com lógica invertida (mais luz = maior valor).
 * Inclui "clamping fino" para forçar a luminosidade a zero apenas no piso de ruído,
 * preservando a granularidade da faixa vermelha.
 */

#include "Bibliotecas.h"

void App_initialize() // Função de inicialização da camada de Aplicação
{
  pinMode(LED_verde, OUTPUT);
  pinMode(LED_amarelo, OUTPUT);
  pinMode(LED_vermelho, OUTPUT);
  pinMode(Buzzer, OUTPUT);
  pinMode(A0, INPUT);
}

// ===================================================================
// FUNÇÃO DE PROCESSAMENTO LOCAL AUTÔNOMA (COM CLAMPING FINO)
// Executada periodicamente pelo loop principal.
// ===================================================================
void App_processamento_local() {
  // 1. Leitura do sensor raw
  int leitura_raw = analogRead(A0);

  // 2. INVERSÃO DA LÓGICA: Converter a leitura raw (onde baixo = luz) 
  //    para um valor lógico (onde alto = luz).
  int luminosidade_logica = 1023 - leitura_raw;

  // --- INÍCIO DA MODIFICAÇÃO (Clamping Fino) ---
  // Define um "piso de ruído". Se a leitura lógica calculada for menor que este
  // valor, consideramos como zero para limpar a medição final.
  // Ajuste PISO_RUIDO conforme necessário (ex: 10, 15, 20).
  const int PISO_RUIDO = 10; 
  if (luminosidade_logica < PISO_RUIDO) {
      luminosidade_logica = 0;
  }
  // --- FIM DA MODIFICAÇÃO ---

  // Variáveis locais para calcular o novo estado dos atuadores
  byte local_led_verde, local_led_amarelo, local_led_vermelho, local_buzzer;

  // 3. Lógica de decisão com base nos limiares e no valor de luminosidade ajustado
  if (luminosidade_logica > limiar_amarelo) { // Muita luz
    local_led_verde = 1;
    local_led_amarelo = 0;
    local_led_vermelho = 0;
    local_buzzer = 0;
  } else if (luminosidade_logica > limiar_vermelho) { // Luz média
    local_led_verde = 0;
    local_led_amarelo = 1;
    local_led_vermelho = 0;
    local_buzzer = 0;
  } else { // Pouca luz / crítico
    local_led_verde = 0;
    local_led_amarelo = 0;
    local_led_vermelho = 1;
    local_buzzer = 1;
  }
  
  // --- Seção Crítica ---
  // Atualiza as variáveis globais e os pinos de forma atômica.
  noInterrupts();
  luminosidade = luminosidade_logica; // Salva o valor (agora 0 se estiver abaixo do PISO_RUIDO)
  LED_verde_status_global = local_led_verde;
  LED_amarelo_status_global = local_led_amarelo;
  LED_vermelho_status_global = local_led_vermelho;
  Buzzer_status_global = local_buzzer;
  
  digitalWrite(LED_verde, LED_verde_status_global);
  digitalWrite(LED_amarelo, LED_amarelo_status_global);
  digitalWrite(LED_vermelho, LED_vermelho_status_global);
  digitalWrite(Buzzer, Buzzer_status_global);
  interrupts();
  // --- Fim da Seção Crítica ---
}


// ===================================================================
// FUNÇÃO DE RECEPÇÃO (Atualiza Limiares)
// Executada quando um pacote da base é recebido.
// ===================================================================
void App_receive()
{
  // 1. Extrai os limiares lógicos do pacote recebido (bytes 16-19)
  int recebido_limiar_amarelo = (Pacote_RX[16] * 256) + Pacote_RX[17];
  int recebido_limiar_vermelho = (Pacote_RX[18] * 256) + Pacote_RX[19];

  // --- Seção Crítica ---
  noInterrupts();
  if (recebido_limiar_amarelo > 0) {
    limiar_amarelo = recebido_limiar_amarelo;
  }
  if (recebido_limiar_vermelho > 0) {
    limiar_vermelho = recebido_limiar_vermelho;
  }
  interrupts();
  // --- Fim da Seção Crítica ---

  // 2. Chama a função de envio para responder à base
  App_send();
}


// ===================================================================
// FUNÇÃO DE ENVIO (Reporta Estado Atual)
// ===================================================================
void App_send()
{
  // --- Seção Crítica ---
  noInterrupts();
  int current_luminosidade_logica = luminosidade;
  byte current_led_verde = LED_verde_status_global;
  byte current_led_amarelo = LED_amarelo_status_global;
  byte current_led_vermelho = LED_vermelho_status_global;
  byte current_buzzer = Buzzer_status_global;
  interrupts();
  // --- Fim da Seção Crítica ---

  // Popula o pacote de transmissão com os valores lidos de forma segura
  Pacote_TX [17] = (byte) (current_luminosidade_logica / 256);
  Pacote_TX [18] = (byte) (current_luminosidade_logica % 256);

  Pacote_TX [34] = current_led_verde;
  Pacote_TX [37] = current_led_amarelo;
  Pacote_TX [40] = current_led_vermelho;
  Pacote_TX [43] = current_buzzer;

  Transp_send();
}
