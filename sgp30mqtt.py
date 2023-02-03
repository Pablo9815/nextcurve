# python 3.6

import random
import time
import os
import board
import busio
import adafruit_sgp30

from paho.mqtt import client as mqtt_client

i2c = busio.I2C(board.SCL, board.SDA, frequency=100000)

# Create library object on our I2C port
sgp30 = adafruit_sgp30.Adafruit_SGP30(i2c)

broker = '192.168.0.2'
port = 1883
topicTVOC = "pablo/raspberry/TVOC"
topicCO2e = "pablo/raspberry/CO2e"
# generate client ID with pub prefix randomly
client_id = f'python-mqtt-{random.randint(0, 1000)}'
username = 'admin'
password = 'admin'

print("SGP30 serial #", [hex(i) for i in sgp30.serial])

sgp30.set_iaq_baseline(0x8973, 0x8AAE)
sgp30.set_iaq_relative_humidity(celsius=22.1, relative_humidity=44)

def check_router():
    response = os.system("ping -c 1 192.168.0.1")
    return response == 0

def connect_mqtt():
    def on_connect(client, userdata, flags, rc):
        if rc == 0:
            print("Connected to MQTT Broker!")
        else:
            print("Failed to connect, return code %d\n", rc)

    client = mqtt_client.Client(client_id)
    client.username_pw_set(username, password)
    client.on_connect = on_connect
    client.connect(broker, port)
    return client


def publish(client):
    value_count = 0
    TVOC_aux = 0
    CO2e_aux = 0
    while True:
        TVOC = sgp30.TVOC
        CO2e = sgp30.eCO2
        
        TVOC_aux += TVOC
        CO2e_aux += CO2e
        
        time.sleep(1)
        value_count += 1
        
        if value_count > 10:
            if check_router():
                print(value_count)
                print(CO2e_aux)
                TVOC_avg = TVOC_aux/value_count
                CO2e_avg = CO2e_aux/value_count
                print(CO2e_avg)
                
                result1 = client.publish(topicTVOC, float("{0:.3f}".format(TVOC_avg)))
                result2 = client.publish(topicCO2e, float("{0:.3f}".format(CO2e_avg)))
        
                value_count = 0
                TVOC_aux = 0
                CO2e_aux = 0
                print(
                    "**** Baseline values: eCO2 = 0x%x, TVOC = 0x%x"
                    % (sgp30.baseline_eCO2, sgp30.baseline_TVOC)
                )
                
                status = result1[0]
                if status == 0:
                    print("TVOC = %d ppb" % (TVOC))
                else:
                    print(f"Failed to send TVOC to topic {topicTVOC}")
                
                status = result2[0]
                if status == 0:
                    print("CO2e = %d ppm" % (CO2e))
                else:
                    print(f"Failed to send CO2e to topic {topicCO2e}")
            else:
                print("Without connection")
                time.sleep(10)
                run()
        
def run():
    while True:
        if check_router():
            client = connect_mqtt()
            client.loop_start()
            publish(client)
        else:
            print("Without connection")
            time.sleep(10)


if __name__ == '__main__':
    run()
