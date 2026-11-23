"""Port forwarder for the console edge. Standard library only.

Docker will not publish a port for a container that sits only on the internal lab network, and lab containers
must stay on that network. So one small "edge" container joins both networks and forwards a single port to the
lab console. It forwards bytes to one fixed address and does nothing else. It listens on two ports that both lead to
the same console: 8300 for the console, and 8301 for the one page (Chapter 4) that must live on a different origin.
"""
import asyncio
import os

TARGET = (os.environ.get("TARGET_HOST", "bdai-console"), int(os.environ.get("TARGET_PORT", "8080")))
LISTEN = [int(p) for p in os.environ.get("LISTEN_PORTS", "8080").split(",")]
UNAVAILABLE = (
    "<!doctype html><meta charset=utf-8><title>No lab console</title>"
    "<body style='font:16px system-ui;max-width:36em;margin:4em auto'>"
    "<h1>No lab console is running</h1><p>Start one from the repository root, for example:</p>"
    "<pre>./shared/scripts/console-up.sh labs/c1-llm/ch03-prompt-injection/injection-lab/compose.yaml</pre></body>"
)


async def pipe(reader: asyncio.StreamReader, writer: asyncio.StreamWriter) -> None:
    try:
        while data := await reader.read(65536):
            writer.write(data)
            await writer.drain()
    except (ConnectionError, asyncio.CancelledError):
        pass
    finally:
        writer.close()


async def handle(client_r: asyncio.StreamReader, client_w: asyncio.StreamWriter) -> None:
    try:
        upstream_r, upstream_w = await asyncio.wait_for(asyncio.open_connection(*TARGET), timeout=3)
    except (OSError, asyncio.TimeoutError):
        body = UNAVAILABLE.encode()
        client_w.write(b"HTTP/1.1 503 Service Unavailable\r\nContent-Type: text/html; charset=utf-8\r\n"
                       b"Connection: close\r\nContent-Length: " + str(len(body)).encode() + b"\r\n\r\n" + body)
        await client_w.drain()
        client_w.close()
        return
    await asyncio.gather(pipe(client_r, upstream_w), pipe(upstream_r, client_w))


async def main() -> None:
    servers = [await asyncio.start_server(handle, "0.0.0.0", port) for port in LISTEN]
    await asyncio.gather(*(s.serve_forever() for s in servers))


if __name__ == "__main__":
    asyncio.run(main())
