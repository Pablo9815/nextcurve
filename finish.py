import os
import RPi.GPIO as GPIO
import time

#GPIO.setwarnings(False)


def main():
    GPIO.cleanup()
    GPIO.setmode(GPIO.BOARD)
    GPIO.setup(15, GPIO.OUT)
    os.system("sudo pkill start.py")
    print("Reiniciando")
    os.system("sudo python3 /home/pablonc/Documentos/start.py")
    start_time = time.time()
    while (time.time() - start_time) < 5:
        GPIO.output(15, GPIO.HIGH)
        time.sleep(0.2)
        GPIO.output(15, GPIO.LOW)
        time.sleep(0.2)
    GPIO.cleanup()
    

main()