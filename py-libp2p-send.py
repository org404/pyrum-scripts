import argparse

import multiaddr
import trio

from libp2p import new_host
from libp2p.crypto.secp256k1 import create_new_key_pair
from libp2p.network.stream.net_stream_interface import INetStream
from libp2p.peer.peerinfo import info_from_p2p_addr
from libp2p.typing import TProtocol

PROTOCOL_ID = TProtocol("/meshsub/1.1.0")


async def run(port: int, destination: str, seed: int = None) -> None:
    listen_addr = multiaddr.Multiaddr(f"/ip4/0.0.0.0/tcp/{port}")

    if seed:
        import random

        random.seed(seed)
        secret_number = random.getrandbits(32 * 8)
        secret = secret_number.to_bytes(length=32, byteorder="big")
    else:
        import secrets

        secret = secrets.token_bytes(32)

    host = new_host(key_pair=create_new_key_pair(secret))
    async with host.run(listen_addrs=[listen_addr]):

        print(f"I am {host.get_id().to_string()}")

        maddr = multiaddr.Multiaddr(destination)
        info = info_from_p2p_addr(maddr)
        # Associate the peer with local ip address
        await host.connect(info)

        # Start a stream with the destination.
        # Multiaddress of the destination peer is fetched from the peerstore using 'peerId'.
        stream = await host.new_stream(info.peer_id, [PROTOCOL_ID])

        msg = b"hi, there!\n"

        await stream.write(msg)
        # Notify the other side about EOF
        await stream.close()
        response = await stream.read()

        print(f"Sent: {msg}")
        print(f"Got: {response}")


def main() -> None:
    description = """
    This program demonstrates a simple echo protocol where a peer listens for
    connections and copies back any input received on a stream.
    To use it, first run 'python ./echo -p <PORT>', where <PORT> is the port number.
    Then, run another host with 'python ./chat -p <ANOTHER_PORT> -d <DESTINATION>',
    where <DESTINATION> is the multiaddress of the previous listener host.
    """
    example_maddr = (
        "/ip4/127.0.0.1/tcp/8000/p2p/QmQn4SwGkDZKkUEpBRBvTmheQycxAHJUNmVEnjA2v1qe8Q"
    )
    parser = argparse.ArgumentParser(description=description)
    parser.add_argument(
        "-p", "--port", default=33333, type=int, help="source port number"
    )
    parser.add_argument(
        "-d",
        "--destination",
	default="/ip4/172.31.20.107/tcp/13000/p2p/16Uiu2HAm2zw4bWPboDzFZqwKmsXoVbYozWWkxU5onqxaxGTjsxXJ",
        type=str,
        help=f"destination multiaddr string, e.g. {example_maddr}",
    )
    parser.add_argument(
        "-s",
        "--seed",
        type=int,
        help="provide a seed to the random number generator (e.g. to fix peer IDs across runs)",
    )
    args = parser.parse_args()

    if not args.port:
        raise RuntimeError("was not able to determine a local port")

    try:
        trio.run(run, args.port, args.destination, args.seed)
    except KeyboardInterrupt:
        pass


if __name__ == "__main__":
    main()
