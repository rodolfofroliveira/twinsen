/**
 * @file _2_Mac.ino
 * @brief Implementação da Camada MAC.
 */

#include "Bibliotecas.h"

void Mac_initialize() // Função de inicialização da camada de Acesso ao Meio
{
  Contador_mac = 0;
}

void Mac_receive(){  // Função de recepção de pacote da Camada MAC
  // Leitura de bytes da camada MAC (se houver lógica específica)
  // byte4 = Pacote_RX[4]; // Exemplo de leitura
  Net_receive(); // chama a função de recepção da camada de Rede
}

void Mac_send() // Função de envio de pacote da Camada MAC
{
  Pacote_TX[4] = Contador_mac/256;
  Pacote_TX[5] = Contador_mac%256;
  // Pacote_TX[6] = Pacote_RX[6]; // Echo de bytes, se necessário
  // Pacote_TX[7] = Pacote_RX[7];
  
  Phy_send();  //Chama a função de envio da Camada Física
}
