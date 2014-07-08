#!/bin/bash

#
# start process in the background and wait for its readiness notification
# via systemd style NOTIFY_SOCKET
#
daemon_notify() {
    exec=$1
    pidfile=$2
    startuplog=$3
    timeout=$4

    # Requires:
    # uuidgen (util-linux)
    # sleep (coreutils)
    export NOTIFY_SOCKET='@/org/rdoproject/systemd/notify/'$(uuidgen)
    python -m keystone.openstack.common.systemd $timeout &
    pidnotify=$!
    $exec &>$startuplog &
    pid=$!
    while [ -d /proc/$pid -a -d /proc/$pidnotify ]
    do
        sleep 1
    done
    # pick up return codes from either process
    if [ ! -d /proc/$pid ]
    then
        wait $pid
        retval=$?
    else
        retval=-1
    fi
    if [ ! -d /proc/$pidnotify ]
    then
        wait $pidnotify
        retnotify=$?
    else
        retnotify=-1
    fi
    if [ $retnotify -eq 0 ]
    then
        # readiness notification received, all OK
        echo $pid > $pidfile
        return 0
    else
        # readiness not received
        if [ $retval -eq -1 ]
        then
            # process exists in unknown state
            return 1
        else
            # startup failed
            return $retval
        fi
    fi
}

daemon_notify "$@"
exit $?
