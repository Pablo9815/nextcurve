<?php
  $ssid = $_POST["ssid"];
  $password = $_POST["password"];
  $config = "network:
    version: 2
    wifis:
        renderer: networkd
        wlan0:
            access-points:
                " . "\"" . $ssid . "\"" . ":
                    password: " . "\"" . $password . "\"" . "
            dhcp4: true
            optional: true";
  file_put_contents("/etc/netplan/50-cloud-init.yaml", $config);
 
  shell_exec('sudo python3 /home/pablonc/Documentos/code.py');
?>

<html>
  <head>
    <title>Configuracion de red WiFi</title>
  </head>
  <body>
    <h1>Configuracion de red WiFi</h1>
    <p>La configuracion se ha guardado con exito. El dispositivo se reiniciara en unos segundos.</p>
  </body>
</html>

