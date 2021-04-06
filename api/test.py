from pprint import pprint
import aiohttp
import asyncio
import logging
import base64
import json


ADDR = "localhost"
PORT = 3500
URL = f"http://{ADDR}:{PORT}/eth/v1alpha1/validator/block"


def handle_str(value: str):
    if value.startswith("0x"):
        v = value[2:]
        b = bytes.fromhex(v)
        e = base64.b64encode(b)
        # we decode raw byte-string into normal string of bytes, because python's json can't handle raw bytes.
        assert str(e) == f"b'{e.decode()}'"
        return e.decode()
    else:
        raise NotImplementedError(f"String handle: unexpected string '{value}'.")


def base64encode(obj):
    # On the first pass we expect dict
    for key in obj:
        item = obj[key]
        if isinstance(item, str):
            obj[key] = handle_str(item)
        elif isinstance(item, int):
            obj[key] = str(item)
        elif isinstance(item, list):
            for index in range(len(item)):
                list_item = item[index]
                if isinstance(list_item, str):
                    item[index] = handle_str(list_item)
                elif isinstance(list_item, int):
                    obj[key] = str(list_item)
                elif isinstance(list_item, dict):
                    # Recutsive case if dictionary
                    base64encode(list_item)
                else:
                    raise NotImplementedError(f"List loop: object '{list_item}' of type '{type(list_item)}'.")
        elif isinstance(item, dict):
            # Recutsive case if dictionary
            base64encode(item)
        else:
            raise NotImplementedError(f"General loop: object '{item}' of type '{type(item)}'.")


with open("data/block.json") as f:
    block = json.load(f)
    base64encode(block)
    # pprint(block)
    # with open("data/block_base64.json", "w+") as t:
    #     json.dump(block, t, indent=4)
    # exit(1)


async def make_request(index, session):
    # Issue: properly base64 encoded bytes data still breaks everything
    # and causes 'gRPC panic':
    #     'error': 'runtime error: invalid memory address or nil pointer dereference'
    async with session.post(URL, json=block, timeout=20) as resp:
        d = await resp.json()
        logging.debug("Request #%s: %s", index, d)
    return True


async def main():
    # index = 0
    # while 1:
        async with aiohttp.ClientSession(headers={"Content-Type": "application/json"}) as session:
            res = await asyncio.gather( *(make_request(i, session) for i in range(1)) )

        # logging.info("Loop %3s done!", index)
        # index += 1


if __name__ == "__main__":
    # Logging setup
    logging.basicConfig(format="%(asctime)s\t%(levelname)s:\t%(message)s")
    logger = logging.getLogger()
    level = logging.DEBUG
    logger.setLevel(level)

    asyncio.run(main())
