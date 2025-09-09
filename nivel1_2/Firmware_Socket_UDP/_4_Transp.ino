/**
 * @file _4_Transp.ino
 * @brief Implementação da Camada de Transporte (Controle de sequência).
 */

#include "Bibliotecas.h"

void Transp_initialize()  // Função de inicialização da camada de Transporte
{
  pkt_counter_up = 0; //Inicializa o contador de pacotes 
}

void Transp_receive()   // Função de recepção de pacote da Camada de Transporte
{
  // Leitura dos dados de transporte recebidos (ex: contador de downlink)
  // byte12 = Pacote_RX[12];
  
  App_receive();//Chama a função de recepção da camada de Aplicação
}

void Transp_send()// Função de envio de pacote da Camada de Transporte
{ 
  pkt_counter_up = pkt_counter_up + 1;
  byte byte14 = pkt_counter_up / 256;  // MSB do contador de pacotes de uplink
  byte byte15 = pkt_counter_up % 256;  // LSB do contador de pacotes de uplink
  
  // Pacote_TX[12] e Pacote_TX[13] poderiam ser um echo do contador de downlink (Pacote_RX[12/13])
  Pacote_TX[14] = byte14;
  Pacote_TX[15] = byte15;
  
  Net_send();  //Chama a função de envio da Camada de Rede
}
