from hcloud.server_types.domain import ServerType
from hcloud.images.domain import Image
from hcloud import Client
from deploy import deploy
import socket
import time
import sys
import os

if not os.environ.get("TOKEN"):
    print("Please, run this script with (Hetzner) TOKEN env variable!\nMore in the Authentication section - https://docs.hetzner.cloud/#authentication.")
    exit(1)

# Create a client
client = Client(token=os.environ["TOKEN"])

# Servers:
# Taken from https://www.hetzner.com/cloud
# Interesting options:
CX11 = "cx11"  # 2.96  €/m - 0.005 €/h - 1vCPU - 2GB RAM  - 20GB storage  - 20TB network cap - the cheapest option, could run any scripts
CX21 = "cx21"  # 5.83  €/m - 0.010 €/h - 2vCPU - 4GB RAM  - 40GB storage  - 20TB network cap - medium, could probably run stripped client
CX31 = "cx31"  # 10.59 €/m - 0.017 €/h - 2vCPU - 8GB RAM  - 80GB storage  - 20TB network cap - minimum specs by the Prysm team for full pledged client
CX41 = "cx41"  # 18.92 €/m - 0.031 €/h - 4vCPU - 16GB RAM - 160GB storage - 20TB network cap - recommended specs by the Prysm team for full pledged client

# In practise, it looks like CX41 would be enough to run 5 attacker nodes even if they will need to sync.
# Running more nodes (if we somehow configure ipv6 traffic), for example 10 becomes very questionable due
# to RAM and storage contraint (CPUs probably can handle this, though the sync will probably take up to
# 2-3 times as long due to being overloaded and increased waste due to context switching between many
# threads). So the worst case scenario (running full node) price for one victim (30 connections) will be
# 6 instances of 5 nodes each, rounding up to about 0.2 €/h (taking into account fees). Thankfully,
# network limits on hetzner are huge so we don't need to worry about that ever despite anything we do.

# This actual type will be used in the code below
TYPE = CX11

# OS name for the server images
IMAGE = "ubuntu-20.04"

# Sleep to let server finish initialization
SLEEP_PERIOD = 30
USER = "root"


# To delete servers use `-d` or `--delete` keywords
if len(sys.argv) > 1 and (sys.argv[1] == "-d" or sys.argv[1] == "--delete"):
    servers = client.servers.get_all()
    command = input(f"Servers to delete - {len(servers)}. Do you confirm? [y/N] ")
    if command.lower() != "y":
        print("Didn't recieve confirmation, exiting ...")
        exit(1)

    for server in servers:
        print(f"Deleting server of ID {server.id} with name {server.name}.")
        server.delete()
        print(f"Deleted server with ID {server.id}!")
else:
    # Number of servers to create.
    if not os.environ.get("N"):
        print(f"You didn't pass N env var for amount of servers to create, exiting!")
        exit(1)
    else:
        N = int(os.environ["N"])
        print(f"Deploying with {N} amount of servers according to N env var ...")
        print("---------------")

    for index in range(N):
        response = client.servers.create(
            name        = f"manifold-venom-{index}",
            server_type = ServerType(name=TYPE),
            image       = Image(name=IMAGE),
        )
        print(f"Created server #{index} of ID {response.server.id}  ({TYPE}, {IMAGE}).")
        print(f"Server's IPv4: {response.server.public_net.ipv4.ip}. Server's IPv6: {response.server.public_net.ipv6.ip}.")
        print(f"Root password for the server: {response.root_password}.")
        print("---------------")
        actions = list()
        if response.action:
            actions.append(response.action)
        if response.next_actions:
            actions.extend(response.next_actions)

        print(f"Awaiting {len(actions)} actions ...")
        for i, a in enumerate(actions):
            print(f"Waiting for action #{i} - status: {a.status} ...")
            a.wait_until_finished()
            print(f"Action #{i} complete! (status: {a.status})")
        print(f"Server status: {response.server.status} ... ")
        print(f"Sleeping for {SLEEP_PERIOD} seconds ...")
        time.sleep(SLEEP_PERIOD)
        # Running deployment
        deploy(response.server.public_net.ipv4.ip, USER, response.root_password)

