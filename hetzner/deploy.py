import pexpect
import asyncio
import string
import random
import yaml


def gen_passwd():
    characters = string.ascii_letters + string.digits
    return "".join(random.choice(characters) for x in range(24))


def read_config(path: str = None):
    if not path: path = "config.yml"

    with open(path) as conf:
        config = yaml.load(conf, Loader=yaml.FullLoader)

    return config


def parse_config(context: dict = {}):
    config = read_config()

    commands = list()
    for item in config["commands"]:
        if isinstance(item, str):
            commands.append({
                "command": item.format(
                    **context
                ),
                "show": False,
            })
        elif isinstance(item, dict):
            show = item.pop("show") if "show" in item else False

            commands.append({
                "command": item["command"].format(
                    **context, **item,
                ),
                "show": show,
            })
        else:
            raise NotImplementedError(
                f"Unparsable config type: {type(item)}.\n"
                f"Value: {item}."
            )

    assertions = list()
    for item in config["assertions"]:
        if isinstance(item, str):
            assertions.append({
                "command": item.format(
                    **context
                ),
            })
        elif isinstance(item, dict):
            show = item.pop("show") if "show" in item else False
            contains = item.pop("contains") if "contains" in item else False

            assertions.append({
                "command": item["command"].format(
                    **context, **item,
                ),
                "show": show,
                "contains": contains,
            })
        else:
            raise NotImplementedError(
                f"Unparsable config type: {type(item)}.\n"
                f"Value: {item}."
            )

    return commands, assertions


async def do_assert(p, item, context):
    await cmd(p, item["command"])

    if "contains" in item:
        if item["contains"] not in p.before.decode():
            raise Exception(
                "[Server #{index}] Assertion Error: command output didn't contain \"{contains}\"".format(
                    **context, contains=item["contains"],
                )
            )


async def aexp(p, text: str, timeout: int = 300):
    return await p.expect(text, async_=True, timeout=timeout)


async def cmd(p, command: str):
    # [DEBUG] print(f">>> {command}")
    p.sendline(command)
    await aexp(p, "~.*?#")
    # [DEBUG] out(p)


def out(p):
    lines = []
    for l in p.before.decode().split("\n"):
        l = l.strip(" \n\r")
        if l:
            lines.append(l)
    # First line is our command
    command = lines.pop(0)
    # TODO: do we really want this?: print(f">>> {command}")
    # The last line is shell prompt
    for line in lines[:-1]:
         print(line)


async def deploy(index, ip: str, username: str, root_pass: str):
    print(f"[Server #{index}] Connecting to the instance {ip} ...")
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

    commands, assertions = parse_config(context)
    # This commands will be executed.
    for item in commands:
        await cmd(p, item["command"])
        if item["show"]: out(p)
    # Running assertions
    for item in assertions:
        await do_assert(p, item, context)
        if item["show"]: out(p)

    # Report about assertion-tests if there were any
    if assertions:
        print(f"[Server #{index}]: successfully ran {len(assertions)} assertions!")


async def start(coros: list, sleep_for: int):
    print(f"Sleeping for {sleep_for} seconds ...")
    await asyncio.sleep(sleep_for)
    return await asyncio.gather(*coros)

