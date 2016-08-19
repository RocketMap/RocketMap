#!/usr/bin/env python
# -*- coding:utf-8 -*-

# A super basic python webhook receiver
# Run in a new terminal as:
#
#    ./hook.py 0.0.0.0 8123
#
# Then setup your runserver.py with `-wh http://127.0.0.1:8123`

import sys
import time
import json
import pprint
from BaseHTTPServer import BaseHTTPRequestHandler, HTTPServer

HOST_NAME = sys.argv[1]
HOST_PORT = int(sys.argv[2])


class S(BaseHTTPRequestHandler):
    def do_POST(self):
        data_string = self.rfile.read(int(self.headers['Content-Length']))
        self.send_response(200)
        self.end_headers()
        pprint.pprint(json.loads(data_string))


if __name__ == '__main__':
    httpd = HTTPServer((HOST_NAME, HOST_PORT), S)
    print time.asctime(), "Server Starts - %s:%s" % (HOST_NAME, HOST_PORT)
    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        pass
    httpd.server_close()
    print time.asctime(), "Server Stops - %s:%s" % (HOST_NAME, HOST_PORT)
