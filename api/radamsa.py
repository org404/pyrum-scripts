from collections import namedtuple, Counter
from pprint import pprint
import aiofiles
import aiohttp
import asyncio
import logging
import base64
import random
import shutil
import ujson
import time
import uuid
import os


NAME, PASS = os.environ.get("NAME"), os.environ.get("PASS")
if not NAME:
    raise ValueError("You must specify basic auth name for voyeur (env 'NAME')!")
if not PASS:
    raise ValueError("You must specify basic auth password for voyeur (env 'PASS')!")


SOURCE_FILE = "data/block.json"
ADDR = "localhost"
PORT = 3500
URL  = f"http://{ADDR}:{PORT}/eth/v1alpha1/validator/block"
VOYEUR_URL = f"https://{NAME}:{PASS}@voyeur.catdrew.dev/api/v1/entries"
# You can use values like 1000 and 100 (accordingly) here and it will remain decently fast.
AMOUNT = 100
LOOPS  = 10
TMP_FOLDER = "/tmp/tmp-{folder}"
TMP_FN = "fuzz-%s"

#
# Note:
#     By default it's /dev/urandom, so range is from 0x00 to 0xFF. But it
#     seems like radamsa happily accepts any range. So we are generating
#     those values ourselves with 'random' module, and later using the seed.
#     If we really want we can also just call /dev/urandom from here via
#     'subprocess' (it's *not* worth it).
#                                                     - andrew, April 7 2021
#
SEED = random.randint(1, 255)

# Convenient struct for result data.
Item = namedtuple("Item", ["code", "index", "error"])


async def generate_payload(ctx):
    os.makedirs(ctx["tmp_folder"])
    tmp_fp  = os.path.join(ctx["tmp_folder"], ctx["tmp_fn"] % "%n")
    command = f"cat {ctx['source']} | radamsa --seed {ctx['seed']} -n {ctx['amount']} -o {tmp_fp}"
    logging.debug("Using command: '%s'", command)
    proc = await asyncio.create_subprocess_shell(
        command,
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE,
    )
    try:
        out, err = await asyncio.wait_for(proc.communicate(), timeout=30)
    except asyncio.TimeoutError:
        logging.error(
            "Something is wrong.. Radamsa hanged.. There are few "
            "issues that might cause this. For example, making "
            "sure that path to the sample data for the input data "
            "is correct or that output directories exist."
        )
        exit(1)


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
            index, len(res), round(len(res) / delta, 2), AMOUNT - context["failed_to_create"], AMOUNT,
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
        # Current solution:
        #     We are using this script as a show-case for voyeur, the service
        #     which can be used for logs visualization and analysis.
        #
        for i in range(len(res)):
            item = res[i]
            # First, we delete useless/empty data before sending it.
            del item["details"]  # always empty
            del item["real_index"]  # at this point indexing is useless
            # Repeating messages is kind of pointless.
            if item["message"] == item["error"]:
                item["error"] = True
            # Now we encode this whole data as base64 to be sent over.
            item["request"] = base64.b64encode(item["request"]).decode()
            # Saving modified object.
            res[i] = item
        # Here we are actually sending data to voyeur.
        async with aiohttp.ClientSession(headers={"Content-Type": "application/json", "X-Namespace": "radamsa fuzzing"}) as session:
            # Sending the whole list (you can alternatively send one by one).
            async with session.post(VOYEUR_URL, json=res, timeout=5) as resp:
                r = await resp.json()
                logging.info("Sent %s entries to voyeur, status: %s ...", len(res), r["code"])

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

