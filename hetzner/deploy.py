from mullvad.lib import run_mullvad, mullvad_assertions
from lib import Runner
import pexpect
import asyncio


CONF = Runner.read_config()
CONFIG = CONF["general"]


async def deploy(index, ip: str, username: str, root_pass: str):
    print(f"[Server #{index}] Connecting to the instance {username}@{ip} ...")
    p = pexpect.spawn(f"ssh -tt -o UserKnownHostsFile=/dev/null {username}@{ip}")
    context = {
        "index": index,
        "mullvad": CONFIG.get("mullvad", {}).get("account"),
    }
    r = Runner(p, context)
    # AUTHENTICATION block
    await r.aexp(".*yes/no/.*")
    await r.send("yes")  # accept ip
    await r.aexp("'s password")
    await r.send(root_pass)  # log in
    await r.aexp("urrent pass")
    await r.send(root_pass)  # change pass
    # Here we generate and show new password
    new_passwd = r.gen_passwd()
    print(f"[Server #{index}] Changed password to {new_passwd} ...")
    await r.aexp("New password:")
    await r.send(new_passwd)  # change pass
    await r.aexp("new password:")
    await r.send(new_passwd)  # confirm pass

    # If mullvad vpn is configured, we install/launch it first
    if context["mullvad"]:
        # TODO: Test this, this probably will drop connection when launching vpn
        for item in run_mullvad(**context):
            await r.cmd(*item)
        for item in mullvad_assertions(**context):
            await r.do_assert(item)

    commands, assertions = r.parse_config()
    # This commands will be executed.
    # bool_true = 1
    for item in commands:
        if item["expect"]:
            await r.cmd(item["command"], expect=item["expect"])
        else:
            await r.cmd(item["command"])

        # if bool_true:
        #     bool_true -= 1
        #     await asyncio.sleep(30)

        if item["show"]: r.out()

    # Running assertions
    for item in assertions:
        await r.do_assert(item)
        if item["show"]: r.out()

    # Report about assertion-tests if there were any
    if assertions:
        r.sys_p(f"Successfully ran {len(assertions)} assertions!", new_line = True, prefix = None)


async def start(server_tasks: list, sleep_for: int, user: str):
    resp_list = await asyncio.gather(*server_tasks)
    print("----------------------------------------------")
    print(f"[Global] Sleeping for {sleep_for} seconds ...")
    await asyncio.sleep(sleep_for)
    # Draw line after sleep to make current action very clear
    print("----------------------------------------------")
    coros = [deploy(i, r.server.public_net.ipv4.ip, user, r.root_password) for i, r in enumerate(resp_list)]
    return await asyncio.gather(*coros)

