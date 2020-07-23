#!/bin/bash



#https://linuxconfig.org/easy-way-to-create-a-debian-package-and-local-package-repository

OURVER=0.1-1

set +e
mkdir -p rpiupspackcomms/DEBIAN
mkdir -p rpiupspackcomms/usr/local/{bin,share/rpiupspackcomms}
cd       rpiupspackcomms/usr/local/share/rpiupspackcomms 
git clone https://github.com/thomasblackshaw/rpiupspackcomms.git rpiupspackcomms/usr/local/share/rpiupspackcomms
chmod +x rpiupspackcomms/usr/local/share/rpiupspackcomms/bash/*
ln -sf   rpiupspackcomms/usr/local/share/rpiupspackcomms/bash/rpiupspackcomms.sh rpiupspackcomms/usr/local/bin/

cat << EOF > rpiupspackcomms/DEBIAN/control
Package: rpiupspackcomms
Version: $OURVER
Depends: python3, python3-serial
Section: custom
Priority: optional
Architecture: all
Essential: no
Installed-Size: 1024
Maintainer: Thomas Blackshaw <thomas.blackshaw@protonmail.com>
Description: Communications for RPi UPSPack, sold at https://www.makerfocus.com/products/raspberry-pi-expansion-board-ups-pack-standard-power-supply
EOF

dpkg-deb --build rpiupspackcomms

mv rpiupspackcomms.deb rpiupspackcomms-"$OURVER"_all.deb
 
