# Those are pyrum instance IP and ID
export P2P_PUBLIC_IP=$(curl -s4 ifconfig.io)
export TADDRESS="/ip4/3.121.110.243/tcp/13000/p2p/16Uiu2HAm2zw4bWPboDzFZqwKmsXoVbYozWWkxU5onqxaxGTjsxXJ"
export TID="16Uiu2HAm2zw4bWPboDzFZqwKmsXoVbYozWWkxU5onqxaxGTjsxXJ"
# ./rumor shell --level debug

# export P2P_PUBLIC_IP=$(curl -s4 ifconfig.io)
# export TADDRESS="/ip4/0.0.0.0/tcp/9001/p2p/16Uiu2HAmL6ZyE81ABAX9qLcgt1LHSunD5633b1oaQKNpkd1nPmEu"
# export TID="16Uiu2HAmL6ZyE81ABAX9qLcgt1LHSunD5633b1oaQKNpkd1nPmEu"
echo -e "$P2P_PUBLIC_IP - $TADDRESS - $TID"
# ./rumor file test.rumor
./rumor shell --level debug
