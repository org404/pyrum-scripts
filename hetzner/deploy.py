import subprocess
import pexpect
import asyncio
import sys


NEW_PASS = "jfsans12985vh21nj4v"
REPO_URL = "https://{}github.com/org404/prysm.git"


def make_url(user, passwd):
    if user and passwd: prefix = f"{user}:{passwd}@"
    else:               prefix =  ""
    return REPO_URL.format(prefix)


async def aexp(p, text: str, timeout: int = -1):
    return await p.expect(text, async_=True, timeout=timeout)


async def cmd(p, command: str):
    # [DEBUG] print(f">>> {command}")
    p.sendline(command)
    await aexp(p, "~.*?#", timeout=300)
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


async def deploy(index, ip: str, username: str, root_pass: str, gh_user: str = None, gh_pass: str = None):
    repo_url = make_url(gh_user, gh_pass)

    print(f"Connecting to the instance {ip} ...")
    p = pexpect.spawn(f"ssh -tt {username}@{ip}")
    # AUTHENTICATION block
    await aexp(p, ".*yes/no/.*")
    p.sendline("yes")  # accept ip
    await aexp(p, "'s password")
    p.sendline(root_pass)  # log in
    await aexp(p, "urrent pass")
    p.sendline(root_pass)  # change pass
    await aexp(p, "New password:")
    # We are doing this everywhere! @securiti
    p.sendline(NEW_PASS)  # change pass
    await aexp(p, "new password:")
    p.sendline(NEW_PASS)  # change pass

    # ACTUAL COMMANDS
    # 42 - is a magic number that prints output of the command before it

    # This commands will be executed.
    commands = [
        # Dependencies
        "apt-get update && apt-get upgrade -qq -y && apt-get install -qq -y " \
        "docker.io golang git curl gnupg",
        # Bazel util
        "curl -fsSL https://bazel.build/bazel-release.pub.gpg | gpg --dearmor > bazel.gpg",
        "mv bazel.gpg /etc/apt/trusted.gpg.d/",
        "echo 'deb [arch=amd64] https://storage.googleapis.com/bazel-apt stable jdk1.8' | tee /etc/apt/sources.list.d/bazel.list",
        "apt-get update && apt-get install -qq -y bazel",

        f"git clone {repo_url}",
        "cd prysm",
        "ls",
        # TODO: Running exhaust script
        # TODO: env vars "./exhaust.sh"

        # Print additional information
        f"echo \"Server #{index} " \
        "(ipv4='$(curl -s -4 ifconfig.io)', ipv6='$(curl -s -6 ifconfig.io)') " \
        "finished deployement.\"",
        42,
    ]

    # want_output = False
    for c in commands:
        if c == 42: out(p); continue

        await cmd(p, c)


async def start(coros: list, sleep_for: int):
    print(f"Sleeping for {sleep_for} seconds ...")
    await asyncio.sleep(sleep_for)
    return await asyncio.gather(*coros)
