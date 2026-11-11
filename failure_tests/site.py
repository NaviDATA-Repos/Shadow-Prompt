# Test "chatbot" page (port 8081). POST /external records what crosses the external boundary.
import json
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
LOG=[]
PAGE=b"""<!doctype html><meta charset=utf-8><title>Fake chatbot</title>
<form id=f><textarea id=prompt rows=4 cols=60></textarea><button id=send type=submit>Send</button></form>
<script>
async function out(){ await fetch('/external',{method:'POST',body:document.getElementById('prompt').value}); }
document.getElementById('f').addEventListener('submit',e=>{e.preventDefault();out();});
document.getElementById('prompt').addEventListener('keydown',e=>{ if(e.key==='Enter'&&!e.shiftKey){e.preventDefault();out();} });
</script>"""
class H(BaseHTTPRequestHandler):
    def log_message(self,*a): pass
    def do_GET(self):
        if self.path=='/log': b=json.dumps(LOG).encode(); ct='application/json'
        elif self.path=='/reset': LOG.clear(); b=b'ok'; ct='text/plain'
        else: b=PAGE; ct='text/html'
        self.send_response(200); self.send_header('Content-Type',ct); self.end_headers(); self.wfile.write(b)
    def do_POST(self):
        n=int(self.headers.get('Content-Length',0)); LOG.append(self.rfile.read(n).decode()); self.send_response(200); self.end_headers(); self.wfile.write(b'ok')
ThreadingHTTPServer(('127.0.0.1',8081),H).serve_forever()
