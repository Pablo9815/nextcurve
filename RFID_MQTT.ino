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

TaskHandle_t Task1;

static unsigned long lastTime = 0;

// Definimos los pines del ESP32 que se utilizarán para controlar el LED RGB
const int redPin = 15;
const int greenPin = 2;
const int bluePin = 4;
const int buzzerPin = 5;

//*****************************************************************************************//
void setup() {
  Serial.begin(115200);                                           // Initialize serial communications with the PC
  SPI.begin();                                                  // Init SPI bus
  
  // Configuramos los pines como salidas
  pinMode(redPin, OUTPUT);
  pinMode(greenPin, OUTPUT);
  pinMode(bluePin, OUTPUT);
  pinMode(buzzerPin, OUTPUT);

  // Apagamos todos los LEDs al iniciar el programa
  digitalWrite(redPin, LOW);
  digitalWrite(greenPin, HIGH);
  digitalWrite(bluePin, HIGH);
  digitalWrite(buzzerPin, LOW);
  
  mfrc522.PCD_Init();                                              // Init MFRC522 card
  Serial.println(F("Read personal data on a MIFARE PICC:"));    //shows in serial that it is ready to read
  setup_wifi();
  client.setServer(mqtt_server, 1883);
  client.setCallback(callback);
  
  // Configuración del objeto NTPClient
  timeClient.begin();

  if (!client.connected()) {
    reconnect();
  }

  client.loop();
  client.publish("esp32/check", "ON");
  
  xTaskCreatePinnedToCore(
                    Task1code,   /* Task function. */
                    "Task1",     /* name of task. */
                    2000,       /* Stack size of task */
                    NULL,        /* parameter of the task */
                    0,           /* priority of the task */
                    &Task1,      /* Task handle to keep track of created task */
                    0);          /* pin task to core 0 */
  delay(500);
}

void Task1code( void * pvParameters ){
  for(;;){
    Serial.print("Task1 running on core ");
    Serial.println(xPortGetCoreID());
  
    if (WiFi.status() != WL_CONNECTED) {
      setup_wifi();
    }
    if (!client.connected()) {
      reconnect();
    }
    
    delay(1000);
  }
}

//*****************************************************************************************//
void loop() {
  Serial.print("TaskLoop running on core ");
  Serial.println(xPortGetCoreID());

  if (!client.connected()) {
    digitalWrite(redPin, LOW);
    digitalWrite(greenPin, HIGH);
    digitalWrite(bluePin, HIGH);
    } else {
      digitalWrite(redPin, HIGH);
      digitalWrite(greenPin, LOW);
      digitalWrite(bluePin, HIGH);
      }
      
  if (millis() - lastTime >= 5000) { // Si han pasado 5 minutos desde la última ejecución
      lastTime = millis(); // Actualiza el tiempo de la última ejecución
      client.loop();
      client.publish("esp32/check", "ON");
    }
  
  /*if (!client.connected()) {
    reconnect();
  }*/
  client.loop();
  client.publish("esp32/reset", "False");
  
  // Prepare key - all keys are set to FFFFFFFFFFFFh at chip delivery from the factory.
  MFRC522::MIFARE_Key key;
  for (byte i = 0; i < 6; i++) key.keyByte[i] = 0xFF;

  MFRC522::StatusCode status;

  if (client.connected() && WiFi.status() == WL_CONNECTED && counter != 0) {
      publish_data();
    }

  /*if (!mfrc522.PCD_PerformSelfTest()) {
    SPI.begin();
    mfrc522.PCD_Init();
    }*/
  // Reset the loop if no new card present on the sensor/reader. This saves the entire process when idle.
  if ( ! mfrc522.PICC_IsNewCardPresent()) {
    return;
  }

  digitalWrite(redPin, HIGH);
  digitalWrite(greenPin, HIGH);
  digitalWrite(bluePin, HIGH);

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
}

void publish_data() {
  Serial.println("!!!!!!!!!!! Publicando datos !!!!!!!!!!!!!!");
  for (int i = 0; i < counter; i += 2) {
    String dirTimeSaved = String(i);
    String dirIDSaved = String(i+1);
    String sampleTimeSaved = myPrefs.getString(dirTimeSaved.c_str(), "");
    String IDSaved = myPrefs.getString(dirIDSaved.c_str(), "");
    char* sampleTime = strdup(sampleTimeSaved.c_str());
    char* ID = strdup(IDSaved.c_str());
    
    client.publish("esp32/time", sampleTime);
    client.publish("esp32/location", location);
    client.publish("esp32/id_read", ID);
    Serial.print(sampleTime);
    Serial.print("  ");
    Serial.println(ID);
    delay(1100);
  }
  myPrefs.end();
  counter = 0;
}

void save_data(char* sampleTime, char* ID) {
  Serial.println("########## Salvando datos #################");
  myPrefs.begin("Storage", false);
  
  String direccionTime = String(counter);                                 //Address for saving measurement data. Position n*(ContToPublish+1)
  String direccionID = String(counter+1);
  
  myPrefs.putString(direccionTime.c_str(), sampleTime);                  //Save data in flash memory
  myPrefs.putString(direccionID.c_str(), ID);
  counter += 2;

  delay(500);
  digitalWrite(redPin, HIGH);
  digitalWrite(greenPin, LOW);
  digitalWrite(bluePin, HIGH);
  digitalWrite(buzzerPin, HIGH);
  delay(500);
  digitalWrite(buzzerPin, LOW);
}

void setup_wifi() {
  delay(10);
  // We start by connecting to a WiFi network
  Serial.println();
  Serial.print("Connecting to ");
  Serial.println(ssid);

  WiFi.begin(ssid, password);

  while (WiFi.status() != WL_CONNECTED) {
    digitalWrite(redPin, HIGH);
    digitalWrite(greenPin, HIGH);
    digitalWrite(bluePin, LOW);
    delay(250);
    Serial.print(".");
    digitalWrite(redPin, HIGH);
    digitalWrite(greenPin, HIGH);
    digitalWrite(bluePin, HIGH);
    delay(250);
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
    
    digitalWrite(redPin, LOW);
    digitalWrite(greenPin, HIGH);
    digitalWrite(bluePin, HIGH);
    
    Serial.print("Attempting MQTT connection...");
    // Attempt to connect
    if (client.connect("ESP8266Client", "admin", "admin")) {
      Serial.println("connected");
      // Subscribe
      client.subscribe("esp32/output");
    } else {
      Serial.print("failed, rc=");
      Serial.print(client.state());
      Serial.println(" try again in 0.5 seconds");
      // Wait 5 seconds before retrying
      delay(500);
    }
  }
}
  
String timeToString(time_t time) {
  char bufferTime[20];
  sprintf(bufferTime, "%02d:%02d:%02d %02d/%02d/%04d", hour(time), minute(time), second(time), day(time), month(time), year(time));
  return String(bufferTime);
}
