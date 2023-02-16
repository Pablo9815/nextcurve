import os
import RPi.GPIO as GPIO
import time

GPIO.setwarnings(False)
GPIO.setmode(GPIO.BOARD)
GPIO.setup(11, GPIO.IN, pull_up_down=GPIO.PUD_UP)
GPIO.setup(13, GPIO.OUT)

def hostpot():
    print("Activando hostpot")
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
    
GPIO.add_event_detect(11, GPIO.FALLING, callback=callback, bouncetime=500)

def main():
    os.system("sudo systemctl disable hostapd")
    os.system("sudo systemctl stop hostapd")
    os.system("sudo service dnsmasq stop")
    
main()
