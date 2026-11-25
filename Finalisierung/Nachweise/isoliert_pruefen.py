"""Prüft ein Abgabearchiv nach frischer Extraktion mit den originalen Installationsdateien."""
from argparse import ArgumentParser
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
import re
import socket
import subprocess
from tempfile import TemporaryDirectory
import time
from urllib.request import build_opener, ProxyHandler, Request
from zipfile import ZipFile


def pruefe(archiv, ordner, originalverzeichnis, modell):
    with TemporaryDirectory(prefix="iu_p3_") as tmp:
        ziel = Path(tmp).resolve()
        with ZipFile(archiv) as z:
            assert z.testzip() is None
            for n in z.namelist():
                assert (ziel / n).resolve().is_relative_to(ziel)
            z.extractall(ziel)
            anzahl = len(z.infolist())
        app = ziel / "Stolz-Leon_IU14173388_DLBFMPGKIU01" / ordner / "Anwendung"
        cache = ziel / "Originale"
        cache.mkdir()
        komponenten = json.loads((app / "komponenten.json").read_text(encoding="utf-8"))
        for k in komponenten["komponenten"]:
            quelle = k.get("originaldatei", k.get("originalarchiv"))
            name = quelle["url"].rsplit("/", 1)[-1]
            lokal = modell if "originaldatei" in k else originalverzeichnis / name
            os.link(lokal, cache / name)
        # Einrichten.cmd ruft Windows PowerShell 5 auf. Den Modulpfad von PowerShell 7
        # aus der Testkonsole nicht an die eingebettete Windows PowerShell vererben.
        einrichter_env = {k: v for k, v in os.environ.items() if k.upper() != "PSMODULEPATH"}
        setup = subprocess.run(
            ["powershell.exe", "-NoProfile", "-ExecutionPolicy", "Bypass", "-File", str(app / "Einrichten.ps1"),
             "-DownloadOrdner", str(cache)], cwd=app, capture_output=True, env=einrichter_env,
            encoding="cp850", errors="replace", check=False, timeout=180,
        )
        if setup.returncode:
            raise RuntimeError(setup.stdout + setup.stderr)
        assert setup.stdout.count("SHA256 bestaetigt:") == 3
        with socket.socket() as web_socket, socket.socket() as model_socket:
            web_socket.bind(("127.0.0.1", 0))
            model_socket.bind(("127.0.0.1", 0))
            port, modell_port = web_socket.getsockname()[1], model_socket.getsockname()[1]
        url = f"http://127.0.0.1:{port}"
        client = build_opener(ProxyHandler({}))
        prozess = subprocess.Popen(
            [str(app / "laufzeit/python/python.exe"), "-B", "-X", "utf8", str(app / "app.py"),
             "--ohne-browser", "--port", str(port), "--modell-port", str(modell_port)],
            cwd=app, stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
            creationflags=subprocess.CREATE_NO_WINDOW,
        )
        token = None

        def post(pfad, daten):
            req = Request(url + "/api/" + pfad, data=json.dumps(daten).encode(), headers={
                "Content-Type": "application/json", "X-Session-Token": token, "Origin": url
            })
            with client.open(req, timeout=125) as antwort:
                return json.load(antwort)

        try:
            for _ in range(50):
                try:
                    with client.open(url, timeout=1) as r:
                        html = r.read().decode()
                    break
                except OSError:
                    time.sleep(0.2)
            else:
                raise RuntimeError("Oberfläche antwortet nicht")
            token = re.search(r'name="session-token" content="([^"]+)"', html).group(1)
            ausgabe = post("translate", {
                "fall_id": "PAKETSTART", "richtung": "DE-EN", "text": "Die Tasse ist blau.",
                "textsorte": "Produktkurztext", "prompt": "handel-v2",
            })
            assert ausgabe["rohuebersetzung"].strip() and ausgabe["status"] == "Entwurf"
            status = json.load(client.open(url + "/api/status"))
        finally:
            if token:
                post("shutdown", {})
            elif prozess.poll() is None:
                prozess.terminate()
            prozess.wait(timeout=15)
        assert prozess.returncode == 0
        return {
            "zeitpunkt_utc": datetime.now(timezone.utc).isoformat(), "zip": archiv.name,
            "sha256": hashlib.sha256(archiv.read_bytes()).hexdigest(), "anzahl_dateien": anzahl,
            "ordner": ordner + "/Anwendung", "einrichtung": setup.stdout.splitlines(),
            "laufzeit": status["version"], "lokale_ports": [port, modell_port],
            "eingabe": ausgabe["text"], "rohausgabe": ausgabe["rohuebersetzung"],
            "status": ausgabe["status"], "beendet": prozess.returncode == 0,
            "grenze": "Originaldateien aus lokalem Cache. Keine Netztrennung, kein Test der Verfügbarkeit der Downloadserver. Funktionsprobe ohne sprachliche Freigabe.",
        }


if __name__ == "__main__":
    p = ArgumentParser(description=__doc__)
    p.add_argument("archiv", type=Path)
    p.add_argument("ordner")
    p.add_argument("originalverzeichnis", type=Path)
    p.add_argument("modell", type=Path)
    p.add_argument("bericht", type=Path)
    a = p.parse_args()
    resultat = pruefe(a.archiv.resolve(), a.ordner, a.originalverzeichnis.resolve(), a.modell.resolve())
    a.bericht.write_text(json.dumps(resultat, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(resultat["rohausgabe"])

