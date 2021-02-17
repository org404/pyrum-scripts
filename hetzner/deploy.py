from lib import read_config, parse_config, gen_passwd, aexp, cmd, do_assert
from mullvad.lib import run_mullvad, mullvad_assertions
from tqdm import tqdm
import pexpect
import asyncio


CONF = read_config()
CONFIG = CONF["general"]


async def deploy(index, ip: str, username: str, root_pass: str):
    print(f"[Server #{index}] Connecting to the instance {username}@{ip} ...")
    p = pexpect.spawn(f"ssh -tt -o UserKnownHostsFile=/dev/null {username}@{ip}")
    # AUTHENTICATION block
    await aexp(p, ".*yes/no/.*")
    p.sendline("yes")  # accept ip
    await aexp(p, "'s password")
    p.sendline(root_pass)  # log in
    await aexp(p, "urrent pass")
    p.sendline(root_pass)  # change pass
    new_passwd = gen_passwd()
    print(f"[Server #{index}] Changed password to {new_passwd} ...")
    await aexp(p, "New password:")
    p.sendline(new_passwd)  # change pass
    await aexp(p, "new password:")
    p.sendline(new_passwd)  # change pass

    context = {
        "index": index,
    }

    # If mullvad vpn is configured, we install/launch it first
    mullvad = CONFIG.get("mullvad")
    if mullvad:
        # TODO: Test this, this probably will drop connection when launching vpn
        context["account"] = mullvad["account"]
        for item in run_mullvad(**context):
            await cmd(p, *item)
        for item in mullvad_assertions(**context):
            await do_assert(p, item, context)

    commands, assertions = parse_config(context)
    # This commands will be executed.
    for item in tqdm(commands):
        await cmd(p, item["command"])
        if item["show"]: out(p)
    # Running assertions
    for item in tqdm(assertions):
        await do_assert(p, item, context)
        if item["show"]: out(p)

    # Report about assertion-tests if there were any
    if assertions:
        print(f"[Server #{index}]: successfully ran {len(assertions)} assertions!")


async def start(coros: list, sleep_for: int):
    print(f"Sleeping for {sleep_for} seconds ...")
    await asyncio.sleep(sleep_for)
    return await asyncio.gather(*coros)

