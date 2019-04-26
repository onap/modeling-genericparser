#!/bin/bash

cd /service/modeling/genericparser

./run.sh

while [ ! -f logs/runtime_genericparser.log ]; do
    sleep 1
done
tail -F logs/runtime_genericparser.log
