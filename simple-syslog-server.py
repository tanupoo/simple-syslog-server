from socketserver import UDPServer, DatagramRequestHandler
import logging
import struct
import re
from argparse import ArgumentParser

ap = ArgumentParser()
ap.add_argument("-s", action="store", dest="server_addr",
                default="0.0.0.0", help="server's addrees.")
ap.add_argument("-p", action="store", dest="server_port",
                type=int, default=8514, help="server's port number.")
ap.add_argument("-f", action="store", dest="log_file", help="the filename to be logged.")
ap.add_argument("-d", action="store_true", dest="debug", help="enable debug mode.")
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
            buf = buf.decode(encoding="utf-8", errors="ignore")
            r = re_line.match(buf)
            if r:
                pri = int(r.group("pri"))
                msg = r.group("msg")
                putlog(pri, msg)

if opt.log_file:
    handler = logging.FileHandler(opt.log_file, mode="a")
    handler.setLevel(logging.DEBUG)
    handler.setFormatter(logging.Formatter(LOG_FORMAT,
                                           datefmt=LOG_DATEFMT))
    logger.addHandler(handler)

if opt.debug:
    handler = logging.StreamHandler()
    handler.setLevel(logging.DEBUG)
    handler.setFormatter(logging.Formatter(LOG_FORMAT,
                                           datefmt=LOG_DATEFMT))
    logger.addHandler(handler)

logger.info(f"Listen on: {opt.server_addr}:{opt.server_port}")
server = UDPServer((opt.server_addr, opt.server_port), SyslogUDPHandler)
server.serve_forever()
