import aiohttp
import asyncio
import logging


ADDR = "localhost"
PORT = 3500
URL = f"http://{ADDR}:{PORT}/eth/v1alpha1/validator/block"


async def make_request(index, session):
    # So there is a bug(?) in current API that causes error below (no client crash):
    #
    # Error:
    #     level=error msg="gRPC panicked!" error="runtime error: invalid memory address or nil pointer dereference"
    #
    # It is triggered **only** when body of the request is empty(!), otherwise even if json
    # payload is an empty string ('""') it is handled correctly and responds with normal
    # error, without causing issues in the client. However if the body is empty we get that
    # error and client spits a huge stack trace in the logs. Interestingly, this leads to
    # much higher load on the node, compared to properly handled error!
    #
    # This doesn't cause any issues:
    #     async with session.post(URL, json="", timeout=20) as resp:
    #
    # But this does:
    async with session.post(URL, data="", timeout=20) as resp:
        d = await resp.json()
        logging.debug("Request #%s: %s", index, d)
        return True


async def main():
    index = 0
    while 1:
        async with aiohttp.ClientSession() as session:
            res = await asyncio.gather( *(make_request(i, session) for i in range(100)) )  # Causes 200%+ load, which is half of the resources on this machine. Memory unaffected.
            # res = await asyncio.gather( *(make_request(i, session) for i in range(1000)))  # Causes 250-300% load, which is most of the resources on this machine. Memory unaffected.
            # res = await asyncio.gather( *(make_request(i, session) for i in range(5000)))  # Causes jumps to max cpu load. Memory unaffected.

        # logging.info("Loop %4s.\trequests succeed: %s/%s.", index, sum(res), len(res))
        logging.info("Loop %4s done!", index)
        index += 1


if __name__ == "__main__":
    # Logging setup
    logging.basicConfig(format="%(asctime)s\t%(levelname)s:\t%(message)s")
    logger = logging.getLogger()
    level = logging.INFO
    logger.setLevel(level)

    asyncio.run(main())
