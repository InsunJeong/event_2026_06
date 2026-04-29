#!/usr/bin/env python3
"""Local server with fake GraphQL endpoint and Next.js image proxy"""
import http.server
import json
import re
import urllib.parse
import os

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

    def do_GET(self):
        # Next.js image optimization API 처리
        if self.path.startswith('/_next/image'):
            parsed = urllib.parse.urlparse(self.path)
            params = urllib.parse.parse_qs(parsed.query)
            url = params.get('url', [''])[0]

            # URL 디코딩 후 쿼리 파라미터 제거
            url = urllib.parse.unquote(url)
            url = url.split('?')[0]

            # 선행 슬래시 제거해서 로컬 파일 경로로 변환
            local_path = url.lstrip('/')

            if os.path.isfile(local_path):
                self.send_response(200)
                ext = os.path.splitext(local_path)[1].lower()
                content_types = {'.png': 'image/png', '.jpg': 'image/jpeg', '.jpeg': 'image/jpeg', '.gif': 'image/gif', '.webp': 'image/webp', '.svg': 'image/svg+xml'}
                self.send_header('Content-Type', content_types.get(ext, 'application/octet-stream'))
                self.end_headers()
                with open(local_path, 'rb') as f:
                    self.wfile.write(f.read())
                return
            else:
                print(f'  [image] NOT FOUND: {local_path}')
                self.send_response(404)
                self.end_headers()
                return

        # 일반 파일 서빙
        super().do_GET()

    def do_POST(self):
        if '/graphql' in self.path:
            length = int(self.headers.get('Content-Length', 0))
            body = self.rfile.read(length).decode('utf-8') if length else ''

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
    print('Image proxy: http://localhost:8080/_next/image?url=...')
    http.server.test(HandlerClass=Handler, port=8080)
