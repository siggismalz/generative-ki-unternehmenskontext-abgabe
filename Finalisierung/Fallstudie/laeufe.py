"""Wiederholt die vorab festgelegten Modellläufe über die lokale Anwendungs-API.

Aufruf unter Windows: python -X utf8 laeufe.py ANWENDUNGSORDNER ZIELORDNER
Optional vergleicht --archiv PFAD den ausführbaren Stand mit der Phase-2-Abgabe.
Voraussetzung: Der Demonstrator wurde im Anwendungsordner eingerichtet.
"""
import argparse
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
import platform
import re
import socket
import subprocess
import time
import urllib.error
import urllib.request
import zipfile

def sha(path):
    with path.open("rb") as f:
        return hashlib.file_digest(f, "sha256").hexdigest()

def json_sichern(path, obj):
    path.write_text(json.dumps(obj, ensure_ascii=False, indent=2), encoding="utf-8")

def freier_port():
    with socket.socket() as s:
        s.bind(("127.0.0.1",0))
        return s.getsockname()[1]

def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument("app", type=Path)
    parser.add_argument("ziel", type=Path)
    parser.add_argument("--archiv", type=Path)
    args=parser.parse_args()
    root=args.app.resolve()
    ziel=args.ziel.resolve()
    ziel.mkdir(parents=True, exist_ok=True)
    if any((ziel/name).exists() for name in ("Rohdaten.json","Provenienz.json")):
        parser.error("Für jede Messung einen freien Zielordner wählen.")
    spec=Path(__file__).with_name("Faelle_vorab.json")
    faelle=json.loads(spec.read_text(encoding="utf-8-sig"))["faelle"]
    config=json.loads((root/"konfiguration.json").read_text(encoding="utf-8"))
    hashes={n:sha(root/n) for n in ("app.py","uebersetzer.py","prompts.json","konfiguration.json","oberflaeche/app.js","oberflaeche/index.html","oberflaeche/stil.css")}
    archiv={}
    if args.archiv:
        with zipfile.ZipFile(args.archiv) as z:
            for name,h in hashes.items():
                item=next(n for n in z.namelist() if n.endswith("/Anwendung/"+name))
                actual=hashlib.sha256(z.read(item)).hexdigest()
                # Git kann beim Auschecken nur Zeilenenden ändern.
                in_zip=z.read(item)
                local=(root/name).read_bytes()
                if local.replace(b"\r\n",b"\n") != in_zip.replace(b"\r\n",b"\n"):
                    raise ValueError("Abweichung von Phase 2: "+name)
                archiv[name]={"sha256":actual,"byteidentisch":h==actual}
    modellhash=sha(root/config["modell_datei"])
    if modellhash!=config["modell_sha256"]:
        raise ValueError("Abweichender Modellhash")
    port=freier_port()
    modelport=freier_port()
    while modelport==port:
        modelport=freier_port()
    prov={"start_utc":datetime.now(timezone.utc).isoformat(),"rechner":platform.platform(),"prozessor":os.getenv("PROCESSOR_IDENTIFIER"),"python_runtime":sha(root/"laufzeit/python/python.exe"),"llama_server":sha(root/"laufzeit/llama/llama-server.exe"),"modell_sha256_gemessen":modellhash,"fallkatalog_sha256":sha(spec),"dateien_sha256":hashes,"phase2_zip_sha256":sha(args.archiv) if args.archiv else None,"phase2_abgleich":archiv,"konfiguration":config,"port":port,"modell_port":modelport}
    json_sichern(ziel/"Provenienz.json",prov)
    base=f"http://127.0.0.1:{port}"
    opener=urllib.request.build_opener(urllib.request.ProxyHandler({}))
    token=None
    def post(path,data):
        req=urllib.request.Request(base+path,data=json.dumps(data).encode(),
              headers={"Content-Type":"application/json","X-Session-Token":token,"Origin":base})
        with opener.open(req,timeout=135) as response:
            return json.load(response)
    p=subprocess.Popen([str(root/"laufzeit/python/python.exe"),"-B","-X","utf8",str(root/"app.py"),"--ohne-browser","--port",str(port),"--modell-port",str(modelport)],cwd=root,creationflags=subprocess.CREATE_NO_WINDOW)
    rows=[]
    try:
        for _ in range(80):
            try:
                with opener.open(base,timeout=2) as response:
                    html=response.read().decode()
                break
            except OSError:
                if p.poll() is not None: raise RuntimeError("Anwendung beendet")
                time.sleep(0.1)
        token=re.search(r'name="session-token" content="([^"]+)"',html).group(1)
        for prompt in ("handel-v2","basis-v1"):
            for case in faelle:
                data={k:case[k] for k in ("text","richtung","textsorte","glossar")}
                data.update(fall_id=case["id"],prompt=prompt)
                try:
                    result=post("/api/translate",data)
                    export=post("/api/export",{**data,"id":result["id"],"korrektur":result["korrektur"],"geprueft":False})
                    assert export["status"]=="Entwurf" and result["rohuebersetzung"]==export["rohuebersetzung"]
                    rows.append(export)
                except urllib.error.HTTPError as exc:
                    rows.append({**data,"api_fehler":exc.code,"fehlermeldung":exc.read().decode()})
                json_sichern(ziel/"Rohdaten.json",rows)
                print(prompt,case["id"],rows[-1].get("sekunden",rows[-1].get("fehlermeldung")),flush=True)
    finally:
        if token:
            try:post("/api/shutdown",{})
            except OSError:pass
        try:p.wait(timeout=10)
        except subprocess.TimeoutExpired:p.terminate();p.wait(timeout=10)
        prov["ende_utc"]=datetime.now(timezone.utc).isoformat()
        prov["prozess_exit"]=p.returncode
        json_sichern(ziel/"Provenienz.json",prov)
if __name__=="__main__":
    main()

