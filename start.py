import os
import RPi.GPIO as GPIO
import time

GPIO.setwarnings(False)
GPIO.setmode(GPIO.BOARD)
GPIO.setup(11, GPIO.IN, pull_up_down=GPIO.PUD_UP)
GPIO.setup(13, GPIO.OUT)
GPIO.setup(15, GPIO.OUT)
task1 = True

def hostpot():
    GPIO.output(15, GPIO.LOW)
    print("Activando hostpot")
    os.system("sudo pkill sgp30code.py")
    os.system("sudo cp /etc/cloud/cloud.cfg.d/files/99-disable-network-config-host.cfg /etc/cloud/cloud.cfg.d/99-disable-network-config.cfg")
    os.system("sudo cp /etc/netplan/files/10-my-config-host.yaml /etc/netplan/10-my-config.yaml")
    os.system("sudo netplan apply")
    os.system("sudo chmod 0777 /etc/netplan/50-cloud-init.yaml")
    
    GPIO.output(13, GPIO.HIGH)

def callback(channel):
    global task1
    task1 = False
    hostpot()

def shutdown():
    os.system("sudo shutdown -r now")
    
def check_router():
    os.system("sudo rfkill unblock wifi")
    response = os.system("ping -c 1 192.168.0.1")
    return response == 0
    
GPIO.add_event_detect(11, GPIO.FALLING, callback=callback, bouncetime=500)

def main():
    while task1:
        GPIO.output(13, GPIO.LOW)
        GPIO.output(15, GPIO.HIGH)
        os.system("rfkill unblock wifi")
        os.system("sudo pkill finish.py")
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
        os.system("sudo python3 /home/pablonc/Documentos/sgp30code.py")
    
main()
