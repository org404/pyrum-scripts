# Fuzzing validator POST requests.
./run_radamsa.sh test morphysm POST data/block.json /validator/block
./run_radamsa.sh test morphysm POST data/block.json /validator/attestation
./run_radamsa.sh test morphysm POST data/block.json /validator/aggregate
./run_radamsa.sh test morphysm POST data/block.json /validator/exit
./run_radamsa.sh test morphysm POST data/block.json /validator/subnet/subscribe

# Fuzzing validator GET requests.
./run_radamsa.sh test morphysm GET  data/slot.json  /validator/block?slot={generated}
./run_radamsa.sh test morphysm GET  data/slot.json  /validators/activesetchanges?epoch={generated}
./run_radamsa.sh test morphysm GET  data/slot.json  /validators/assignments?epoch={generated}
./run_radamsa.sh test morphysm GET  data/slot.json  /validators/participation?epoch={generated}

# Fuzzing beacon node GET requests.
./run_radamsa.sh test morphysm GET  data/slot.json  /beacon/blocks?slot={generated}
./run_radamsa.sh test morphysm GET  data/slot.json  /beacon/blocks?epoch={generated}
./run_radamsa.sh test morphysm GET  data/slot.json  /beacon/blocks?root={generated}
./run_radamsa.sh test morphysm GET  data/slot.json  /beacon/attestations?epoch={generated}
./run_radamsa.sh test morphysm GET  data/slot.json  /beacon/attestations/indexed?epoch={generated}
./run_radamsa.sh test morphysm GET  data/slot.json  /beacon/committees?epoch={generated}
./run_radamsa.sh test morphysm GET  data/slot.json  /beacon/individual_votes?epoch={generated}

