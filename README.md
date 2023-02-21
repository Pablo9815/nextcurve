##########CLONAR GITHUB

https://github.com/Pablo9815/nextcurve.git
RECORDAR PONER EL GITHUB EN PUBLICO PARA MAYOR FACILIDAD

##########LEVANTAR PAGINA WEB

sudo apt-get update

sudo apt-get install apache2 -y

sudo mv /var/www/html/index.html /var/www/html/index.html.orig

sudo cp (UBICACION DE index.html) /var/www/html/index.html

sudo cp (UBICACION DE submit.php) /var/www/html/submit.php

#########ACTIVAR SERVICIO PHP

https://techexpert.tips/es/apache-es/apache-instalacion-de-php-fpm-en-ubuntu-linux/
REEMPLAZAR a2enconf php7.4-fpm CON a2enconf php(TAB) PARA VER LA VERSION INSTALADA

#########PARA CORRER SCRIPT DE PYTHON

sudo apt install python3-pip
sudo apt-get install python3-dev python3-rpi.gpio
sudo pip3 install adafruit-blinka
sudo pip3 install adafruit-circuitpython-sgp30
sudo pip3 install paho-mqtt

#########PARA NO PEDIR CONTRASEÑA

sudo nano /etc/systemd/system/getty@tty1.service.d/autologin.conf
EN SECCION [SERVICE] PONER:
ExecStart=-/sbin/agetty --autologin TU_USUARIO --noclear %I $TERM

Activar interfaz I2C

#########CREAR HOSTPOT

https://pimylifeup.com/raspberry-pi-wireless-access-point/comment-page-1/

sudo crontab -e
@reboot sleep 60 && python /home/pablonc/Documentos/script.py

#########PARA CLONAR SD

https://www.thefastcode.com/es-eur/article/how-to-clone-your-raspberry-pi-sd-card-for-foolproof-backup

