import trio
from pyrum import WebsocketConn, TCPConn, UnixConn, SubprocessConn, Rumor, Call

from remerkleable.complex import Container
from remerkleable.byte_arrays import Bytes32, Bytes4
from remerkleable.basic import uint64

import itertools
import random
import string
import sys
import os


# Use command line to set target
if len(sys.argv) > 1:
    ADDRESS = sys.argv[1]
else:
    print("No address supplied, trying hardcoded address..")
    ADDRESS = "/ip4/172.31.20.107/tcp/13000/p2p/16Uiu2HAm2zw4bWPboDzFZqwKmsXoVbYozWWkxU5onqxaxGTjsxXJ"
    # ADDRESS = "/ip4/172.31.20.107/tcp/12000/p2p/16Uiu2HAm2zw4bWPboDzFZqwKmsXoVbYozWWkxU5onqxaxGTjsxXJ"
    print(f"ADDRESS: {ADDRESS}")

AMOUNT_OF_PEERS = 100
PATH_TO_RUMOR = os.environ.get("PATH_TO_RUMOR", "./rumor/app")

COLOR = "\n"  # r"\033[0;33m"
END = "\n"  # r"\033[0m"  # No Color
printc = lambda s: print(f"{COLOR}{s}{END}")


class StatusReq(Container):
    version: Bytes4
    finalized_root: Bytes32
    finalized_epoch: uint64
    head_root: Bytes32
    head_slot: uint64


def generator_names(n: int = None, names: list = None):
    if names:
        for name in names:
            yield name
        return
    
    # else case
    i = 0
    for size in itertools.count(1):
        for s in itertools.product(string.ascii_lowercase, repeat=size):
            yield "".join(s)
            i += 1
            # exit if we have certain range (n)
            if n is not None and i >= n: return


async def basic_rpc_example(rumor: Rumor, addr: str, n_peers: int):
    # actors = []
    namegen = generator_names()
    i = 0
    while 1:
        i += 1
        name = next(namegen)
    # for i, name in enumerate(generator_names(n_peers)):
        printc(f"working on actor-#{i} - {name}")
        actor = rumor.actor(name)
        # actors.append(actor)
        await actor.host.start()
        # Flags are keyword arguments
        await actor.host.listen(tcp=33000 + i)
        printc(f"started actor-#{i}")
        actor_addr = await actor.host.view().addr()
        printc(f"actor-#{i} host addr: {actor_addr}")
        # Forcing rumor to move on if hanged
        with trio.move_on_after(0.5):
            target = await actor.peer.connect(addr)
            printc(f"connected actor-#{i}!")
            printc(f"target connection: {target}")
            # Request in hex (some random transaction from the internet)
            # req = b"0xf86b80850ba43b7400825208947917bc33eea648809c285607579c9919fb864f8f8703baf82d03a0008025a0067940651530790861714b2e8fd8b080361d1ada048189000c07a66848afde46a069b041db7c29dbcc6becf42017ca7ac086b12bd53ec8ee494596f790fb6a0a69"
            # req = StatusReq(head_slot=12101240402414214).encode_bytes().hex()
            # Sending data
            # req_call = actor.rpc.status.req.raw(target["peer_id"], req, raw=True)
            # req_resp = await req_call
            # printc(f"req_resp: {req_resp}")
        await trio.sleep(0.1)
    exit(0)


async def run_example(addr: str, n_peers: int):
    # Optionally specify your own rumor executable, for local development/modding of Rumor
    async with SubprocessConn(cmd=f"{PATH_TO_RUMOR} bare --level=trace") as conn:
    # async with SubprocessConn(cmd='/rumor bare --level=trace') as conn:
        # A Trio nursery hosts all the async tasks of the Rumor instance.
        async with trio.open_nursery() as nursery:
            # And optionally use Rumor(conn, nursery, debug=True) to be super verbose about Rumor communication.
            await basic_rpc_example(Rumor(conn, nursery, debug=False), addr, n_peers)


trio.run(run_example, ADDRESS, AMOUNT_OF_PEERS)
