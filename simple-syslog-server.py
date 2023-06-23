#!/usr/bin/env python

from socketserver import UDPServer, DatagramRequestHandler
import logging
import re
from argparse import ArgumentParser
from HTTPRequestsHandler import HTTPRequestsHandler

ap = ArgumentParser()
ap.add_argument("-s", action="store", dest="server_addr",
                default="0.0.0.0", help="server's addrees.")
ap.add_argument("-p", action="store", dest="server_port",
                type=int, default=8514, help="server's port number.")
ap.add_argument("--decode", action="store", dest="decode_policy",
                choices=["ignore", "strict", "replace"], default="replace",
                help="specify the decode policy if it's failed.")
ap.add_argument("--file-handler", "-f", action="store", dest="log_file",
                help="enable FILE handler and specify the filename to log.")
ap.add_argument("--http-handler", "-H", action="store", dest="log_url",
                help="enable HTTP handler "
                "and specify the url to sent the message.")
ap.add_argument("-d", action="store_true", dest="debug",
                help="enable debug mode.")
opt = ap.parse_args()

logger = logging.getLogger("syslog")
logger.setLevel(logging.DEBUG)

re_line = re.compile("<(?P<pri>\d+)>(?P<msg>.*)")
LOG_FORMAT = "%(asctime)s.%(msecs)d: %(levelname)s: %(message)s"
LOG_DATEFMT = "%Y-%m-%dT%H:%M:%S"

def putlog(pri, msg):
    if pri == 15:
        logger.debug(f"{msg}")
    elif pri == 14:
        logger.info(f"{msg}")
    elif pri == 12:
        logger.warning(f"{msg}")
    elif pri == 11:
        logger.error(f"{msg}")
    elif pri == 10:
        logger.fatal(f"{msg}")
    else:
        logger.info(f"<{pri}>{msg}")

class SyslogUDPHandler(DatagramRequestHandler):

    def handle(self):
        client_addr, client_port = self.client_address
        while True:
            buf = self.rfile.read(512)
            if len(buf) == 0:
                break
            buf = buf.decode(encoding="utf-8", errors=opt.decode_policy)
            r = re_line.match(buf)
            if r:
                pri = int(r.group("pri"))
                msg = r.group("msg")
                if msg[-1] == "\x00":
                    msg = msg[:-1]
                putlog(pri, msg)
            else:
                putlog(logging.ERROR, f"SYSLOG ERROR: {buf}")

if opt.log_file:
    handler = logging.FileHandler(opt.log_file, mode="a")
    handler.setLevel(logging.DEBUG)
    handler.setFormatter(logging.Formatter(LOG_FORMAT,
                                           datefmt=LOG_DATEFMT))
    logger.addHandler(handler)

if opt.log_url:
    handler = HTTPRequestsHandler(opt.log_url)
    handler.setLevel(logging.DEBUG)
    logger.addHandler(handler)

if opt.debug or not (opt.log_file or opt.log_url):
    handler = logging.StreamHandler()
    handler.setLevel(logging.DEBUG)
    handler.setFormatter(logging.Formatter(LOG_FORMAT,
                                           datefmt=LOG_DATEFMT))
    logger.addHandler(handler)

putlog(logging.INFO, f"Listen on: {opt.server_addr}:{opt.server_port}")
server = UDPServer((opt.server_addr, opt.server_port), SyslogUDPHandler)
server.serve_forever()
