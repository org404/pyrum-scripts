from collections import namedtuple, Counter
import aiofiles
import aiohttp
import asyncio
import logging
import random
import shutil
import json
import time
import uuid
import os


SOURCE_FILE = "data/test.json"
ADDR = "localhost"
PORT = 3500
URL  = f"http://{ADDR}:{PORT}/eth/v1alpha1/validator/block"
# You can use values like 1000 and 100 (accordingly) here and it will remain decently fast.
AMOUNT = 50
LOOPS  = 10
TMP_FOLDER = "/tmp/tmp-{folder}"
TMP_FN = "fuzz-%s"

#
# Note:
#     By default it's /dev/urandom, so range is from 0x00 to 0xFF. So
#     we are generating those values ourselves with 'random' module,
#     and later using the seed. If we really want we can also just call
#     /dev/urandom from here via 'subprocess'.
#                                                     - andrew, April 7 2021
#
SEED = random.randint(1, 256)

# Convenient struct for result data.
Item = namedtuple("Item", ["code", "index", "error"])


async def generate_payload(ctx):
    os.makedirs(ctx["tmp_folder"])
    tmp_fp  = os.path.join(ctx["tmp_folder"], ctx["tmp_fn"] % "%n")
    command = f"cat {ctx['source']} | radamsa --seed {ctx['seed']} -n {ctx['amount']} -o {tmp_fp}"

    proc = await asyncio.create_subprocess_shell(
        command,
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE,
    )
    out, err = await proc.communicate()


async def read_payload(index, ctx):
    tmp_fp = os.path.join(ctx["tmp_folder"], ctx["tmp_fn"] % str(index + 1))
    try:
        async with aiofiles.open(tmp_fp, "rb") as f:
            return await f.read()
    # Note:
    #     For some unknown to me reason "radamsa" just refuses to
    #     output files sometimes. And other times it outputs some
    #     percentage of them, so we log it, and show general stat
    #     with .INFO level, because we really don't want it to
    #     fail silently.
    #                                           - andrew, April 7 2021
    except FileNotFoundError:
        logging.debug("Failed to read file for request #%s, using default value ...", index + 1)
        ctx["failed_to_create"] += 1
        return b""


async def make_request(index, session, ctx):
    request = await read_payload(index, ctx)

    async with session.post(ctx["url"], data=request, timeout=20) as resp:
        d = await resp.json()

    logging.debug("Request #%s: %s ...", index, d)
    d["request"] = request
    d["real_index"] = ctx["base_index"] + index
    return d


async def main():
    analitics = list()
    seed  = SEED
    logging.info("Generated random seed: %s ...", SEED)
    index = 0
    while index < LOOPS:
        logging.info("Used seed: %s ...", seed)
        context = {
            "base_index": index * AMOUNT,
            "seed": seed,
            "source": SOURCE_FILE,
            "url": URL,
            "amount": AMOUNT,
            "tmp_folder": TMP_FOLDER.format(folder=uuid.uuid4()),
            "tmp_fn": TMP_FN,
            "failed_to_create": 0,
        }
        try:
            payload = await generate_payload(context)
            seed += 1

            start_t = time.time()
            async with aiohttp.ClientSession() as session:
                res = await asyncio.gather( *(make_request(index=i, session=session, ctx=context) for i in range(AMOUNT)))
        finally:
            shutil.rmtree(context["tmp_folder"])

        delta = time.time() - start_t
        logging.info(
            f"Loop %{len(str(AMOUNT))}s done! Ran %s requests (at rate %.2f/second). Created files: %s/%s ...",
            index, len(res), round(len(res) / delta, 2), context["failed_to_create"], AMOUNT,
        )
        index += 1

        #
        # Note:
        #     We could save data and then analyze it later, but the problem
        #     is it takes too much memory to store huge amount of requests.
        #     Much better for us to run the script with some seed, so then
        #     we will have an ability to replay the request data, and if we
        #     find something interesting and want to replay it. So for now
        #     just extract errors and prettify the output, as below.
        #                                                  - andrew, April 7 2021
        # Initial idea (too much memory):
        #     with open("data/output.json", "w+") as f:
        #         json.dump(all_data, f, indent=4)
        #
        # Current:
        for item in res:
            error = item["error"]
            # This should be here, because it's a properly handled json parsing
            # response/error, but it always will have unique characters inside
            # it, so it makes the error a hell to analyze.
            if "invalid character" in error:
                error = "Invalid character in the data"

            analitics.append(Item(
                code  = item["code"],
                index = item["real_index"],
                error = error,
            ))

    # In the end just group all results by error type and show count.
    counter = Counter((a.error for a in analitics))
    print(*counter.most_common(20), sep="\n")


if __name__ == "__main__":
    # Logging setup.
    logging.basicConfig(format="%(asctime)s\t%(levelname)s:\t%(message)s")
    logger = logging.getLogger()
    level = logging.INFO
    logger.setLevel(level)

    asyncio.run(main())

