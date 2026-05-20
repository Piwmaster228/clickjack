import http.server

class Handler(http.server.SimpleHTTPRequestHandler):
    def guess_type(self, path):
        t = super().guess_type(path)
        if isinstance(t, str) and t.startswith('text/html'):
            return 'text/html; charset=utf-8'
        return t

    def do_GET(self):
        if self.path.startswith('/.well-known/'):
            self.send_response(200)
            self.send_header('Content-Type', 'application/json')
            self.end_headers()
            self.wfile.write(b'{}')
            return
        super().do_GET()

http.server.test(HandlerClass=Handler, port=5000, bind='0.0.0.0')
