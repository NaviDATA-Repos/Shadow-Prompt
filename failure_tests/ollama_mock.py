# Stub of the Ollama OpenAI-compatible endpoint. Modes: ok | timeout | invalid | http500
import sys, json, time, re
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
MODE = sys.argv[1]
class H(BaseHTTPRequestHandler):
    def log_message(self,*a): pass
    def _cors(self):
        self.send_header('Access-Control-Allow-Origin','*'); self.send_header('Access-Control-Allow-Headers','*'); self.send_header('Access-Control-Allow-Methods','*')
    def do_OPTIONS(self): self.send_response(204); self._cors(); self.end_headers()
    def do_POST(self):
        n=int(self.headers.get('Content-Length',0)); body=json.loads(self.rfile.read(n) or b'{}')
        prompt=body['messages'][0]['content']; text=prompt.split('Text to analyze: ',1)[1]
        if MODE=='timeout': time.sleep(60)
        if MODE=='http500':
            self.send_response(500); self._cors(); self.end_headers(); return
        if MODE=='invalid': out=''
        else:
            out=re.sub(r'IT\d{2}[A-Z]\d{22}','***',text); out=re.sub(r'[\w.]+@[\w.]+\.\w+','***',out)
        data=json.dumps({'choices':[{'message':{'role':'assistant','content':out}}]}).encode()
        self.send_response(200); self._cors(); self.send_header('Content-Type','application/json'); self.end_headers(); self.wfile.write(data)
ThreadingHTTPServer(('127.0.0.1',11434),H).serve_forever()
