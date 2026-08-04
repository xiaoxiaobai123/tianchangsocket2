#!/bin/bash

# Backup the original file
cp /etc/network/interfaces /etc/network/interfaces.bak

# Define the new configuration
CONFIG='
# interfaces(5) file used by ifup(8) and ifdown(8)
# Include files from /etc/network/interfaces.d:
source-directory /etc/network/interfaces.d
auto eth2
iface eth2 inet static
address 192.168.3.50
netmask 255.255.255.0
auto eth1
iface eth1 inet static
address 192.168.2.50
netmask 255.255.255.0
auto eth0
iface eth0 inet static
address 192.168.1.50
netmask 255.255.255.0
gateway 192.168.1.1
broadcast 192.168.1.255
'

# Update the interfaces file
echo "$CONFIG" > /etc/network/interfaces

# Restart the networking service using the provided command
sudo /etc/init.d/networking restart

