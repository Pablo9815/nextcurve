<?php
  $ssid = $_POST["ssid"];
  $password = $_POST["password"];
  $config = "ctrl_interface=DIR=/var/run/wpa_supplicant GROUP=netdev
  update_config=1
  country=US

  network={
    ssid=" . "\"" . $ssid . "\"" . "
    psk=" . "\"" . $password . "\"" . "
    key_mgmt=WPA-PSK
  }";
  file_put_contents("/etc/wpa_supplicant/wpa_supplicant.conf", $config);
?>
<html>
  <head>
    <title>Configuración de red WiFi</title>
  </head>
  <body>
    <h1>Configuración de red WiFi</h1>
    <p>La configuración se ha guardado con éxito.</p>
  </body>
</html>
