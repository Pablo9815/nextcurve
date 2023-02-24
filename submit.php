<html>
  <head>
    <title>Configuración de red WiFi</title>
  </head>
  <body>
    <h1>Configuración de red WiFi</h1>
    <p>La configuración se ha guardado con éxito. El dispositivo se reiniciará en unos segundos.</p>
  </body>
</html>

<?php
  $ssid = $_POST["ssid"];
  $password = $_POST["password"];
  $config = "network:
    version: 2
    wifis:
        renderer: networkd
        wlan0:
            access-points:
                " . "\"" . $ssid . "\"" . "
                    password: " . "\"" . $password . "\"" . "
            dhcp4: true
            optional: true";
  file_put_contents("/etc/netplan/50-cloud-init.yaml", $config);
  
  // Esperar 5 segundos y luego reiniciar la Raspberry Pi
  shell_exec('sudo python3 /home/pablonc/Documentos/finish.py');
?>
