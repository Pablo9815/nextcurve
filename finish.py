import os
import RPi.GPIO as GPIO
import time

#GPIO.setwarnings(False)


def main():
    os.system("sudo pkill start.py")
    GPIO.cleanup()
    GPIO.setmode(GPIO.BOARD)
    GPIO.setup(15, GPIO.OUT)
    print("Reiniciando")
    os.system("sudo python3 /home/pablonc/Documentos/start.py")
    start_time = time.time()
    while (time.time() - start_time) < 5:
        GPIO.output(15, GPIO.HIGH)
        time.sleep(0.1)
        GPIO.output(15, GPIO.LOW)
        time.sleep(0.1)
    GPIO.cleanup()
    

main()
