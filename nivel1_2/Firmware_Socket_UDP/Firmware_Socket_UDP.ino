// Em Firmware_Socket_UDP.ino

#include "Bibliotecas.h"

// --- Configuração WiFi ---
#ifndef STASSID
#define ssid "Sanctum Home2"         
#define password  "s1lverAn26"        
#endif

// --- Definição dos Buffers de Pacotes ---
byte Pacote_RX[52];
byte Pacote_TX[52];
char packetBuffer[UDP_TX_PACKET_MAX_SIZE + 1];

// --- Funções Principais ---

void setup() {
  Phy_initialize();
  Mac_initialize();
  Net_initialize();
  Transp_initialize();
  App_initialize();
}

void loop() {
  Phy_receive();

  unsigned long currentMillis = millis();
  if (currentMillis - previousMillis >= interval) {
    previousMillis = currentMillis;
    App_processamento_local();
  }
}