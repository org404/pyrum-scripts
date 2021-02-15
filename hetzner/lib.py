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


async def aexp(p, text: str, timeout: int = 300):
    return await p.expect(text, async_=True, timeout=timeout)


async def cmd(p, command: str, expect: str = "~.*?#"):
    # [DEBUG] print(f">>> {command}")
    p.sendline(command)
    await aexp(p, expect)
    # [DEBUG] out(p)


async def do_assert(p, item, context):
    await cmd(p, item["command"])

    if "contains" in item:
        if item["contains"] not in p.before.decode():
            raise Exception(
                "[Server #{index}] Assertion Error: command output didn't contain \"{contains}\"".format(
                    **context, contains=item["contains"],
                )
            )


