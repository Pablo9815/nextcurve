import os
import RPi.GPIO as GPIO
import time

GPIO.setwarnings(False)
GPIO.setmode(GPIO.BOARD)
GPIO.setup(11, GPIO.IN, pull_up_down=GPIO.PUD_UP)
GPIO.setup(13, GPIO.OUT)
GPIO.setup(15, GPIO.OUT)

def hostpot():
    GPIO.output(15, GPIO.LOW)
    print("Activando hostpot")
    os.system("sudo cp /etc/dhcpcdhost.conf /etc/dhcpcd.conf")
    os.system("sudo service dhcpcd restart")
    os.system("sudo systemctl unmask hostapd")
    os.system("sudo systemctl enable hostapd")
    os.system("sudo systemctl start hostapd")
    os.system("sudo service dnsmasq start")
    os.system("sudo chmod 0777 /etc/wpa_supplicant/wpa_supplicant.conf")
    
    GPIO.output(13, GPIO.HIGH)

def callback(channel):
    hostpot()

def shutdown():
    os.system("sudo shutdown -r now")
    
def check_router():
    os.system("sudo rfkill unblock wifi")
    response = os.system("ping -c 1 192.168.0.1")
    return response == 0
    
GPIO.add_event_detect(11, GPIO.FALLING, callback=callback, bouncetime=500)

def main():
    GPIO.output(13, GPIO.LOW)
    GPIO.output(15, GPIO.HIGH)
    os.system("rfkill unblock wifi")
    os.system("sudo pkill finish.py")
    os.system("sudo cp /etc/dhcpcdwifi.conf /etc/dhcpcd.conf")
    os.system("sudo systemctl disable hostapd")
    os.system("sudo systemctl stop hostapd")
    os.system("sudo service dnsmasq stop")
    os.system("sudo service dhcpcd restart")
    while not check_router():
        GPIO.output(15, GPIO.LOW)
        time.sleep(1)
        GPIO.output(15, GPIO.HIGH)
        time.sleep(1)
    print("Ejecutando script")
    os.system("sudo python3 /home/pablonc/Documentos/sgp30code.py")
    
main()