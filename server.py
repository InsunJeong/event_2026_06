#!/usr/bin/env python3
"""Local server with fake GraphQL endpoint"""
import http.server
import json
import re

class Handler(http.server.SimpleHTTPRequestHandler):
    def end_headers(self):
        self.send_header('Cache-Control', 'no-store, no-cache, must-revalidate, max-age=0')
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Headers', '*')
        self.send_header('Access-Control-Allow-Methods', '*')
        super().end_headers()

    def do_OPTIONS(self):
        self.send_response(200)
        self.end_headers()

    def do_POST(self):
        if '/graphql' in self.path:
            length = int(self.headers.get('Content-Length', 0))
            body = self.rfile.read(length).decode('utf-8') if length else ''

            # birthday-card 페이지의 __NEXT_DATA__에서 데이터 읽기
            try:
                with open('birthday-card/index.html', 'r') as f:
                    html = f.read()
                m = re.search(r'type="application/json">\s*(.*?)\s*</script>', html, re.DOTALL)
                if m:
                    data = json.loads(m.group(1))
                    meta = data['props']['pageProps']['birthdayCardMeta']

                    if 'getBirthdayCard' in body and 'Coupon' not in body:
                        resp = json.dumps({'data': {'getBirthdayCard': meta}})
                    elif 'Coupon' in body:
                        resp = json.dumps({'data': {'getBirthdayCardCoupon': None}})
                    elif 'Session' in body or 'getSession' in body:
                        resp = json.dumps({'data': {'getSession': None}})
                    else:
                        resp = json.dumps({'data': {}})
                else:
                    resp = json.dumps({'data': {}})
            except Exception as e:
                print(f'Error: {e}')
                resp = json.dumps({'data': {}})

            self.send_response(200)
            self.send_header('Content-Type', 'application/json')
            self.end_headers()
            self.wfile.write(resp.encode())
            return

        self.send_response(404)
        self.end_headers()

if __name__ == '__main__':
    print('Starting server on http://localhost:8080')
    print('GraphQL endpoint: http://localhost:8080/graphql')
    http.server.test(HandlerClass=Handler, port=8080)
