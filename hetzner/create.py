from hcloud.server_types.domain import ServerType
from deploy import deploy, start, read_config
from hcloud.images.domain import Image
from hcloud import Client
import asyncio
import yaml
import sys
import os

CONF = read_config()
CONFIG = CONF["general"]

if not CONFIG.get("token"):
    print("Please, run this script with (Hetzner) \"token\" variable in config.yml!\nMore in the Authentication section - https://docs.hetzner.cloud/#authentication.")
    exit(1)

# Create a client
client = Client(token=CONFIG["token"])

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
    if not CONFIG.get("servers"):
        print(f"You didn't set \"servers\" var for amount of servers to create, exiting!")
        exit(1)
    else:
        N = int(CONFIG["servers"])
        print(f"Deploying {N} servers according to config.yml ...")
        print("---------------")

    tasks = list()
    for index in range(N):
        response = client.servers.create(
            name        = f"manifold-venom-{index}",
            server_type = ServerType(name=TYPE),
            image       = Image(name=IMAGE),
        )
        print(f"Created server #{index} of ID {response.server.id}  ({TYPE}, {IMAGE}).")
        print(f"Server's IPv4: {response.server.public_net.ipv4.ip}. Server's IPv6: {response.server.public_net.ipv6.ip}.")
        print(f"Root password for the server: {response.root_password}.")

        actions = list()
        if response.action:       actions.append(response.action)
        if response.next_actions: actions.extend(response.next_actions)

        print(f"Awaiting {len(actions)} (initialization) actions ...")
        for i, a in enumerate(actions):
            a.wait_until_finished()
        print(f"Server status: {response.server.status} ... ")
        print("---------------")
        # Running deployment
        tasks.append(deploy(
            index,
            response.server.public_net.ipv4.ip,
            USER,
            response.root_password,
        ))

    asyncio.run(start(tasks, SLEEP_PERIOD))
    print("---------------")
    print("Done!")

