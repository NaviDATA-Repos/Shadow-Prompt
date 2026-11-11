import subprocess, sys, time, json, os, urllib.request, csv
from playwright.sync_api import sync_playwright
HERE=os.path.dirname(os.path.abspath(__file__))
EXT={'orig':os.path.join(HERE,'..','extension','original'),'fc':os.path.join(HERE,'..','extension','fail_closed')}
PROMPT="Il mio IBAN e IT60X0542811101000000123456 e la mia email e mario.rossi@azienda.it"
SENS=['IT60X0542811101000000123456','mario.rossi@azienda.it']
CONDS=[('ok','ok'),('ollama_unavailable',None),('inference_timeout','timeout'),('invalid_output','invalid'),('http_error','http500')]
def start(cmd): return subprocess.Popen(cmd,stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL)
def get(path): return json.loads(urllib.request.urlopen('http://127.0.0.1:8081'+path).read() or b'null')
def run(extname, cond, mode, timing, how, p):
    mock = start([sys.executable,f'{HERE}/ollama_mock.py',mode]) if mode else None
    time.sleep(0.8)
    urllib.request.urlopen('http://127.0.0.1:8081/reset').read()
    ctx=p.chromium.launch_persistent_context(f'/tmp/sp_ud_{extname}_{cond}_{timing}_{how}',channel='chromium',headless=True,
        args=[f'--disable-extensions-except={EXT[extname]}',f'--load-extension={EXT[extname]}'])
    try:
        pg=ctx.new_page(); pg.goto('http://localhost:8081/'); pg.wait_for_timeout(1500)
        pg.click('#prompt'); pg.keyboard.type(PROMPT,delay=5)
        pg.wait_for_timeout(1300 if timing=='after_check' else 50)
        if how=='click': pg.click('#send')
        else: pg.keyboard.press('Enter')
        pg.wait_for_timeout(17000 if cond=='inference_timeout' else 2500)
        banner=pg.evaluate("document.getElementById('shadowprompt-banner')?.textContent||''")
        box=pg.input_value('#prompt')
    finally:
        ctx.close()
        if mock: mock.terminate()
    log=get('/log')
    leaked=[m for m in log if any(s in m for s in SENS)]
    return dict(extension=extname,condition=cond,timing=timing,submit=how,prompts_sent=len(log),unmasked_sent=len(leaked),banner=banner[:70],box_after=box[:60])
site=start([sys.executable,f'{HERE}/site.py']); time.sleep(1)
rows=[]
try:
    with sync_playwright() as p:
        for ext in sys.argv[1:] or ['orig','fc']:
            for cond,mode in CONDS:
                for timing in ('after_check','immediate'):
                    if cond=='inference_timeout' and timing=='immediate': continue
                    r=run(ext,cond,mode,timing,'click',p); rows.append(r); print(r,flush=True)
        # Enter-key path on the main cases
        for ext in sys.argv[1:] or ['orig','fc']:
            for cond,mode in (('ok','ok'),('ollama_unavailable',None)):
                r=run(ext,cond,mode,'after_check','enter',p); rows.append(r); print(r,flush=True)
finally:
    site.terminate()
with open(f'{HERE}/results.csv','w',newline='') as f:
    w=csv.DictWriter(f,fieldnames=list(rows[0])); w.writeheader(); w.writerows(rows)
