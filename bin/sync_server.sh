#!/bin/bash

CURRDIR=`dirname "$0"`
BASEDIR=`cd "$CURRDIR"; pwd`


NAME="Report Server"
CMD="$BASEDIR"/../lib/report_server_main.py


if [ "$1" = "-d" ]; then
    shift
    EXECUTEDIR=$1'/'
    shift
else
    EXECUTEDIR=$(cd $BASEDIR'/../'; pwd)
fi

if [ "$2" = "-s" ]; then
    shift
    SERVER_TYPE=$2
    shift
else
    SERVER_TYPE=syncing
fi

if [ ! -d "$EXECUTEDIR" ]; then
    echo "ERROR: $EXECUTEDIR is not a dir"
    exit
fi

if [ ! -d "$EXECUTEDIR"/conf ]; then
    echo "ERROR: could not find $EXECUTEDIR/conf/"
    exit
fi

if [ ! -d "$EXECUTEDIR"/logs ]; then
    mkdir "$EXECUTEDIR"/logs
fi

cd "$EXECUTEDIR"


start() {
    PID=$(ps aux | grep "report_server_main.py" | grep "$SERVER_TYPE" | awk '{ print $2}')
    if [ ! -n "$PID" ];then
        "$CMD" -d "$EXECUTEDIR" -s "$SERVER_TYPE" >> /dev/null 2>&1 &
        echo "$SERVER_TYPE" is running!
    else
        echo "$SERVER_TYPE is running as $PID, we'll do nothing"
     fi
}

stop() {
    PID=$(ps aux | grep "report_server_main.py" | grep "$SERVER_TYPE" | awk '{ print $2}')
    if [ ! -n "$PID" ];then
        echo "$SERVER_TYPE" is not running!
    else
        kill -9 $PID
        echo "$SERVER_TYPE" is stop!
     fi
}


RETVAL=0
case "$1" in
    start)
        start
        ;;  
    stop)
        stop
        ;;
    *)  
    echo "Usage: $0 {start|stop|restart|status|reload}"
    RETVAL=1
esac
exit $RETVAL


