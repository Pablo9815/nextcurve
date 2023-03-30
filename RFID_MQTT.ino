#include <SPI.h>
#include <MFRC522.h>
#include <WiFi.h>
#include <PubSubClient.h>
#include <Wire.h>
#include <WiFiUdp.h>
#include <NTPClient.h>
#include <Preferences.h>
#include <TimeLib.h>

#define location  "room_1"

#define RST_PIN         22           // Configurable, see typical pin layout above
#define SS_PIN          21          // Configurable, see typical pin layout above

MFRC522 mfrc522(SS_PIN, RST_PIN);   // Create MFRC522 instance

// Replace the next variables with your SSID/Password combination
const char* ssid = "pablonet";
const char* password = "98150012";

// Add your MQTT Broker IP address, example:
const char* mqtt_server = "192.168.1.2";

// Configuración del servidor NTP
const char* ntpServer = "pool.ntp.org";
const int ntpPort = 123;

// Zona horaria de Orlando, Florida
const int timeZoneOffset = -5; // UTC-5

WiFiUDP ntpUDP;
NTPClient timeClient(ntpUDP, ntpServer, timeZoneOffset * 3600, 60000);

WiFiClient espClient;
PubSubClient client(espClient);
long lastMsg = 0;
char msg[50];
int value = 0;

Preferences myPrefs;
int counter = 0;

//*****************************************************************************************//
void setup() {
  Serial.begin(115200);                                           // Initialize serial communications with the PC
  SPI.begin();                                                  // Init SPI bus
  mfrc522.PCD_Init();                                              // Init MFRC522 card
  Serial.println(F("Read personal data on a MIFARE PICC:"));    //shows in serial that it is ready to read
  setup_wifi();
  client.setServer(mqtt_server, 1883);
  client.setCallback(callback);
  
  // Configuración del objeto NTPClient
  timeClient.begin();
}

//*****************************************************************************************//
void loop() {
  
  if (!client.connected()) {
    reconnect();
  }
  client.loop();
  client.publish("esp32/reset", "False");
  
  // Prepare key - all keys are set to FFFFFFFFFFFFh at chip delivery from the factory.
  MFRC522::MIFARE_Key key;
  for (byte i = 0; i < 6; i++) key.keyByte[i] = 0xFF;

  MFRC522::StatusCode status;

  // Reset the loop if no new card present on the sensor/reader. This saves the entire process when idle.
  if ( ! mfrc522.PICC_IsNewCardPresent()) {
    return;
  }

  // Select one of the cards
  if ( ! mfrc522.PICC_ReadCardSerial()) {
    return;
  }

  Serial.println(F("**Card Detected:**"));
  
  obtain_data(mfrc522.uid.uidByte, mfrc522.uid.size);
  
  Serial.println(F("\n**End Reading**\n"));

  delay(1000); //change value if you want to read cards faster

  mfrc522.PICC_HaltA();
  mfrc522.PCD_StopCrypto1();
}

void obtain_data(byte *buffer, byte bufferSize) {
    char output[bufferSize*3 + 1]; // Se define la variable char con tamaño suficiente para contener todos los elementos del buffer y los espacios en blanco
    output[0] = '\0'; // Se inicializa la variable con una cadena vacía
    
    for (byte i = 0; i < bufferSize; i++) {
        sprintf(output + strlen(output), "%s%02X", i == 0 ? "" : "", buffer[i]); // Se concatena cada elemento del buffer a la variable char
    }

    
    // Actualización del objeto NTPClient si hay conexión a Internet
    if (WiFi.status() == WL_CONNECTED) {
      Serial.println("Sincronizando hora con servidor NTP...");
      timeClient.update();
      setTime(timeClient.getEpochTime());
    }
    // Obtención de la hora actual y formateo
    String formattedTime = timeToString(now());
    char bufferTimepub[20];
    formattedTime.toCharArray(bufferTimepub, 20);


    save_data(bufferTimepub, output);
    
    if (WiFi.status() == WL_CONNECTED) {
      publish_data(bufferTimepub, output);
    }
    
}

void publish_data(char* sampleTime, char* ID) {
  for (int i = 0; i < counter; i += 2) {
    String dirTimeSaved = String(i);
    String dirIDSaved = String(i+1);
    String sampleTimeSaved = myPrefs.getString(dirTimeSaved.c_str(), "");
    String IDSaved = myPrefs.getString(dirIDSaved.c_str(), "");
    sampleTime = strdup(sampleTimeSaved.c_str());
    ID = strdup(IDSaved.c_str());
    
    client.publish("esp32/time", sampleTime);
    client.publish("esp32/location", location);
    client.publish("esp32/id_read", ID);
  }
  myPrefs.end();
  counter = 0;
}

void save_data(char* sampleTime, char* ID) {
  myPrefs.begin("Storage", false);
  
  String direccionTime = String(counter);                                 //Address for saving measurement data. Position n*(ContToPublish+1)
  String direccionID = String(counter+1);
  
  myPrefs.putString(direccionTime.c_str(), sampleTime);                  //Save data in flash memory
  myPrefs.putString(direccionID.c_str(), ID);
  counter += 2;
}

void setup_wifi() {
  delay(10);
  // We start by connecting to a WiFi network
  Serial.println();
  Serial.print("Connecting to ");
  Serial.println(ssid);

  WiFi.begin(ssid, password);

  while (WiFi.status() != WL_CONNECTED) {
    delay(500);
    Serial.print(".");
  }
  
  Serial.println("");
  Serial.println("WiFi connected");
  Serial.println("IP address: ");
  Serial.println(WiFi.localIP());
}

void callback(char* topic, byte* message, unsigned int length) {
  Serial.print("Message arrived on topic: ");
  Serial.print(topic);
  Serial.print(". Message: ");
  String messageTemp;
  
  for (int i = 0; i < length; i++) {
    Serial.print((char)message[i]);
    messageTemp += (char)message[i];
  }
  Serial.println();

  // Feel free to add more if statements to control more GPIOs with MQTT

  // If a message is received on the topic esp32/output, you check if the message is either "on" or "off". 
  // Changes the output state according to the message
  if (String(topic) == "esp32/output") {
    if(messageTemp == "state"){
      Serial.print("State: ");
      if (!mfrc522.PCD_PerformSelfTest()) {
        Serial.println(F("Self test failed, possibly a connection issue or faulty module"));
        Serial.println("Error");
      client.publish("esp32/state", "Error");
      }
      else {
        Serial.println("OK");
        client.publish("esp32/state", "OK");
      }
    }
    else if(messageTemp == "reset"){
      client.publish("esp32/reset", "True");
      Serial.print("resetting");
      delay(2000);
      ESP.restart();
    }
  }
}

void reconnect() {
  // Loop until we're reconnected
  while (!client.connected()) {
    Serial.print("Attempting MQTT connection...");
    // Attempt to connect
    if (client.connect("ESP8266Client", "admin", "admin")) {
      Serial.println("connected");
      // Subscribe
      client.subscribe("esp32/output");
    } else {
      Serial.print("failed, rc=");
      Serial.print(client.state());
      Serial.println(" try again in 5 seconds");
      // Wait 5 seconds before retrying
      delay(5000);
    }
  }
}
  
String timeToString(time_t time) {
  char bufferTime[20];
  sprintf(bufferTime, "%02d:%02d:%02d %02d/%02d/%04d", hour(time), minute(time), second(time), day(time), month(time), year(time));
  return String(bufferTime);
}
