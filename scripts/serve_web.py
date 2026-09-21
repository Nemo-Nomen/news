import functools
import http.server

DIRECTORY = "/Users/axel/Documents/Axel News/web"
PORT = 8743

handler = functools.partial(http.server.SimpleHTTPRequestHandler, directory=DIRECTORY)
httpd = http.server.ThreadingHTTPServer(("127.0.0.1", PORT), handler)
print(f"Serving {DIRECTORY} on http://127.0.0.1:{PORT}")
httpd.serve_forever()
