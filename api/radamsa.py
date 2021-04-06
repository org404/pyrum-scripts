import subprocess
import aiohttp
import asyncio
import logging
import json


ADDR = "localhost"
PORT = 3500
URL  = f"http://{ADDR}:{PORT}/eth/v1alpha1/validator/block"
SOURCE_FILE = "data/block.json"

all_data = list()

async def make_request(index, session):
    command = f"cat {SOURCE_FILE} | radamsa"
    proc = await asyncio.create_subprocess_shell(
        command,
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE,
    )
    out, err = await proc.communicate()

    async with session.post(URL, data=out, timeout=20) as resp:
        d = await resp.json()

    logging.debug("Request #%s: %s", index, d)
    d["request_data"] = f'"{out}"'
    all_data.append(d)
    return True


async def main():
    index = 0
    while index < 10:
        async with aiohttp.ClientSession() as session:
            res = await asyncio.gather( *(make_request(i, session) for i in range(500)) )

        logging.info("Loop %4s done!", index)
        index += 1

    with open("data/output.json", "w+") as f:
        json.dump(all_data, f, indent=4)


if __name__ == "__main__":
    # Logging setup
    logging.basicConfig(format="%(asctime)s\t%(levelname)s:\t%(message)s")
    logger = logging.getLogger()
    level = logging.INFO
    logger.setLevel(level)

    asyncio.run(main())

