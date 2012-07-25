#!/bin/sh
PORT=43001
DBDIR=$PWD/db
MONGOD="mongod \
        --dbpath=$DBDIR \
        --fork \
        --logpath $DBDIR/mongod.log \
        --noauth \
        --nojournal \
        --noprealloc \
        --nounixsocket \
        --pidfilepath=$DBDIR/mongod.pid \
        --port $PORT \
        --smallfiles \
        --syncdelay 300"

if [ -d "$DBDIR" ]; then
    echo "db directory exists. Already running?"
    exit $?
elif [[ $# -ne 1 ]]; then
    echo "Need an env: coverage-better.sh env323"
    exit $?
else
    echo "creating db directory $DBDIR"
    mkdir $DBDIR
    echo "Starting mongod"
    $MONGOD
    PID=`cat $DBDIR/mongod.pid`
    echo "mongod started with pid: $PID"
    echo "starting tests"
    TEST_MONGODB=localhost:$PORT ./$1/bin/coverage run setup.py test && ./$1/bin/coverage report -m --omit=*env*,*/tests/*,setup.py
    echo "killing mongod at: $PID"
    kill -9 $PID
    echo "removing $DBDIR"
    rm -rf $DBDIR
fi



