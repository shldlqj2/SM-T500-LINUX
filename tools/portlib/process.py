"""Bounded binary capture. Never invokes a host shell or kills the ADB server."""
from dataclasses import dataclass
from datetime import datetime, timezone
import queue
import subprocess
import threading
import time


@dataclass
class Result:
    stdout: bytes
    stderr: bytes
    exit_code: int | None
    started_at: str
    duration_ms: int
    error_code: str | None = None
    cleanup_unconfirmed: bool = False


class Runner:
    def run(self, argv, *, timeout=15.0, limit=8 * 1024 * 1024):
        started_at = datetime.now(timezone.utc).isoformat(timespec="milliseconds").replace("+00:00", "Z")
        start = time.monotonic()
        buffers = [bytearray(), bytearray()]
        error = None
        cleanup = False
        proc = None
        messages = queue.Queue(maxsize=16)
        stop = threading.Event()
        threads = []

        def reader(stream, index):
            try:
                while not stop.is_set():
                    chunk = stream.read(65536)
                    if not chunk:
                        break
                    while not stop.is_set():
                        try:
                            messages.put((index, chunk), timeout=0.05)
                            break
                        except queue.Full:
                            pass
            except (OSError, ValueError):
                pass
            finally:
                while not stop.is_set():
                    try:
                        messages.put((index, None), timeout=0.05)
                        break
                    except queue.Full:
                        pass

        try:
            proc = subprocess.Popen(argv, stdin=subprocess.DEVNULL, stdout=subprocess.PIPE,
                                    stderr=subprocess.PIPE, shell=False, bufsize=0)
            for index, stream in enumerate((proc.stdout, proc.stderr)):
                thread = threading.Thread(target=reader, args=(stream, index), daemon=True)
                thread.start()
                threads.append(thread)
            done = set()
            total = 0
            while len(done) < 2 or proc.poll() is None:
                if time.monotonic() - start >= timeout:
                    error = "timeout"
                    break
                try:
                    index, chunk = messages.get(timeout=0.02)
                except queue.Empty:
                    continue
                if chunk is None:
                    done.add(index)
                    continue
                kept = chunk[:max(0, limit - total)]
                buffers[index].extend(kept)
                total += len(kept)
                if len(kept) != len(chunk):
                    error = "output_limit"
                    break
        except KeyboardInterrupt:
            error = "user_interrupted"
        except OSError:
            error = "tool_failed"
        finally:
            if proc is not None:
                if error is not None:
                    # Even an exited client does not prove remote commands have stopped.
                    cleanup = True
                if proc.poll() is None:
                    try:
                        proc.terminate()
                        proc.wait(timeout=0.5)
                    except (OSError, subprocess.TimeoutExpired):
                        try:
                            proc.kill()
                            proc.wait(timeout=0.5)
                        except (OSError, subprocess.TimeoutExpired):
                            cleanup = True
                stop.set()
                for thread in threads:
                    thread.join(timeout=0.25)
                # Do not block closing pipes still owned by a reader with an inherited FD.
                if not any(thread.is_alive() for thread in threads):
                    proc.stdout.close()
                    proc.stderr.close()
                else:
                    cleanup = True
        return Result(bytes(buffers[0]), bytes(buffers[1]),
                      proc.poll() if proc is not None else None, started_at,
                      max(0, int((time.monotonic() - start) * 1000)), error, cleanup)
