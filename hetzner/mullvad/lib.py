from typing import Generator, Tuple, Dict


__all__ = (
    "commands",
    "assertions",
)


# By the default we expect bash return, otherwise if tuple is provided,
# second argument will be an expected output string
COMMANDS = (
    "apt-get update && apt-get install -qq -y curl jq openresolv wireguard",
    "curl -LO https://mullvad.net/media/files/mullvad-wg.sh",
    "chmod +x ./mullvad-wg.sh",
    # Here we expect to be asked for account number,
    # which is the only authentication value
    ("./mullvad-wg.sh", "Mullvad account number:"),
    # This is an important part, here you have to input account number
    "{MULLVAD_ID}",

    # We can predefine which countries/servers we want
    # Examples:
    #   - "export NEW_WG=mullvad-gb19",
    #   - "export NEW_WG={MULLVAD_SERVER}",

    # We can just randomly choose from all config files
    "export NEW_WG=$(ls /etc/wireguard/ | shuf -n 1 | sed 's/\(.*\)\..*/\1/')",
    "wg-quick up $NEW_WG",
    "systemctl enable wg-quick@$NEW_WG",
)


ASSERTIONS = (
    ("wg", "interface: "),
)


def commands(**kwargs) -> Generator[Tuple[str, str], None, None]:
    for item in COMMANDS:
        if isinstance(item, str):
            yield item.format(**kwargs), None
        elif isinstance(item, tuple):
            cmd, expect = item
            yield cmd.format(**kwargs), expect
        else:
            raise NotImplementedError(f"Argument {item} is not supported!")


def assertions(**kwargs) -> Generator[Dict[str, str], None, None]:
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

    for cmd, expect in commands(**ctx):
        print(expect if expect else "~#", end=" ")
        print(cmd)
    print(f"{'-' * 16}\nDoing assertions:\n{'-' * 16}")
    for i, item in enumerate(assertions(**ctx)):
        print(f"Assertion #{i}")
        print("cmd:\t\t", item["command"])
        if item["contains"]: print("contains:\t", item["contains"])

