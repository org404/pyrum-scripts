sudo iptables -I OUTPUT 1 -m owner --gid-owner prysm-beaconchain -j DROP
