#!/bin/bash

for i in {2..5}
do
    scp ringo.py mloo3@networklab$i.cc.gatech.edu:~/ringo.py
done
