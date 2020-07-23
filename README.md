# rpiupspackcomms
Tools for communicating with the RPi UPSPack circuit board via its TTL/USB port

Board may be purchased from here: https://www.makerfocus.com/products/raspberry-pi-expansion-board-ups-pack-standard-power-supply

To build and install for Debian systems:-

```
cd /tmp
rm -Rf rpiupspackcomms*
git clone https://github.com/thomasblackshaw/rpiupspackcomms.git
cd rpiupspackcomms
bash setup/build_for_debian.sh
apt install python3-serial
dpkg -i rpiupspackcomms*.deb
```

Or, for non-Debian-derived GNU/Linux operating systems:-

```
cd /tmp
rm -Rf rpiupspackcomms*
git clone https://github.com/thomasblackshaw/rpiupspackcomms.git
cd rpiupspackcomms
bash setup/install_on_generic.sh
```


