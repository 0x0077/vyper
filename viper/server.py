
from http.server import BaseHTTPRequestHandler, HTTPServer
from socketserver import ThreadingMixIn

import json

from viper.parser import parse_to_lll
from viper import compiler, optimizer


class ViperRequestHandler(BaseHTTPRequestHandler):

    def send_404(self):
        self.send_response(404)
        self.end_headers()
        return

    def do_GET(self):

        if self.path == '/':
            self.send_response(200)
            self.end_headers()
            self.wfile.write(b'Viper Compiler.\n')
        else:
            self.send_404()

        return

    def do_POST(self):

        if self.path == '/compile':
            content_len = int(self.headers.get('content-length'))
            post_body = self.rfile.read(content_len)
            data = json.loads(post_body)

            response, status_code = self._compile(data)

            self.send_response(status_code)
            self.send_header("Content-type", "application/json")
            self.end_headers()
            self.wfile.write(json.dumps(response).encode())

        else:
            self.send_404()

        return

    def _compile(self, data):
        code = data.get('code')
        if not code:
            return {'status': 'failed', 'message': 'No "code" key supplied'}, 400
        if not isinstance(code, str):
            return {'status': 'failed', 'message': '"code" must be a non-emtpy string'}, 400

        try:
            code = data['code']
            out_dict = {
                'abi': compiler.mk_full_signature(code),
                'bytecode': '0x' + compiler.compile(code).hex(),
                'ir': str(optimizer.optimize(parse_to_lll(code)))
            }
        except Exception as e:
            return {
                'status': 'failed', 'message': str(e)
            }, 500

        out_dict.update({'status': "success"})

        return out_dict, 200


class ViperHTTPServer(ThreadingMixIn, HTTPServer):
    """Handle requests in a separate thread."""


def runserver(host='', port=8000):
    server_address = (host, int(port))
    httpd = ViperHTTPServer(server_address, ViperRequestHandler)
    print('Listening on http://{0}:{1}'.format(host, port))
    httpd.serve_forever()
    httpd.shutdown()
