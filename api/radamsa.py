from collections import namedtuple, Counter
from tempfile import mkdtemp
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

DEBUG = bool(os.environ.get("DEBUG", 0))

ADDR = "localhost"
PORT = 3500
BASE_URL   = f"http://{ADDR}:{PORT}/eth/v1alpha1"
VOYEUR_URL = f"https://{NAME}:{PASS}@voyeur.catdrew.dev/api/v1/entries"
# You can use values like 1000 and 100 (accordingly) here and it will remain decently fast.
AMOUNT = 50
INFINITE = bool(os.environ.get("INFINITE", 0))
LOOPS = float("inf" if INFINITE else 50)
TMP_FN = "fuzz-%s"

#
# Note:
#     By default radamsa uses /dev/urandom, so range is from 0x00 to 0xFF. But it
#     seems like radamsa will happily accept any range. So we are generating
#     those values ourselves with 'random' module, and later using the seed.
#     If we really want we can also just call /dev/urandom from here via
#     'subprocess' (it's *not* worth it).
#                                                     - andrew, April 7 2021
#
SEED = random.randint(1, 255)

# Convenient struct for result data.
Item = namedtuple("Item", ["code", "index", "error"])
Result = namedtuple("Result", "path, counter")


async def generate_payload(ctx):
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


async def make_request(index, session, method, ctx):
    payload = await read_payload(index, ctx)

    if method == "POST":
        async with session.post(ctx["url"], data=payload, timeout=20) as resp:
            if resp.status == 200:
                d = {"status": 200}
            else:
                d = await resp.json()

        # Too much...
        #logging.debug("Request #%s, seed %s, data: %s ...", index, ctx["seed"], d)

        # We should not send this data (for continuous fuzzing it's too large), instead, we just store the seed.
        #d["payload"] = payload

    elif method == "GET":
        # Eh, python.. We need this hack to put fuzzer output from bytes into the url.
        try:
            payload = str(payload)[2:-1]
        except Exception as e:
            logging.debug("Decoding fuzzer output error: %s ...", e)
            payload = 0

        async with session.get(ctx["url"].format(generated=payload), timeout=20) as resp:
            if resp.status == 200:
                d = {"status": 200}
            else:
                d = await resp.json()

        # Too much...
        #logging.debug("Request #%s, seed %s, data: %s ...", index, ctx["seed"], d)
        #d["payload"] = payload

    else:
        raise ValueError(f"Bad method: {method}")

    # Store seed that was used to generate request payload.
    d["seed"] = ctx["seed"]
    # Note:
    #     Here we store both relative and absolute indecies. Relative
    #     index is required to re-generate payload from seed. Absolute
    #     index is just an additional metainfo, which could help with
    #     statistical analysis, or it can just stripped later - as we
    #     do below.
    #                                                  - andrew, May 6 2021
    d["relative_index"] = index
    d["absolute_index"] = ctx["base_index"] + index
    return d


