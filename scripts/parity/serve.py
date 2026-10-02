#!/usr/bin/env python3
"""Serve a static build or a WordPress mirror for parity runs in the cloud (which cannot reach .test sites).

    python3 serve.py <folder> <port> [--not-found 404.html]

/about/ serves about/index.html, a missing path serves the not-found page with status 404, every response is
no-store. Example: the static build on 8771 and the mirror on 8773, then
REF=http://127.0.0.1:8771 WP=http://127.0.0.1:8773 node parity.mjs --widths=390,768,1440
"""
import http.server
import os
import sys
from functools import partial

ROOT = os.path.abspath(sys.argv[1])
PORT = int(sys.argv[2])
NOT_FOUND = sys.argv[sys.argv.index('--not-found') + 1] if '--not-found' in sys.argv else '404.html'


class Handler(http.server.SimpleHTTPRequestHandler):
    def end_headers(self):
        self.send_header('Cache-Control', 'no-store')
        super().end_headers()

    def send_head(self):
        path = self.translate_path(self.path)
        if os.path.isdir(path) and not os.path.exists(os.path.join(path, 'index.html')) or (not os.path.exists(path) and not os.path.isdir(path)):
            page = os.path.join(ROOT, NOT_FOUND)
            body = open(page, 'rb').read() if os.path.exists(page) else b'Not found'
            self.send_response(404)
            self.send_header('Content-Type', 'text/html; charset=utf-8')
            self.send_header('Content-Length', str(len(body)))
            self.end_headers()
            from io import BytesIO
            return BytesIO(body)
        return super().send_head()

    def log_message(self, *args):
        pass


http.server.ThreadingHTTPServer(('127.0.0.1', PORT), partial(Handler, directory=ROOT)).serve_forever()
