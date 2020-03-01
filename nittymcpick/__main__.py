import argparse
import os
import time
from queue import Queue
from threading import Thread

from gidgetlab.aiohttp import GitLabBot
from urllib.parse import urlparse

import gitlab
from nittymcpick.cls.job import Job
from nittymcpick.cls.linter import Linter

_args = None
bot = GitLabBot("nittymcpick")
_linter = []
job_queue = Queue()


def create_args():
    parser = argparse.ArgumentParser(
        prog="nittymcpick", description='Your friendly linting bot for gitlab')
    parser.add_argument("--token", default=os.getenv("GL_ACCESS_TOKEN"),
                        help="Access token to use (default:GL_ACCESS_TOKEN from environment)")
    parser.add_argument("--onlynew", default=False, action="store_true",
                        help="Comment only on changes (default:false)")
    parser.add_argument("--nowip", default=False, action="store_true",
                        help="Ignore WIP merge requests (default:false)")
    parser.add_argument("--host", default="127.0.0.1",
                        help="IP to bind to (default:127.0.0.1)")
    parser.add_argument("--port", type=int, default=8888,
                        help="Port to bind to (default:8888)")
    parser.add_argument("--botname", default=os.getenv("NITTY_MCPICK_USERNAME", None) or "nittymcpick",
                        help="Username of the bot in GitLab (default:NITTY_MCPICK_USERNAME from env or 'nittymcpick')")
    parser.add_argument("--tmpdir", default="/tmp",
                        help="Path for temporary checkouts")
    parser.add_argument("config", help="config file")
    return parser.parse_args()


def queue_runner():
    while True:
        if not job_queue.empty():
            x = job_queue.get()
            print("Run Job for: {}".format(x))
            try:
                x.Run()
            except Exception as e:
                print("Job {} failed: {}".format(x, e))
        else:
            time.sleep(0.5)


@bot.router.register("Merge Request Hook")
async def merge_request_event(event, gl, *args, **kwargs):
    try:
        _url = urlparse(event.data["repository"]["homepage"])
        _sgl = gitlab.Gitlab("{}://{}".format(_url.scheme,
                                              _url.netloc), private_token=_args.token)
        x = Job(event, gl, _args, _sgl, _linter)
        print("Add Job for: {}".format(x))
        job_queue.put(x)
    except Exception as e:
        print("Error at adding a job: {}".format(e))

def main():
    # Create all the needed global objects
    _args = create_args()
    if not _args.token:
        raise ValueError("Access token is not set - Can't proceed")
    _linter = Linter.SetupLinter(_args)
    # Start job queue
    worker = Thread(target=queue_runner)
    worker.setDaemon(True)
    worker.start()
    # Start webhook server
    bot.run(host=_args.host, port=_args.port)

if __name__ == "__main__":
    main()
