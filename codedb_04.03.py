import random
import time
import os
import sys
import RPi.GPIO as GPIO
import board
import busio
import adafruit_sgp30
import adafruit_dht
import sqlite3

GPIO.setwarnings(False)
GPIO.setmode(GPIO.BCM)
GPIO.setup(17, GPIO.IN, pull_up_down=GPIO.PUD_UP)
GPIO.setup(27, GPIO.OUT)
GPIO.setup(22, GPIO.OUT)
GPIO.setup(10, GPIO.OUT)

try_count = 8

# Connect to the SQLite database
#con = sqlite3.connect('storage.db')
#cur = con.cursor()

#cur.execute('''CREATE TABLE IF NOT EXISTS data
#        (temperature real, humidity real, tvoc real, co2eq real)''')


def setup(try_count):
    print(".")
    if try_count > 0:
        try:
            global dhtDevice
            dhtDevice = adafruit_dht.DHT22(board.D4)
            i2c = busio.I2C(board.SCL, board.SDA, frequency=100000)

            # Create library object on our I2C port
            global sgp30
            sgp30 = adafruit_sgp30.Adafruit_SGP30(i2c)

            print("SGP30 serial #", [hex(i) for i in sgp30.serial])

            try_count = 8
        except:
            try_count -= 1
            time.sleep(2)
            setup(try_count)

    else:
        print("Something was wrong. Please check this device")
        GPIO.output(27, GPIO.LOW)
        GPIO.output(22, GPIO.LOW)
        GPIO.output(10, GPIO.HIGH)
        try_count = 8
        config(try_count)

def hostpot():
    GPIO.output(22, GPIO.HIGH)
    GPIO.output(27, GPIO.HIGH)
    GPIO.output(10, GPIO.HIGH)
    print("Activating hostpot")
    os.system("sudo cp /etc/cloud/cloud.cfg.d/files/99-disable-network-config-host.cfg /etc/cloud/cloud.cfg.d/99-disable-network-config.cfg")
    os.system("sudo cp /etc/netplan/files/10-my-config-host.yaml /etc/netplan/10-my-config.yaml")
    os.system("sudo netplan apply")
    os.system("sudo chmod 0777 /etc/netplan/50-cloud-init.yaml")
    time.sleep(3)
    os.system("sudo pkill -f codedb_04.03.py")

def callback(channel):
    hostpot()

GPIO.add_event_detect(17, GPIO.FALLING, callback=callback, bouncetime=500)

def turn_wifi_off():
    os.system("sudo rfkill block wifi")
    print("Turning off")

def turn_wifi_on():
    os.system("sudo rfkill unblock wifi")
    print("Turning on")

def check_router():
    response = os.system("ping -c 1 192.168.0.1")
    return response == 0

def push_data(temp, temperature_aqi, hum, humidity_aqi, TVOC_avg, tvoc_aqi, CO2e_avg, co2eq_aqi):
    con = sqlite3.connect('data_base_NC.db')
    cur = con.cursor()

    cur.execute('''CREATE TABLE IF NOT EXISTS air
                    (T text, T_r text, H text, H_r text, TVOC text, TVOC_r text, CO2 text, CO2_r text)''')

    cur.execute('''INSERT INTO air (T, T_r, H, H_r, TVOC, TVOC_r, CO2, CO2_r) VALUES (?, ?, ?, ?, ?, ?, ?, ?)''',
                    (temp, temperature_aqi, hum, humidity_aqi, TVOC_avg, tvoc_aqi, CO2e_avg, co2eq_aqi))
    con.commit()
    print("Data pushed successfully.")


