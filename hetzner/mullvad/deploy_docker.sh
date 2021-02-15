# script args
NAME=$1
PATH_TO_CONFIG=$2

#
# Few things to note here:
#  - This will run the container which we should be able to use
#    by running desired container with "--network=container:$NAME"
#    option. This is a separate script because we probably want
#    to deploy vpns one by one.
#  - Before running this container, you must install mullvad on
#    the target, because we will need to generate config files and
#    keys. In short, run 'INSTALL_MULLVAD' block of commands
#.
docker run -d \
  --name=$NAME \
  --cap-add=NET_ADMIN \
  --cap-add=SYS_MODULE \
  -e PUID=1000 \
  -e PGID=1000 \
  -e TZ=Europe/London \
  -p 51820:51820/udp \
  -v $PATH_TO_CONFIG:/config \
  -v /lib/modules:/lib/modules \
  --sysctl="net.ipv4.conf.all.src_valid_mark=1" \
  --sysctl="net.ipv6.conf.all.src_valid_mark=1" \
  --restart unless-stopped \
  ghcr.io/linuxserver/wireguard

