# python 3.6

import random
import time
import os
import sys
import RPi.GPIO as GPIO
import board
import busio
import adafruit_sgp30
from paho.mqtt import client as mqtt_client

GPIO.setwarnings(False)
GPIO.setmode(GPIO.BOARD)
GPIO.setup(11, GPIO.IN, pull_up_down=GPIO.PUD_UP)
GPIO.setup(13, GPIO.OUT)
GPIO.setup(15, GPIO.OUT)
task1 = True

try_count = 5
broker = '192.168.0.10'
port = 1883
topicTVOC = "pablo/raspberry/TVOC"
topicCO2e = "pablo/raspberry/CO2e"
# generate client ID with pub prefix randomly
client_id = f'python-mqtt-{random.randint(0, 1000)}'
username = 'admin'
password = 'admin'

def setup(try_count):
    print(".")
    if try_count > 0:
        try:
            i2c = busio.I2C(board.SCL, board.SDA, frequency=100000)

            # Create library object on our I2C port
            global sgp30
            sgp30 = adafruit_sgp30.Adafruit_SGP30(i2c)

            print("SGP30 serial #", [hex(i) for i in sgp30.serial])

            #sgp30.set_iaq_baseline(0x8973, 0x8AAE)
            sgp30.set_iaq_relative_humidity(celsius=22.1, relative_humidity=44)
            
            try_count = 5
        except:
            try_count -= 1
            time.sleep(2)
            setup(try_count)
        
    else:
        print("Something was wrong. Please reset device")
        sys.exit(1)

def hostpot():
    GPIO.output(15, GPIO.LOW)
    print("Activando hostpot")
    os.system("sudo cp /etc/cloud/cloud.cfg.d/files/99-disable-network-config-host.cfg /etc/cloud/cloud.cfg.d/99-disable-network-config.cfg")
    os.system("sudo cp /etc/netplan/files/10-my-config-host.yaml /etc/netplan/10-my-config.yaml")
    os.system("sudo netplan apply")
    os.system("sudo chmod 0777 /etc/netplan/50-cloud-init.yaml")
    
    GPIO.output(13, GPIO.HIGH)

def callback(channel):
    global task1
    task1 = False
    hostpot()
    
GPIO.add_event_detect(11, GPIO.FALLING, callback=callback, bouncetime=500)
        
def turn_wifi_off():
    os.system("sudo rfkill block wifi")
    print("Turning off")
    
def turn_wifi_on():
    os.system("sudo rfkill unblock wifi")
    print("Turning on")
    
    crono_start = time.time()
    while not check_router():
        crono_end = time.time()
        if (crono_end - crono_start) < 20:
            print("Waiting")
            time.sleep(2)
        else:
            print("Unable to connect to network. Check your router and reset this device")
            sys.exit(1)
    
def check_router():
    response = os.system("ping -c 1 192.168.0.1")
    return response == 0

def connect_mqtt(crono_start):
    def on_connect(client, userdata, flags, rc):
        if rc == 0:
            print("Connected to MQTT Broker!")
        else:
            print("Failed to connect, return code %d\n", rc)

    client = mqtt_client.Client(client_id)
    client.username_pw_set(username, password)
    client.on_connect = on_connect
    
    try:
        client.connect(broker, port)
    except:
        crono_end = time.time()
        print("Can't connect to server")
        if (crono_end - crono_start) < 20:
            connect_mqtt(crono_start)
        else:
            print("Unable to connect to broker MQTT. Check your server and reset this device")
            sys.exit(1)
    return client


def publish(TVOC_avg, CO2e_avg):
    turn_wifi_on()
    crono_start = time.time()
    client = connect_mqtt(crono_start)
    client.loop_start()
    
    result1 = client.publish(topicTVOC, float("{0:.3f}".format(TVOC_avg)))
    result2 = client.publish(topicCO2e, float("{0:.3f}".format(CO2e_avg)))
    time.sleep(1)
    turn_wifi_off()
    
    status = result1[0]
    if status == 0:
        print("TVOC = %d ppb" % (TVOC_avg))
    else:
        print(f"Failed to send TVOC to topic {topicTVOC}")
    
    status = result2[0]
    if status == 0:
        print("CO2e = %d ppm" % (CO2e_avg))
    else:
        print(f"Failed to send CO2e to topic {topicCO2e}")
        
def measure_values():
    value_count = 0
    TVOC_aux = 0
    CO2e_aux = 0
    while True:
        print("Midiendo")
        TVOC = sgp30.TVOC
        CO2e = sgp30.eCO2
        
        TVOC_aux += TVOC
        CO2e_aux += CO2e
        
        time.sleep(1)
        value_count += 1
        
        if value_count >= 10:
            TVOC_avg = TVOC_aux/value_count
            CO2e_avg = CO2e_aux/value_count
            print(CO2e_avg)
            print(TVOC_avg)
            
            publish(TVOC_avg, CO2e_avg)
                    
            value_count = 0
            TVOC_aux = 0
            CO2e_aux = 0
            print(
                "**** Baseline values: eCO2 = 0x%x, TVOC = 0x%x"
                % (sgp30.baseline_eCO2, sgp30.baseline_TVOC)
            )

def sgp30code(try_count):
    if try_count > 0:
        try:
            time.sleep(2)
            turn_wifi_on()
            crono_start = time.time()
            client = connect_mqtt(crono_start)
            print("Listo")
            turn_wifi_off()
            measure_values()
            try_count = 5
        except:
            try_count -= 1
            sgp30code(try_count)
    else:
        print("Something was wrong. Please reset device")
        sys.exit(1)
        
def config(try_count):
    while task1:
        GPIO.cleanup()
        GPIO.output(13, GPIO.LOW)
        GPIO.output(15, GPIO.HIGH)
        os.system("sudo rfkill unblock wifi")
        os.system("sudo rm /etc/cloud/cloud.cfg.d/99-disable-network-config.cfg")
        os.system("sudo rm /etc/netplan/10-my-config.yaml")
        os.system("sudo netplan apply")
        while not check_router():
            crono_start = time.time()
            while (time.time() - crono_start) <= 6:
                GPIO.output(15, GPIO.LOW)
                time.sleep(0.5)
                GPIO.output(15, GPIO.HIGH)
                time.sleep(0.5)
        print("Ejecutando script")
        print("Configurando")
        setup(try_count)
        sgp30code(try_count)

config(try_count)
