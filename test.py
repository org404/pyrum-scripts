import trio
from pyrum import WebsocketConn, TCPConn, UnixConn, SubprocessConn, Rumor, Call

from remerkleable.complex import Container
from remerkleable.byte_arrays import Bytes32, Bytes4
from remerkleable.basic import uint64


class StatusReq(Container):
    version: Bytes4
    finalized_root: Bytes32
    finalized_epoch: uint64
    head_root: Bytes32
    head_slot: uint64

"""
async def basic_rpc_example(rumor: Rumor):
    alice = rumor.actor('alice')
    await alice.host.start()
    # Flags are keyword arguments
    await alice.host.listen(tcp=9000)
    print("started alice")
    addr = await alice.host.view().addr()
    print(f"alice host addr: {addr}")
    pubk = addr.split("/")[-1]
    await alice.peer.connect(f"/ip4/172.31.7.38/tcp/9000/p2p/{pubk}")
    print("connected alice!")
"""

async def basic_rpc_example(rumor: Rumor):
    alice = rumor.actor('alice')
    await alice.host.start()
    # Flags are keyword arguments
    await alice.host.listen(tcp=9000)
    print("started alice")

    # Concurrency in Rumor, planned with async (Trio) in Pyrum
    bob = rumor.actor('bob')
    await bob.host.start()
    await bob.host.listen(tcp=9001)
    print("started bob")

    long_call = alice.sleep('5s')  # sleep 5 seconds
    print('made long call')
    short_call = alice.sleep('3s')  # sleep 3 seconds
    print('made short call')

    await short_call
    print("done with short call")
    await long_call
    print('done with long call')

    # Getting a result should be as easy as calling, and waiting for the key we are after
    bob_addr = await bob.host.view().addr()
    print('BOB has address: ', bob_addr)

    # Command arguments are just call arguments
    await alice.peer.connect(bob_addr)
    print("connected alice to bob!")

    # You can use either await or async-for to get data of a specific key
    async for addr in bob.host.view().addr():
        print(f'bob has addr: {addr}')  # multiple addresses, but the last one matters most.

    # Optionally request more peer details
    peerdata = await alice.peer.list(details=True).peers()
    print(f'alice peer list: {peerdata}')

    print("Testing a Status RPC exchange")

    alice_peer_id = await alice.host.view().peer_id()

    alice_status = StatusReq(head_slot=42)
    bob_status = StatusReq(head_slot=123)

    async def alice_work(nursery: trio.Nursery) -> Call:
        print("alice: listening for status requests")
        call = alice.rpc.status.listen(raw=True)
        # Wait for inital completion of setup, i.e. the listener is online.
        # It will stay open in the background, until `await call.finished()`
        await call

        async def process_requests():
            # Each req object is a dict with all the latest log data at the time of completion of the step.
            async for req in call:
                print(f"alice: Got request: {req}")
                assert 'input_err' not in req
                # Or send back an error; await alice.rpc.status.resp.invalid_request(req['req_id'], f"hello! Your request was invalid, because: {req['input_err']}")
                assert req['data'] == bob_status.encode_bytes().hex()
                resp = alice_status.encode_bytes().hex()
                print(f"alice: sending response back to request {req['req_id']}: {resp}")
                await alice.rpc.status.resp.chunk.raw(req['req_id'], resp, done=True)
            print("alice: stopped listening for status requests")

        nursery.start_soon(process_requests)

        return call

    async def bob_work():
        # Send alice a status request
        req = bob_status.encode_bytes().hex()
        print(f"bob: sending alice ({alice_peer_id}) a status request: {req}")
        req_call = bob.rpc.status.req.raw(alice_peer_id, req, raw=True)
        await req_call
        # Await request to be written to stream
        await req_call.next()
        # Await first (and only) response chunk
        resp = await req_call.next()

        print(f"bob: received status response from alice: {resp}")
        assert resp['chunk_index'] == 0  # first chunk
        assert resp['result_code'] == 0  # success chunk
        assert resp['data'] == alice_status.encode_bytes().hex()

    # Run tasks in a trio nursery to make them concurrent
    async with trio.open_nursery() as nursery:
        # Set up alice to listen for requests
        alice_listen_call = await alice_work(nursery)

        # Make bob send a request and check a response, after alice is set up
        await bob_work()

        # Close listener of alice
        await alice_listen_call.cancel()


async def run_example():
# Optionally specify your own rumor executable, for local development/modding of Rumor
    async with SubprocessConn(cmd='cd rumor && go run . bare --level=trace') as conn:
        # A Trio nursery hosts all the async tasks of the Rumor instance.
        async with trio.open_nursery() as nursery:
            # And optionally use Rumor(conn, nursery, debug=True) to be super verbose about Rumor communication.
            await basic_rpc_example(Rumor(conn, nursery, debug=True))

trio.run(run_example)