async def fuzzing_routine(method: str, base_url: str, url_path: str, source_path: str, seed: int, n_loops: int, n_requests: int):
    url = base_url + url_path

    analitics = list()
    logging.info("Generated random seed: %s ...", seed)
    index = 0
    while index < n_loops:
        logging.info("Used seed: %s ...", seed)
        context = {
            "base_index": index * n_requests,
            "seed": seed,
            "source": source_path,
            "url": url,
            "amount": n_requests,
            "tmp_folder": mkdtemp(),
            "tmp_fn": TMP_FN,
            "failed_to_create": 0,
        }
        try:
            payload = await generate_payload(context)
            seed += 1

            start_t = time.time()
            async with aiohttp.ClientSession() as session:
                res = await asyncio.gather( *(make_request(index=i, session=session, method=method, ctx=context) for i in range(n_requests)))
        finally:
            shutil.rmtree(context["tmp_folder"])

        delta = time.time() - start_t
        logging.info(
            f"Loop %{len(str(AMOUNT))}s done! Ran %s requests (at rate %.2f/second). Created files: %s/%s ...",
            index, len(res), round(len(res) / delta, 2), n_requests - context["failed_to_create"], n_requests,
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
        array_to_send = list()
        for i in range(len(res)):
            item = res[i]

            # First, we skip requests that have status 200. At least for now, it's much easier to ignore successful ones to work with errors only.
            if item.get("status") == 200:
                continue

            # Then, we delete useless/empty data before sending it.
            assert item["details"] != ""
            del item["details"]  # always empty

            del item["absolute_index"]  # at this point indexing is not very useful

            # Repeating messages is pointless and just takes storing space.
            if item["message"] == item["error"]:  item["error"]   = True
            # Now we encode this whole data as base64 to be sent over.
            if item.get("payload"):               item["payload"] = base64.b64encode(item["payload"]).decode()

            # Saving modified object.
            array_to_send.append(item)
            # We cannot do this during 
            if DEBUG:  analitics.append(item)

        # Here we are actually sending data to voyeur.
        async with aiohttp.ClientSession(headers={"Content-Type": "application/json", "X-Namespace": "radamsa fuzzing"}) as session:
            # Sending the whole list (you can alternatively send one by one).
            async with session.post(VOYEUR_URL, json = array_to_send, timeout = 5) as resp:
                r = await resp.json()
                logging.info("Sent %s entries to voyeur, status: %s ...", len(array_to_send), r["code"])

    # In the end just group all results by error type and show count.
    if DEBUG:
        counter = Counter(a["message"] for a in analitics)
        return Result(url_path, counter)


async def main():
    reqs = await asyncio.gather(
        # Fuzzing validator endpoints that expect POST request.
        fuzzing_routine("POST", BASE_URL, "/validator/block",            "data/block.json", SEED, LOOPS, AMOUNT),
        fuzzing_routine("POST", BASE_URL, "/validator/attestation",      "data/block.json", SEED, LOOPS, AMOUNT),
        fuzzing_routine("POST", BASE_URL, "/validator/aggregate",        "data/block.json", SEED, LOOPS, AMOUNT),
        fuzzing_routine("POST", BASE_URL, "/validator/exit",             "data/block.json", SEED, LOOPS, AMOUNT),
        fuzzing_routine("POST", BASE_URL, "/validator/subnet/subscribe", "data/block.json", SEED, LOOPS, AMOUNT),

        # Fuzzing validator endpoints that expect GET request.
        fuzzing_routine("GET", BASE_URL, "/validator/block?slot={generated}",              "data/slot.json", SEED, LOOPS, AMOUNT),  # slot is a number
        fuzzing_routine("GET", BASE_URL, "/validators/activesetchanges?epoch={generated}", "data/slot.json", SEED, LOOPS, AMOUNT),  # epoch is a number
        fuzzing_routine("GET", BASE_URL, "/validators/assignments?epoch={generated}",      "data/slot.json", SEED, LOOPS, AMOUNT),  # epoch is a number
        fuzzing_routine("GET", BASE_URL, "/validators/participation?epoch={generated}",    "data/slot.json", SEED, LOOPS, AMOUNT),  # epoch is a number

        # Documentation for this endpoint says:
        #     // Retrieve attestations by block root, slot, or epoch.
        # ..but no idea how to retrieve by block root or by slot. Tried:
        #     "root", "block_root", "blockroot", "slot", "block_slot", "blockslot"
        fuzzing_routine("GET", BASE_URL, "/beacon/attestations?epoch={generated}", "data/slot.json", SEED, LOOPS, AMOUNT),  # epoch is a number

        # Documentation for this endpoint says:
        #     // Retrieve attestations by block root, slot, or epoch.
        # ..but no idea how to retrieve by block root or by slot. Tried:
        #     "root", "block_root", "blockroot", "slot", "block_slot", "blockslot"
        fuzzing_routine("GET", BASE_URL, "/beacon/attestations/indexed?epoch={generated}", "data/slot.json", SEED, LOOPS, AMOUNT),  # epoch is a number

        # Fuzzing beacon node endpoints that expect GET request.
        fuzzing_routine("GET", BASE_URL, "/beacon/blocks?slot={generated}",  "data/slot.json", SEED, LOOPS, AMOUNT),  # slot is a number
        fuzzing_routine("GET", BASE_URL, "/beacon/blocks?epoch={generated}", "data/slot.json", SEED, LOOPS, AMOUNT),  # epoch is a number
        fuzzing_routine("GET", BASE_URL, "/beacon/blocks?root={generated}",  "data/slot.json", SEED, LOOPS, AMOUNT),  # root is a base64 encoded

        # No data here
        # fuzzing_routine("GET", BASE_URL, "/beacon/chainhead",                    "data/slot.json", SEED, LOOPS, AMOUNT),
        # fuzzing_routine("GET", BASE_URL, "/beacon/weak_subjectivity_checkpoint", "data/slot.json", SEED, LOOPS, AMOUNT),

        # Fuzzing beacon node endpoints that expect GET request.
        fuzzing_routine("GET", BASE_URL, "/beacon/committees?epoch={generated}",       "data/slot.json", SEED, LOOPS, AMOUNT),  # epoch is a number
        fuzzing_routine("GET", BASE_URL, "/beacon/individual_votes?epoch={generated}", "data/slot.json", SEED, LOOPS, AMOUNT),  # epoch is a number
    )

    if DEBUG:
        for data in reqs:
            print("~" * 40)
            print(f"Result for {data.path}:\n")
            print(*data.counter.most_common(50), sep="\n")


if __name__ == "__main__":
    # Logging setup.
    logging.basicConfig(format="%(asctime)s\t%(levelname)s:\t%(message)s")
    logger = logging.getLogger()
    level = logging.INFO if not DEBUG else logging.DEBUG
    logger.setLevel(level)

    asyncio.run(main())

