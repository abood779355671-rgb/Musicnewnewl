#!/bin/bash

echo ">> INSTALLING REQUIREMENTS..."
pip3 install -U -r requirements.txt

echo ">> STARTING MUSIC PLAYER..."
python3 main.py
