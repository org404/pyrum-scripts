import trio
from pyrum import WebsocketConn, TCPConn, UnixConn, SubprocessConn, Rumor, Call

# from remerkleable.complex import Container
# from remerkleable.byte_arrays import Bytes32, Bytes4
# from remerkleable.basic import uint64

import random
import string
import sys


# Use command line to set target
ADDRESS = sys.argv[1]
# ADDRESS = "/ip4/0.0.0.0/tcp/9000/p2p/16Uiu2HAmJfkg3gZdggHPFmfB6tsDjqKcYVrLhSvifPq9LrvwEnKG"
AMOUNT_OF_PEERS = 10


def generator_names(n: int = None, names: list = None):
    if names:
        for name in names:
            yield name
    elif n > 0:
        for each in range(n):
            # generating names like: a, b, c ... z, aa, ab ... zz, aaa ...   etc
            name = ""
            for n_chars in range((each // len(string.ascii_lowercase)) + 1):
                name += string.ascii_lowercase[each % len(string.ascii_lowercase)]
            yield name


async def basic_rpc_example(rumor: Rumor, addr: str, n_peers: int):
    actors = []
    for i, name in enumerate(generator_names(n_peers)):
        print(f"working on actor-#{i} - {name}")
        actor = rumor.actor(name)
        await actor.host.start()
        # Flags are keyword arguments
        await actor.host.listen(tcp=33000 + i)
        print(f"started actor-#{i}")
        actor_addr = await actor.host.view().addr()
        print(f"actor-#{i} host addr: {actor_addr}")
        await actor.peer.connect(addr)
        print(f"connected actor-#{i}!")

    exit(0)


async def run_example(addr: str, n_peers: int):
    # Optionally specify your own rumor executable, for local development/modding of Rumor
    async with SubprocessConn(cmd='/rumor bare --level=trace') as conn:
        # A Trio nursery hosts all the async tasks of the Rumor instance.
        async with trio.open_nursery() as nursery:
            # And optionally use Rumor(conn, nursery, debug=True) to be super verbose about Rumor communication.
            await basic_rpc_example(Rumor(conn, nursery, debug=True), addr, n_peers)


trio.run(run_example, ADDRESS, AMOUNT_OF_PEERS)
