#!/bin/bash
echo "--- Resolvendo problema do Mouse Fantasma ---"
sudo modprobe -r i2c_hid_acpi
sudo modprobe i2c_hid_acpi
echo "Touchpad reiniciado com sucesso!"
