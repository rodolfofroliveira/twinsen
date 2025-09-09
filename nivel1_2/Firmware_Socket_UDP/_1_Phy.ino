/**
 * @file _1_Phy.ino
 * @brief Implementação da Camada Física (WiFi, UDP, Simulação de RSSI).
 */

#include "Bibliotecas.h"

void Phy_initialize()  // Funcao de inicializacao da camada Física
{
  Serial.begin(115200);
  randomSeed(analogRead(0));
  WiFi.mode(WIFI_STA);
  WiFi.hostname(newHostname.c_str());
  WiFi.begin(ssid, password);
  while (WiFi.status() != WL_CONNECTED) {
    Serial.print('.');
    delay(500);
  }
  Serial.println("\n-------------------------------------------------------");
  Serial.print("PK2 Conectada! Endereco IP: ");
  Serial.println(WiFi.localIP());
  Serial.printf("UDP server on port %d\n", localPort);
  Udp.begin(localPort);
  Serial.printf("Default hostname: %s\n", WiFi.hostname().c_str());

  RX_ledblink = false;
  TX_ledblink = false;
}

void Phy_receive()  // Funcao de recepcao de pacote da Camada Física
{
  if (millis() - tempo_ip >= 5000) {
    Serial.println("-------------------------------------------------------");
    Serial.print("PK2 Conectada! Endereco IP: ");
    Serial.println(WiFi.localIP());
    tempo_ip = millis();
  }

  int packetSize = Udp.parsePacket();
  if (packetSize >= 52) {
    int n = Udp.read(packetBuffer, UDP_TX_PACKET_MAX_SIZE);
    packetBuffer[n] = 0;
    if (RX_ledblink) {
      digitalWrite(LED_vermelho, HIGH);
    }

    for (byte i = 0; i < 52; i++)
    {
      Pacote_RX[i] = packetBuffer[i];
      Pacote_TX[i] = 0;
    }

    int x = random(1, 101);
    int AB = ((Pacote_RX[47] * 10) + Pacote_RX[48]);
    int CD = ((Pacote_RX[49] * 10) + Pacote_RX[50]);

    if (Pacote_RX[51] == 1 && x <= Pacote_RX[50]) {
      if (RX_ledblink) {
        digitalWrite(LED_vermelho, LOW);
      }
    } else if (Pacote_RX[51] == 2 && x <= (((AB + CD) % 5) + 1) * 10) {
      if (RX_ledblink) {
        digitalWrite(LED_vermelho, LOW);
      }
    } else {
      if (RX_ledblink) {
        delay(50);
        digitalWrite(LED_vermelho, LOW);
      }
      Mac_receive();
    }
  }
}

void Phy_send()  // Funcao de envio de pacote da Camada Física
{
  double Shadowing_marsaglia;
  box_muller(5, &Shadowing_marsaglia, NULL);

  if (TX_ledblink) {
    digitalWrite(LED_verde, HIGH);
  }

  if (Pacote_RX[51] == 3) {
    int BA = ((Pacote_RX[48] * 10) + Pacote_RX[47]);
    int DC = ((Pacote_RX[50] * 10) + Pacote_RX[49]);

    if (((BA + DC) % 5) == 0) {
      RSSI_dBm_dl = (-93 + Shadowing_marsaglia);
    } else if (((BA + DC) % 5) == 1) {
      RSSI_dBm_dl = (-86 + Shadowing_marsaglia);
    } else if (((BA + DC) % 5) == 2) {
      RSSI_dBm_dl = (-84 + Shadowing_marsaglia);
    } else if (((BA + DC) % 5) == 3) {
      RSSI_dBm_dl = (-79 + Shadowing_marsaglia);
    } else if (((BA + DC) % 5) == 4) {
      RSSI_dBm_dl = (-70 + Shadowing_marsaglia);
    }
  } else if (Pacote_RX[51] == 4) {
    Phy_shadowing();
  } else {
    RSSI_dBm_dl = WiFi.RSSI();
  }

  Phy_dBm_to_Radiuino();

  Pacote_TX[0] = RSSI_ul;
  Pacote_TX[1] = LQI_ul;
  Pacote_TX[2] = RSSI_dl;
  Pacote_TX[3] = LQI_dl;

  Serial.println(RSSI_dBm_dl);

  Udp.beginPacket(Udp.remoteIP(), Udp.remotePort());
  for (byte i = 0; i < 52; i++) {
    Udp.write(Pacote_TX[i]);
  }
  Udp.endPacket();

  if (TX_ledblink) {
    delay(50);
    digitalWrite(LED_verde, LOW);
  }
}

void Phy_dBm_to_Radiuino()
{
  if (RSSI_dBm_dl > -10.5)
  {
    RSSI_dl = 127;
    LQI_dl = 1;
  }

  if (RSSI_dBm_dl <= -10.5 && RSSI_dBm_dl >= -74)
  {
    RSSI_dl = ((RSSI_dBm_dl + 74) * 2);
    LQI_dl = 0;
  }

  if (RSSI_dBm_dl < -74)
  {
    RSSI_dl = (((RSSI_dBm_dl + 74) * 2) + 256);
    LQI_dl = 0;
  }
}

void Phy_shadowing()
{
  float Frequencia;
  float Ptx, Despacolivre, Dtotal;
  float Gtx, Grx, Beta, Shadowing, Pd0;
  float Lel, Lambda;
  double Shadowing_marsaglia;

  if (Pacote_RX[50] == 1) {
    Frequencia = 433e6;
  } else if (Pacote_RX[50] == 2) {
    Frequencia = 915e6;
  } else if (Pacote_RX[50] == 3) {
    Frequencia = 2.437e9;
  } else if (Pacote_RX[50] == 4) {
    Frequencia = 5.5e9;
  }

  Ptx = Pacote_RX[49] / 10.0;
  Gtx = Pacote_RX[48] / 10.0;
  Grx = Pacote_RX[47] / 10.0;
  Despacolivre = Pacote_RX[46];
  Beta = Pacote_RX[45] / 10.0;
  Dtotal = ((Pacote_RX[43] * 256) + Pacote_RX[44]);
  Shadowing = Pacote_RX[42];

  Lambda = 3e8 / Frequencia;
  Lel = pow(((12.5664 * Despacolivre) / Lambda), 2);
  Pd0 = Ptx + Gtx + Grx - 10 * log10(Lel);

  box_muller(Shadowing / 10, &Shadowing_marsaglia, NULL);
  RSSI_dBm_dl = Pd0 - 10 * Beta * (log10(Dtotal / Despacolivre)) + Shadowing_marsaglia;
}

void box_muller(double sigma, double *r1, double *r2) {
  double u1, u2, v1, v2, s, z1, z2;
  for (;;) {
    u1 = (float)random(RAND_MAX) / ((float)RAND_MAX + 1);
    u2 = (float)random(RAND_MAX) / ((float)RAND_MAX + 1);
    v1 = 2.0L * u1 - 1.0L;
    v2 = 2.0L * u2 - 1.0L;
    s = v1 * v1 + v2 * v2;
    if (s <= 1.0L && s != 0.0L)
      break;
  }
  z1 = sqrt(-2.0L * log(s) / s) * v1;
  z2 = sqrt(-2.0L * log(s) / s) * v2;
  if (r1 != NULL) *r1 = (z1 * sigma);
  if (r2 != NULL) *r2 = (z2 * sigma);

  return;
}
