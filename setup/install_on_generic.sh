#!/bin/bash
#
#
# install on generic (non-systemd) GNU/Linux OS

die() {
    echo "$1" >> /dev/stderr
    exit 1
}


install_me() {
    [ -e "/usr/share/rpiupspackcomms" ] && mv /usr/share/rpiupspackcomms /usr/share/rpiupspackcomms.$RANDOM$RANDOM
    mkdir -p /usr/share/rpiupspackcomms
    cp -af * /usr/share/rpiupspackcomms/
    chmod +x /usr/share/rpiupspackcomms/bash/*
    ln -sf   /usr/share/rpiupspackcomms/bash/rpiupspackcomms.sh /usr/bin/   
}


tweak_rclocal() {
    noof_lines_in_rc_local=$(wc -l /etc/rc.local | cut -d' ' -f1)
    lino_of_exit0=$(grep -n "exit 0" /etc/rc.local | tail -n1 | cut -d':' -f1)
    [ "$noof_lines_in_rc_local" != "" ] || die "Unable to figure out the number of lines in /etc/rc.local"
    if [ "$lino_of_exit0" == "" ] || [ "$(($noof_lines_in_rc_local-$lino_of_exit0))" -gt "8" ] ; then
        echo "exit 0" >> /etc/rc.local
        lino_of_exit0=$(grep -n "exit 0" /etc/rc.local | tail -n1 | cut -d':' -f1)
    fi
    [ -e "/etc/.rc.local.before-rpiupspackcomms" ] && cp -f /etc/.rc.local.before-rpiupspackcomms /etc/rc.local
    cp -f /etc/rc.local /etc/.rc.local.before-rpiupspackcomms
    head -n$(($lino_of_exit0-1)) /etc/.rc.local.before-rpiupspackcomms> /etc/rc.local
    cat << EOF >> /etc/rc.local
while true; do bash /usr/bin/rpiupspackcomms.sh; sleep 5; done
exit 0
EOF
}



install_me
tweak_rclocal

