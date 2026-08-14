#!/bin/bash
echo "========================================"
echo "  GameMaster - PUBG Controller"
echo "  Installing dependencies..."
echo "========================================"
pip3 install -r requirements.txt
echo "Starting GameMaster..."
python3 main.py
