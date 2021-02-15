from typing import Generator, Tuple, Dict


__all__ = (
    "run_mullvad",
    "assertions",
    "INSTALL_MULLVAD",
    "RUN_MULLVAD",
)


# By the default we expect bash return, otherwise if tuple is provided,
# second argument will be an expected output string
INSTALL_MULLVAD = (
    "apt-get update && apt-get install -qq -y curl jq openresolv wireguard",
    "curl -LO https://mullvad.net/media/files/mullvad-wg.sh",
    "chmod +x ./mullvad-wg.sh",
    # Here we expect to be asked for account number,
    # which is the only authentication value
    ("./mullvad-wg.sh", "Mullvad account number:"),
    # This is an important part, here you have to input account number
    "{MULLVAD_ID}",
)


RUN_MULLVAD = (
    # We can predefine which countries/servers we want
    # Examples:
    #   - "export NEW_WG=mullvad-gb19",
    #   - "export NEW_WG={MULLVAD_SERVER}",

    # We can just randomly choose from all config files
    "export NEW_WG=$(ls /etc/wireguard/ | shuf -n 1 | sed 's/\(.*\)\..*/\1/')",
    "wg-quick up $NEW_WG",
    "systemctl enable wg-quick@$NEW_WG",
)


COMMANDS = INSTALL_MULLVAD + RUN_MULLVAD


ASSERTIONS = (
    ("wg", "interface: "),
)


def run_mullvad(commands: tuple = COMMANDS, **kwargs) -> Generator[Tuple[str, str], None, None]:
    for item in commands:
        if isinstance(item, str):
            yield item.format(**kwargs), None
        elif isinstance(item, tuple):
            cmd, expect = item
            yield cmd.format(**kwargs), expect
        else:
            raise NotImplementedError(f"Argument {item} is not supported!")


def mullvad_assertions(**kwargs) -> Generator[Dict[str, str], None, None]:
    for item in ASSERTIONS:
        if isinstance(item, str):
            yield {
                "command": item.format(**kwargs),
                "contains": None
            }
        elif isinstance(item, tuple):
            cmd, expect = item
            yield {
                "command": cmd.format(**kwargs),
                "contains": expect
            }
        else:
            raise NotImplementedError(f"Argument {item} is not supported!")


if __name__ == "__main__":
    ctx = {"a": 1, "MULLVAD_ID": "1111222233334444"}

    for cmd, expect in run_mullvad(commands=INSTALL_MULLVAD,**ctx):
        print(">>>", cmd)
        print("<<<", expect if expect else "Awaiting for shell ...")
    print(f"{'-' * 16}\nDoing assertions:\n{'-' * 16}")
    for i, item in enumerate(mullvad_assertions(**ctx)):
        print(f"Assertion #{i}")
        print("cmd:\t\t", item["command"])
        if item["contains"]: print("contains:\t", item["contains"])