def measure_values():
    value_count = 0
    TVOC_aux = 0
    CO2e_aux = 0
    while True:
        print("Midiendo")
        DHTread = True
        DHTcount = 0
        sgp30read = True
        sgp30count = 0
        while DHTread:
            if DHTcount < 20:
                try:
                    temp = dhtDevice.temperature
                    hum = dhtDevice.humidity
                    print(temp)
                    print(hum)
                    if temp is not None or hum is not None:
                        sgp30.set_iaq_relative_humidity(celsius=temp, relative_humidity=hum)
                        DHTread = False
                        DHTcount = 0
                        print("obtuvo t h")
                    else:
                        time.sleep(0.5)
                        DHTcount += 1
                except:
                    print("NO t h")
                    time.sleep(1)
                    DHTcount += 1
                    continue
            else:
                print("Unable to find temperature and humidity sensor. Check this device")
                GPIO.output(27, GPIO.LOW)
                GPIO.output(22, GPIO.LOW)
                GPIO.output(10, GPIO.HIGH)
                try_count = 8
                config(try_count)

        while sgp30read:
            if sgp30count < 20:
                try:
                    sgp30.set_iaq_baseline(0x9636, 0x95C0) #CALIBRAR PARA CADA SENSOR SGP30

                    TVOC = sgp30.TVOC
                    CO2e = sgp30.eCO2

                    TVOC_aux += TVOC
                    CO2e_aux += CO2e

                    time.sleep(1)
                    value_count += 1

                    sgp30read = False

                    if value_count >= 5:
                        TVOC_avg = TVOC_aux/value_count
                        CO2e_avg = CO2e_aux/value_count
                        print(CO2e_avg)
                        print(TVOC_avg)

                        print("Pusheando")
                        push_data(temp, hum, TVOC_avg, CO2e_avg)
#temperature_aqi, humidity_aqi, tvoc_aqi, co2eq_aqi = calculate_air_quality(temp, hum, TVOC_avg, CO2e_avg)

 #                       push_data(temp, temperature_aqi, hum, humidity_aqi, TVOC_avg, tvoc_aqi, CO2e_avg, co2eq_aqi)

                        value_count = 0
                        TVOC_aux = 0
                        CO2e_aux = 0
                        print(
                            "**** Baseline values: eCO2 = 0x%x, TVOC = 0x%x"
                            % (sgp30.baseline_eCO2, sgp30.baseline_TVOC)
                        )
                except:
                    print("NO info from sgp30")
                    time.sleep(1)
                    sgp30count += 1
                    continue

            else:
                print("Unable to find sgp30 sensor. Check this device")
                GPIO.output(27, GPIO.LOW)
                GPIO.output(22, GPIO.LOW)
                GPIO.output(10, GPIO.HIGH)
                try_count = 8
                config(try_count)


def sgp30code(try_count):
    if try_count > 0:
        try:
            time.sleep(2)
            # turn_wifi_on()
            measure_values()
            try_count = 8
        except:
            try_count -= 1
            sgp30code(try_count)
    else:
        print("Something was wrong. Please reset this device")
        GPIO.output(27, GPIO.LOW)
        GPIO.output(22, GPIO.LOW)
        GPIO.output(10, GPIO.HIGH)
        try_count = 8
        config(try_count)

def config(try_count):
    GPIO.output(27, GPIO.LOW)
    GPIO.output(22, GPIO.HIGH)
    GPIO.output(10, GPIO.HIGH)

    if not check_router():
        os.system("sudo rfkill unblock wifi")
        os.system("sudo rm /etc/cloud/cloud.cfg.d/99-disable-network-config.cfg")
        os.system("sudo rm /etc/netplan/10-my-config.yaml")
        os.system("sudo netplan apply")

        GPIO.output(27, GPIO.HIGH)
        GPIO.output(22, GPIO.LOW)
        GPIO.output(10, GPIO.LOW)
        crono_start = time.time()
        while ((time.time() - crono_start) <= 20) and (not check_router()):
            GPIO.output(27, GPIO.LOW)
            time.sleep(0.5)
            GPIO.output(27, GPIO.HIGH)
            time.sleep(0.5)
        if not check_router():
            GPIO.output(27, GPIO.HIGH)
        else:
            GPIO.output(27, GPIO.LOW)
            GPIO.output(22, GPIO.HIGH)
            GPIO.output(10, GPIO.LOW)
    else:
        GPIO.output(27, GPIO.LOW)
        GPIO.output(22, GPIO.HIGH)
        GPIO.output(10, GPIO.LOW)

    print("Ejecutando script")
    print("Configurando")
    setup(try_count)
    sgp30code(try_count)

config(try_count)
