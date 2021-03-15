import asyncio
import logging
import json
import os


CONTAINER_NAME = "attack_rumor"
ARGS = (
    "docker", "run", "--rm", "-d",
    "--name", CONTAINER_NAME,
    "-e", f"TADDRESS={os.environ['TADDRESS']}",
    "-e", f"TID={os.environ['TID']}",
    "-e", f"FORK_DIGEST={os.environ['FORK_DIGEST']}",
    "-e", f"FORK_DIGEST_NO_PREFIX={os.environ['FORK_DIGEST_NO_PREFIX']}",
    "-v", "$PWD/test.rumor:/test.rumor:rw",
    # Prepared slot for formatting
    "{vpn}"
    "rumor-custom", "file", "test.rumor",
    "--level", "debug",
)


class RumorRunner:
    def __init__(self):
        self.p = None

    async def check_docker_ps(self):
        p = await asyncio.create_subprocess_shell(
            "docker ps",
            stdout = asyncio.subprocess.PIPE,
            stderr = asyncio.subprocess.PIPE,
        )
        stdout, _ = await p.communicate()
        out = stdout.decode().rstrip("\n\r ")
        return CONTAINER_NAME in out

    async def kill_old_container(self):
        p = await asyncio.create_subprocess_shell(
            f"docker stop {CONTAINER_NAME}",
            stdout = asyncio.subprocess.PIPE,
            stderr = asyncio.subprocess.PIPE,
        )
        await p.wait()
        assert await self.check_docker_ps() is False

    async def start_process(self):
        logging.info("Recreating rumor process ...")
        # Kill old process if needed
        if self.p is not None and self.p.returncode is not None:
            logging.debug("Killing old process ...")
            self.p.kill()
        logging.debug("Killing old container ...")
        await self.kill_old_container()
        # Parsing arguments
        main_cmd = " ".join(ARGS)
        vpn = os.environ.get("VPN_NETWORK", "")
        if vpn:
            vpn = f"--network={vpn}"
        # Create child process with rumor
        tmp_p = await asyncio.create_subprocess_shell(
            main_cmd.format(vpn=vpn),
            stdin  = asyncio.subprocess.PIPE,
            stdout = asyncio.subprocess.PIPE,
            stderr = asyncio.subprocess.PIPE,
        )
        await tmp_p.wait()
        self.p = await asyncio.create_subprocess_shell(
            f"docker logs -f {CONTAINER_NAME}",
            stdout = asyncio.subprocess.PIPE,
            stderr = asyncio.subprocess.PIPE,
        )
        logging.info(f"Started new process #{self.p.pid}")

    async def process_line(self, line: dict):
        msg = line["msg"]
        # print(line)
        if msg == "peer disconnected":
            logging.error(f"Disconnected from peer: {line['peer']}")
            # Recreate the process
            await self.start_process()
        elif msg == "started listening on address":
            logging.debug(f"Created peer wtih address: {line['addr']}")

    async def main(self):
        await self.start_process()
        try:
            while self.p.returncode is None:
                b = await self.p.stdout.readline()
                text = b.decode().rstrip("\n\r ")

                if text and text.startswith("{"):
                    out = json.loads(text)
                    await self.process_line(out)
                elif text:
                    logging.warn("Unexpected text: \"{text}\"")

                await asyncio.sleep(0.05)
        finally:
            if self.p.returncode is not None:
                logging.info(f"Execution finished with the return code '{self.p.returncode}'!")
            else:
                logging.error("Execution was interrupted!")
            logging.debug("Killing old container ...")
            await self.kill_old_container()


if __name__ == "__main__":
    logging.basicConfig(level=logging.DEBUG)
    r = RumorRunner()
    asyncio.run(r.main())

