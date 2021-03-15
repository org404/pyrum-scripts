#
# TODO: This is WIP for actual automated deployment script.
#

# Those are pyrum instance IP and ID
export TADDRESS="/ip4/3.121.110.243/tcp/13000/p2p/16Uiu2HAm2zw4bWPboDzFZqwKmsXoVbYozWWkxU5onqxaxGTjsxXJ"
export TID="16Uiu2HAm2zw4bWPboDzFZqwKmsXoVbYozWWkxU5onqxaxGTjsxXJ"
# Target's fork digest
export FORK_DIGEST="0x3b088795"
export FORK_DIGEST_NO_PREFIX=${FORK_DIGEST#"0x"}
#
# Here we run our attack script as a background process, while
# redirecting stdout into the file. This way we can poll (continuesly
# read) contents of the file for logs and decide, for example, that we
# need to switch ip.
#
# OUTPUT_LOG="OUTPUT_LOG_.log"
# ./rumor file test.rumor --level warn

python3 attack.py

