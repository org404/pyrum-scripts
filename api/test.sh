PORT=3500
ADDR=localhost
#ADDR=3.121.110.243
TEST_ID="16Uiu2HAkxuYmv2jZTCvvrvVkByPsGgTGRScKT15cvogf1qRbWoDd"

# Valid get requests:
#curl -w "\n" -sX GET -H "accept: application/json" http://$ADDR:$PORT/eth/v1alpha1/validator/block?slot=959547 | json_pp
#curl -w "\n" -sX GET -H "accept: application/json" http://$ADDR:$PORT/eth/v1alpha1/validator/attestation?slot=959544 | json_pp

# Trying to post a block:

# Requests below trigger
#     "error" : "invalid character 'd' looking for beginning of value"
#
#curl -w "\n" -sX POST -d @data/block.ssz -H "accept: application/json" http://$ADDR:$PORT/eth/v1alpha1/validator/block | json_pp
#curl -w "\n" -sX POST --data-binary @data/block.ssz -H "accept: application/json" http://$ADDR:$PORT/eth/v1alpha1/validator/block | json_pp

# Request below triggers
#     'bazel-prysm/external/go_sdk/src/encoding/base64/base64.go:	return "illegal base64 data at input byte " + strconv.FormatInt(int64(e), 10)'
#
#curl -w "\n" -sX POST -d @data/block.json -H "accept: application/json" http://$ADDR:$PORT/eth/v1alpha1/validator/block | json_pp

#curl -w "\n" -sX POST -d @data/block2.json -H "accept: application/json" http://$ADDR:$PORT/eth/v1alpha1/validator/block | json_pp

#curl -w "\n" -sX POST -d @data/block2.json -H "accept: application/json" http://$ADDR:$PORT/eth/v1alpha1/beacon/attestations/pool
curl -w "\n" -s -H "accept: application/json" http://$ADDR:$PORT/eth/v1alpha1/beacon/attestations/pool | json_pp

