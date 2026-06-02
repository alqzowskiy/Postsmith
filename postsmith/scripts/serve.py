import argparse
import functools
import os
import shutil
import socketserver
import sys
import threading
import webbrowser
from http.server import SimpleHTTPRequestHandler

import workspace


HOST = "127.0.0.1"
DEFAULT_PORT = 4848


class Gallery(socketserver.ThreadingTCPServer):
    allow_reuse_address = True


def gallery_source():
    here = os.path.dirname(os.path.abspath(__file__))
    return os.path.normpath(os.path.join(here, "..", "assets", "gallery.html"))


def install_gallery(target_dir):
    shutil.copyfile(gallery_source(), os.path.join(target_dir, "index.html"))


def serve_dir(root, port, no_open):
    handler = functools.partial(QuietHandler, directory=root)
    url = "http://" + HOST + ":" + str(port) + "/"
    with Gallery((HOST, port), handler) as server:
        print("Serving " + root)
        print("Gallery at " + url)
        print("Press Ctrl+C to stop.")
        if not no_open:
            threading.Timer(0.8, lambda: webbrowser.open(url)).start()
        try:
            server.serve_forever()
        except KeyboardInterrupt:
            print("")
            print("Stopped.")
        finally:
            server.shutdown()


class QuietHandler(SimpleHTTPRequestHandler):
    def log_message(self, *args):
        return


def serve_job(workspace_path, job_id, port, no_open):
    out_dir = workspace.job_dir(workspace_path, job_id)
    if not os.path.isdir(out_dir):
        print("No such job: " + job_id, file=sys.stderr)
        sys.exit(1)
    if not os.path.exists(os.path.join(out_dir, "manifest.json")):
        print("Warning: no manifest.json in " + out_dir + " yet.", file=sys.stderr)
    install_gallery(out_dir)
    serve_dir(out_dir, port, no_open)


def serve_history(workspace_path, port, no_open):
    registry = workspace.load_registry(workspace_path)
    install_gallery(workspace_path)
    for job in registry.get("jobs", []):
        out_dir = workspace.job_dir(workspace_path, job.get("id", ""))
        if os.path.isdir(out_dir):
            install_gallery(out_dir)
    serve_dir(workspace_path, port, no_open)


def run(job=None, port=None, no_open=False):
    workspace_path = workspace.init_workspace()
    if port is None:
        config = workspace.load_config(workspace_path)
        port = config["defaults"].get("port", DEFAULT_PORT)
    if job:
        serve_job(workspace_path, job, port, no_open)
    else:
        serve_history(workspace_path, port, no_open)


def main(argv=None):
    parser = argparse.ArgumentParser(description="Serve a postsmith gallery.")
    parser.add_argument("--job", help="job id to serve (default: history of all jobs)")
    parser.add_argument("--port", type=int, default=None)
    parser.add_argument("--no-open", action="store_true", help="do not open a browser")
    args = parser.parse_args(argv)
    run(job=args.job, port=args.port, no_open=args.no_open)


if __name__ == "__main__":
    main()
