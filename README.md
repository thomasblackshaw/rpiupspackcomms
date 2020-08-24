# rpiupspackcomms
Tools for communicating with the RPi UPSPack circuit board via its TTL/USB port

Board may be purchased from here: https://www.makerfocus.com/products/raspberry-pi-expansion-board-ups-pack-standard-power-supply

To build and install::

```
wget http://bit.do/rpiups_debian -O /tmp/installer.sh && bash /tmp/installer.sh
OR
wget http://bit.do/rpiups_generic -O /tmp/installer.sh && bash /tmp/installer.sh
```

To uninstall:-
```apt-get remove rpiupspackcomms
OR
bash /usr/share/rpiupspackcomms/setup/uninstall_from_generic.sh
```

There.
