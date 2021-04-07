
#
# Warning:
#    This eats all the resources very quickly, and since the node
#    never crashes, your whole system might become unresponsive.
#    Make sure you have access to hardware killswitch to reboot
#    the machine!
#                                               - andrew, April 7 2021
#
ADDR=localhost
PORT=3500

seq 1 500 | xargs -I $ -n1 -P50  curl -sX GET -H "accept: application/json" http://$ADDR:$PORT/eth/v1alpha1/debug/state?slot=99999

