# Those are pyrum instance IP and ID
export P2P_PUBLIC_IP=$(curl -s4 ifconfig.io)
export TADDRESS="/ip4/3.121.110.243/tcp/13000/p2p/16Uiu2HAm2zw4bWPboDzFZqwKmsXoVbYozWWkxU5onqxaxGTjsxXJ"
export TID="16Uiu2HAm2zw4bWPboDzFZqwKmsXoVbYozWWkxU5onqxaxGTjsxXJ"
# ./rumor shell --level debug

# export P2P_PUBLIC_IP=$(curl -s4 ifconfig.io)
# export TADDRESS="/ip4/0.0.0.0/tcp/9001/p2p/16Uiu2HAmL6ZyE81ABAX9qLcgt1LHSunD5633b1oaQKNpkd1nPmEu"
# export TID="16Uiu2HAmL6ZyE81ABAX9qLcgt1LHSunD5633b1oaQKNpkd1nPmEu"

#
# To set this I've used modified version of synced node
# and just encoded and printed correct fork digest.
#
export FORK_DIGEST="0x3b088795"
export FORK_DIGEST_NO_PREFIX=${FORK_DIGEST#"0x"}
# General info
echo -e "$P2P_PUBLIC_IP - $TADDRESS - $TID - $FORK_DIGEST - $FORK_DIGEST_NO_PREFIX"
# ./rumor file test.rumor
./rumor shell --level debug
