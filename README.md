# Description
This example let's you spin up listening rumor server (extremely light - 26MB) with p2p protocol and dv5 support. In this example we will open rumor shell, load our attack script, creating one attack client and establishing/keeping connection to hardcoded target (our test instance).

### Pre-requirements
Must have:  
* docker  
* docker-compose  
* golang 1.4

### Setup
Clone repo and initialize submodules:  
```
git clone git@github.com:org404/pyrum-scripts.git
# initialize
git submodule update --init --recursive
```

### Further instructions
Refer to readme for [rumor scripts](./scripts/) (**simple**) or [obtrusive](./obtrusive/) (**requires hetzner token**).
