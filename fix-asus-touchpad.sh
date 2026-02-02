#!/bin/bash
# Remove o driver problemático e carrega o modo estável
sudo modprobe -r psmouse
sudo modprobe psmouse proto=imps
echo "Touchpad resetado para modo estável!"
