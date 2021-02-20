from hcloud.server_types.domain import ServerType
from hcloud.images.domain import Image
import asyncio
import string
import random
import yaml
import sys


class Runner:
    # A hack to sync writing
    NEEDS_NEW_LINE = False
    # Global indecies for config arrays
    INDECIES = {}

    def __init__(self, tunnel, context: dict):
        self.p = tunnel
        self.context = context
        self.loop = asyncio.get_event_loop()

    async def send(self, text: str):
        resp = await self.loop.run_in_executor(None, self.p.sendline, text)

    @staticmethod
    def gen_passwd():
        characters = string.ascii_letters + string.digits
        return "".join(random.choice(characters) for x in range(24))

    @staticmethod
    def read_config(path: str = None):
        if not path: path = "config.yml"
        with open(path) as conf:
            config = yaml.load(conf, Loader=yaml.FullLoader)
        return config

    def parse_config(self):
        config = self.read_config()

        commands = list()
        for item in config["commands"]:
            if isinstance(item, str):
                commands.append({
                    "command": item.format(
                        **self.context
                    ),
                    "show": False,
                    "period": 1,
                    "expect": None,
                })
            elif isinstance(item, dict):
                show = item.pop("show") if "show" in item else False
                period = item.pop("period") if "period" in item else 1
                expect = item.pop("expect") if "expect" in item else None
                if "use" in item:
                    use = item["use"]
                    if use not in config.get("vars", []):
                        raise ValueError(f"Couldn't find '{use}' in vars!")
                    if use not in self.INDECIES:
                        self.INDECIES[use] = 0
                        it = config["vars"][use][0]
                    else:
                        self.INDECIES[use] += 1
                        it = config["vars"][use][self.INDECIES[use]]
                else:
                    it = None

                commands.append({
                    "command": item["command"].format(
                        **self.context, **item, it=it,
                    ),
                    "show": show,
                    "period": period,
                    "expect": expect,
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
                        **self.context
                    ),
                    show: False,
                    period: 1,
                    contains: False,
                })
            elif isinstance(item, dict):
                show = item.pop("show") if "show" in item else False
                period = item.pop("period") if "period" in item else 1
                contains = item.pop("contains") if "contains" in item else False

                assertions.append({
                    "command": item["command"].format(
                        **self.context, **item,
                    ),
                    "show": show,
                    "period": period,
                    "contains": contains,
                })
            else:
                raise NotImplementedError(
                    f"Unparsable config type: {type(item)}.\n"
                    f"Value: {item}."
                )

        return commands, assertions

    def sys_p(self, text: str, new_line: bool = False, prefix: str = "..."):
        # We can't do this inline
        text = text.strip(" \n")
        index = self.context["index"]
        if not prefix:
            prefix = ""
        else:
            prefix = prefix + " "

        if new_line:
            text = f"[Server #{index}] {prefix}{text}\r"
            if self.NEEDS_NEW_LINE:
                self.NEEDS_NEW_LINE = False
                text = "\n" + text
            print(text)
        else:
            sys.stdout.write(f"\r[Server #{index}] {prefix}{text}\033[K")
            sys.stdout.flush()
            self.NEEDS_NEW_LINE = True

    def out(self):
        lines = []
        for l in self.p.before.decode().split("\n"):
            l = l.strip(" \n\r")
            if l:
                lines.append(l)
        # First line is our command
        command = lines.pop(0)
        # The last line is shell prompt
        for line in lines[:-1]:
            self.sys_p(line, new_line = True)

    async def aexp(self, text: str, timeout: int = 1800):  # set timeout to a large value, default timeout is supposed to be -1 (infinite), but in reality it errors in a couple of minutes
        return await self.p.expect(text, async_=True, timeout=timeout)

    async def cmd(self, command: str, expect: str = "~.*?#", show_command: bool = True):
        if show_command:
            # print commands
            self.sys_p(command, prefix = "~#:")
        # Run actual command
        await self.send(command)
        await self.aexp(expect)

    async def do_assert(self, item):
        await self.cmd(item["command"], show_command = False)

        if item["contains"]:
            if item["contains"] not in self.p.before.decode():
                index = self.context["index"]
                raise Exception(
                    "[Server #{index}] Assertion Error: command output didn't contain \"{contains}\"".format(
                        **self.context, contains=item["contains"],
                    )
                )

    @staticmethod
    def _create_server(client, stype, image, index):
        response = client.servers.create(
            name        = f"manifold-venom-{index}",
            server_type = ServerType(name=stype),
            image       = Image(name=image),
        )
        print(f"[Server #{index}] Created the server with ID {response.server.id}  ({stype}, {image}).")
        print(f"[Server #{index}] IPv4: {response.server.public_net.ipv4.ip}. IPv6: {response.server.public_net.ipv6.ip}.")
        print(f"[Server #{index}] Root password: {response.root_password}.")

        actions = list()
        if response.action:       actions.append(response.action)
        if response.next_actions: actions.extend(response.next_actions)

        print(f"[Server #{index}] Awaiting {len(actions)} (initialization) actions ...")
        for a in actions:
            a.wait_until_finished()
        print(f"[Server #{index}] Spinning up ...")
        return response

    @classmethod
    async def create_server(cls, client, stype, image, index):
        loop = asyncio.get_event_loop()
        resp = await loop.run_in_executor(None, cls._create_server, client, stype, image, index)
        return resp
