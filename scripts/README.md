### Instructions
In this example we will open rumor shell, load our attack script, creating one attack client and establishing/keeping connection to hardcoded target (our test instance).

### How to run
##### 1. Prepare Rumor Docker
Simply go into rumor submodule and run the build script.
```shell
# open rumor submodule
cd ../rumor
# build app inside rumor repo
./build.sh
# go back to this dir
cd ../scripts
```

##### 2. Configure script
Open `test.sh` and set your target's correct address and id.  
By default connects to our test instance.

##### 3. Run Script
To open rumor shell, run `test.sh`.  
Then inside the shell write `include test.rumor`, it will be imported and executed immediatelly.  
If you are overwhelmed by the logs, try setting lower value in the `test.sh`.

#### TODO
You can run prepared setup that will create a peer and try to connect to your target and make `status` and `block-by-root` requests.  
For that simply do:
`./test.sh`
  
