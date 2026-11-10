"""Temporary loopback-only CONNECT relay for remote dependency downloads.

TLS stays end-to-end. No request bodies, credentials or traffic are logged.
Only known package/model distribution domains and port 443 are allowed.
"""
import http.server
import select
import socket

DOMAINS = ('pypi.org', 'pythonhosted.org', 'pytorch.org', 'huggingface.co',
           'hf.co', 'xethub.hf.co', 'github.com', 'githubusercontent.com')


class Relay(http.server.BaseHTTPRequestHandler):
    def log_message(self, *args):
        pass

    def do_CONNECT(self):
        host, _, port = self.path.rpartition(':')
        if port != '443' or not any(host == d or host.endswith('.' + d) for d in DOMAINS):
            self.send_error(403)
            return
        try:
            upstream = socket.create_connection((host, 443), timeout=20)
        except OSError:
            self.send_error(502)
            return
        with upstream:
            self.send_response(200, 'Connection established')
            self.end_headers()
            self.wfile.flush()
            peers = [self.connection, upstream]
            try:
                while True:
                    ready, _, _ = select.select(peers, [], [], 120)
                    if not ready:
                        return
                    for source in ready:
                        data = source.recv(256 * 1024)
                        if not data:
                            return
                        (upstream if source is self.connection else self.connection).sendall(data)
            except OSError:
                return


if __name__ == '__main__':
    server = http.server.ThreadingHTTPServer(('127.0.0.1', 18791), Relay)
    server.daemon_threads = True
    server.serve_forever()
