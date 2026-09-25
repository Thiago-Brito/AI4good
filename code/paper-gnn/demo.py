"""Local browser demo; every /predict request executes the trained networks."""
import argparse
import json
from http.server import BaseHTTPRequestHandler, HTTPServer
from urllib.parse import urlparse, parse_qs
from data import ROOT, OUTPUTS
from infer import Predictor


def serve(port):
    predictor=Predictor()
    class Handler(BaseHTTPRequestHandler):
        def do_GET(self):
            url=urlparse(self.path)
            if url.path=='/':
                content=(ROOT/'demo.html').read_bytes(); content_type='text/html; charset=utf-8'
            elif url.path=='/predict':
                try:
                    node=int(parse_qs(url.query).get('node',['1708'])[0])
                    content=json.dumps(predictor.predict(node)).encode(); content_type='application/json'
                except (ValueError, IndexError):
                    self.send_error(400,'Invalid node'); return
            elif url.path=='/summary':
                content=(OUTPUTS/'main/summary.json').read_bytes(); content_type='application/json'
            elif url.path=='/paper.pdf':
                content=(ROOT.parents[1]/'academy/papers/artigo-overleaf/outputs/ordered-gnn/artigo-original-2023.pdf').read_bytes()
                content_type='application/pdf'
            elif url.path=='/report.pdf':
                content=(ROOT.parents[1]/'academy/papers/artigo-overleaf/outputs/ordered-gnn/samplepaper.pdf').read_bytes()
                content_type='application/pdf'
            else:
                self.send_error(404); return
            self.send_response(200); self.send_header('Content-Type',content_type)
            self.send_header('Content-Length',str(len(content))); self.end_headers(); self.wfile.write(content)
    print(f'Demonstracao: http://127.0.0.1:{port}',flush=True)
    HTTPServer(('127.0.0.1',port),Handler).serve_forever()


if __name__=='__main__':
    p=argparse.ArgumentParser(); p.add_argument('--port',type=int,default=8765)
    serve(p.parse_args().port)
