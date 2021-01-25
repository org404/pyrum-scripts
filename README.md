# Description
This example let's you spin up listening rumor server (extremely light - 26MB) with p2p protocol and dv5 support. In this example it will be our "attack" target.  
After that you can spin up another container (using rumor as well) with simple script `connect.py`, that creates 10 clients and establishes connection to given address.  

### Pre-requirements
Must have:  
* docker  
* docker-compose  

**To configure Prysm to accept only local connections, apply `--p2p-allowlist=172.0.0.0/8` flag to your none when launching**

### Setup
For some libraries we need external OS-level dependencies, on ubuntu do:
```
sudo apt-get install gcc libpq-dev python3-dev python3-pip python3-venv python3-wheel -y
```
  
Clone repo and initialize submodules:  
```
git clone git@github.com:org404/pyrum-scripts.git
# initialize
git submodule update --init --recursive
```
  
You might also need python virtualenv. To install it type:
```
sudo apt-get install python3-virtualenv
```
And then create (if do not exist yet) and activate with:
```
# inside the project dir
virtualenv -p python3.8 .venv
source .venv/bin/activate
```
In addition, it is recommended to upgrade pip and utils:
```
python -m pip install -U pip wheel setuptools
```
Note: when you activated virtual env, `python` is an alias for your python3.8 instance. Otherwise (without virtualenv), you will probably need to run `python3`.

### Connecting to Prysm client
Installing deps:
```
python -m pip install -r requirements.txt
```
  
Building rumor:
```
# go into rumor submodule
cd rumor
CGO_ENABLED=1 GOOS=linux go build -ldflags '-extldflags "-w -s"' -o app
# go back to our proj
cd ..
```
  
Now you are ready to connect, to open prysm logs to see whether it's working, type:
```
sudo journalctl -fu prysm-beaconchain
```

Running script to connect to any reachable multiaddr:
```
./connect.sh <address>
```
  
### Running example [Docker]
First, you should spin up a receiving server:
```
./server.sh  
```
After it starts, you will see logs. You need to extract a full address to use later when establishing a connection. It will look something like `"/ip4/0.0.0.0/tcp/9000/p2p/16Uiu2HAmB8GdZXvfaBDtXCk585Wr4mdqgeFn489Gn2D6DraMsgLZ"`. The last part is a peer id, so it will be unique each time.  
Now, if you want to connect from outside (another machine), you need to change the ip (`0.0.0.0` part) in the address to your machine's external ipv4.  
  
Running second container:
```
./connect.sh <address>
```
You should almost immediately see a log, from 10 connected peers (default amount). Make sure you can find "connected to peer" in the log. And no errors. This confirms that you established connection successfully.

### Clean up
Connector container exists automatically on finish, but "server" container is set to run for weeks (with one huuge `sleep 99999m`). This is a friendly reminder to put that container down, when you don't need it.  
For that enter `rumor` directory and run stop command:
```
cd rumor
docker-compose down
```

### Errors
If you can't connect to the peer, make sure that:  
* peer is reachable (it is inside your network)
* make sure peer has enough available slots for connections; 
