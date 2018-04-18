#!/bin/bash

for i in {6..8}
do
    scp ringo.py mloo3@networklab$i.cc.gatech.edu:~/ringo.py
done
