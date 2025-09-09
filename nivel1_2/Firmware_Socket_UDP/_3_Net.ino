/**
 * @file _3_Net.ino
 * @brief Implementação da Camada de Rede (Roteamento simples).
 */

#include "Bibliotecas.h"

void Net_initialize() // Função de inicialização da camada de Rede
{
  My_address = 1; // Define o endereço do sensor
}

void Net_receive()  // Função de recepção de pacote da Camada de Rede
{
  byte dest_addr = Pacote_RX[8];
  Dest_address = dest_addr; // Armazena o endereço de destino (para uso em Net_send)
  Orig_address = Pacote_RX[10]; // Armazena o endereço de origem

  if (dest_addr == My_address) // Verifica se o pacote é para este dispositivo
     {
      Contador_mac = Contador_mac + 10; // Incremento de exemplo
      Transp_receive(); //Chama a função de recepção da camada de Transporte
     }
}

void Net_send()// Função de envio de pacote da Camada de Rede
{
  Pacote_TX[8] = Orig_address; // Endereço de destino da resposta é a origem do pacote recebido
  Pacote_TX[10] = My_address; // Meu endereço como origem da resposta
  
  Mac_send();  //Chama a função de envio da Camada de Acesso ao Meio
}
