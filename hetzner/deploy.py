import subprocess
import pexpect
import sys


NEW_PASS = "jfsans12985vh21nj4v"


def cmd(p, command: str):
    print(f">>> {command}")
    p.sendline(command)
    p.expect(".+?~#")


def deploy(ip, username, root_pass):
    print(f"Connecting to the instance {ip} ...")
    p = pexpect.spawn(f"ssh -tt {username}@{ip}")
    # AUTHENTICATION block
    p.expect(".*yes/no/.*")
    p.sendline("yes")  # accept ip
    p.expect("'s password")
    p.sendline(root_pass)  # log in
    p.expect("urrent pass")
    p.sendline(root_pass)  # change pass
    p.expect("New password:")
    # We are doing this everywhere! @securiti
    p.sendline(NEW_PASS)  # change pass
    p.expect("new password:")
    p.sendline(NEW_PASS)  # change pass

    # ACTUAL COMMANDS
    # This commands will be executed. Current commands serve only testing purpose.
    commands = [
        "touch test.txt",
        "ls",
    ]

    # want_output = False
    for c in commands:
        cmd(p, c)

