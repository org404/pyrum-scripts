# Description
This example let's you spin up listening rumor server (extremely light - 26MB) with p2p protocol and dv5 support. In this example it will be our "attack" target.  
After that you can spin up another container (using rumor as well) with simple script `connect.py`, that creates 10 clients and establishes connection to given address.  

### Pre-requirements
Must have:  
* docker  
* docker-compose  

### Running example
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

### Errors
TODO

