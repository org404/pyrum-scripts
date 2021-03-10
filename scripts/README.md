### How to run
##### 1. Install Rumor
You can follow installation instructions in the `rumor` submodule, but in my case it didn't work so I just built it:
```shell
# inside rumor repo
go build .
cp rumor ../scripts/
```

##### 2. Configure script
Open `test.sh` and set your target's correct address and id.

##### 3. Run Script
You can run prepared setup that will create a peer and try to connect to your target and make `status` and `block-by-root` requests.  
For that simply do:
`./test.sh`
  
If you want to open shell, you can uncomment last line in `test.sh` instead.
Then inside the shell write `include test.rumor`, it will be imported and executed immediatelly.
