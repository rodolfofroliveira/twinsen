// Em Bibliotecas.h

#ifndef _BIBLIOTECAS_H
#define _BIBLIOTECAS_H

#include <Arduino.h>
#include <ESP8266WiFi.h>
#include <WiFiUdp.h>

// --- Instância UDP ---
WiFiUDP Udp;

// --- Definições de Pinos ---
#define LED_verde D4
#define LED_amarelo D7
#define LED_vermelho D3
#define Buzzer D5


// Estado da Camada Física
float RSSI_dBm_dl = 0.0;
float RSSI_dBm_ul = 0.0;
int RSSI_dl = 0;
int LQI_dl = 0;
int RSSI_ul = 0;
int LQI_ul = 0;

// Estado da Camada de Rede (se necessário, verifique se My_address já foi movido)
byte Orig_address = 0;
byte Dest_address = 0;


// --- Constantes Globais ---
const long interval = 500;

// --- Variáveis Globais de Configuração e Estado (Definição Direta) ---
unsigned int localPort = 8888;
String newHostname = "SENSOR001";
unsigned long tempo_ip = 0;
unsigned long previousMillis = 0;

bool TX_ledblink = false;
bool RX_ledblink = false;

int Contador_mac = 0;
byte My_address = 1;
int pkt_counter_up = 0;

// Estado da Aplicação
int luminosidade = 0;
byte LED_verde_status_global = 0;
byte LED_amarelo_status_global = 0;
byte LED_vermelho_status_global = 0;
byte Buzzer_status_global = 0;

// Limiares (com valores padrão)
int limiar_amarelo = 500; // Valor padrão para fronteira Verde/Amarelo
int limiar_vermelho = 200; // Valor padrão para fronteira Amarelo/Vermelho

// Buffers de Pacotes (mantidos como extern para definição no .ino principal)
extern byte Pacote_RX[52];
extern byte Pacote_TX[52];
extern char packetBuffer[];

// --- Protótipos de Funções Globais ---
// (Certifique-se que todos os protótipos da resposta anterior estão aqui)
void Phy_initialize();
void Phy_receive();
void Phy_send();
void Phy_dBm_to_Radiuino();
void Phy_shadowing();
void box_muller(double sigma, double *r1, double *r2);
void Mac_initialize();
void Mac_receive();
void Mac_send();
void Net_initialize();
void Net_receive();
void Net_send();
void Transp_initialize();
void Transp_receive();
void Transp_send();
void App_initialize();
void App_processamento_local();
void App_receive();
void App_send();

#endif // _BIBLIOTECAS_H