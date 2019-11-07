import asyncio
import functools
import os
import re
import sys
import traceback

if sys.platform == "win32":
    asyncio.set_event_loop_policy(asyncio.WindowsProactorEventLoopPolicy())


def log_async_exception(log_func=None, stop_loop=False, ignore_cancel=True):
    """
    A decorator that wraps the passed in coroutine and logs any uncaught exception and optionally stops the loop
    """
    if log_func is None:
        log_func = print

    def deco(coroutine):
        @functools.wraps(coroutine)
        async def wrapper(*args, **kwargs):
            try:
                await coroutine(*args, **kwargs)
            except Exception as e:
                if ignore_cancel and isinstance(e, asyncio.CancelledError):
                    pass
                else:
                    # log the exception and stop everything
                    log_func(f'\nCoroutine "{coroutine.__qualname__}" terminated due to exception\n' + " |"
                             "\n  | ".join(traceback.format_exc().splitlines()))
                    if stop_loop:
                        log_func("Stopping event loop due to unhandled exception in coroutine")
                        loop = asyncio.get_event_loop()
                        loop.stop()

        return wrapper

    return deco


class ShellRunner:
    def __init__(self, cmd="cmd"):
        self._cmd = cmd
        self._buffer = ""
        self._expect_found = asyncio.Event()
        self._patt = []
        self._process = None
        self._which_pattern_matched = -1
        self._tasks = []
        self.before = ""
        self.after = ""
        self.match = None

    async def sendline(self, string):
        await self.send(string + "\n")

    async def send(self, string):
        if self._process is None:
            await self._start_process()
        self._process.stdin.write(f"{string}".encode("ascii"))
        await self._process.stdin.drain()

    @log_async_exception(stop_loop=True)
    async def _start_process(self):
        self._process = await asyncio.create_subprocess_shell(self._cmd,
                                                              stdin=asyncio.subprocess.PIPE,
                                                              stdout=asyncio.subprocess.PIPE,
                                                              stderr=asyncio.subprocess.PIPE)
        self._tasks.append(asyncio.create_task(self._read_stdout(self._process.stdout)))
        self._tasks.append(asyncio.create_task(self._read_stderr(self._process.stderr)))

    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, exc_value, traceback):
        for task in self._tasks:
            task.cancel()
        self._process.stdin.write_eof()
        await self._process.stdin.drain()
        try:
            await asyncio.wait_for(self._process.wait(), timeout=1.0)
        except asyncio.TimeoutError:
            self._process.kill()

    async def expect(self, regex, timeout=10):
        if self._process is None:
            await self._start_process()
        if isinstance(regex, str):
            regex = [regex]
        self._patt = [re.compile(r) for r in regex]
        try:
            await asyncio.wait_for(self._expect_found.wait(), timeout=timeout)
        except asyncio.TimeoutError:
            raise TimeoutError(f"Expect timed out, buffer contents:\n {self._buffer!r}")
        self._expect_found.clear()
        self._patt = []
        return self._which_pattern_matched

    @log_async_exception(stop_loop=True)
    async def _read_stdout(self, stream):
        while True:
            try:
                char = await asyncio.wait_for(stream.read(1), timeout=0.1)
                if not char:
                    break
                self._buffer += char.decode("ascii")
                print(char.decode("ascii"), end="", flush=True)
            except asyncio.TimeoutError:
                pass
            for which, p in enumerate(self._patt):
                match = p.search(self._buffer)
                if match:
                    self.match = match
                    self.after = match.group(0)
                    self.before = self._buffer[:match.start()]
                    self._buffer = self._buffer[match.end():]
                    self._which_pattern_matched = which
                    self._expect_found.set()
                    break

    @log_async_exception(stop_loop=True)
    async def _read_stderr(self, stream):
        while True:
            line = await stream.readline()
            if line:
                print(f'\n{line.decode("ascii").strip()}', flush=True)
            else:
                break


async def main():
    commands = ["dir", "conda activate pigss", "conda info", "echo All done"]
    prompt = lambda: re.escape(os.getcwd() + ">")
    async with ShellRunner("cmd") as client:
        await client.expect(prompt())
        for command in commands:
            await client.sendline(command)
            await client.expect(prompt())
            await client.sendline("echo ExitCode: %errorlevel%")
            await client.expect("echo ExitCode: %errorlevel%\nExitCode: ([-+]?[0-9]+)\r\n", 5)
            if int(client.match.group(1)) != 0:
                break
            await client.expect(prompt())


if __name__ == "__main__":
    asyncio.run(main())
