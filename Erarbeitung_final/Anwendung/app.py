"""Lokale Einzelplatzoberfläche. Startet ausschließlich den mitgelieferten Modellserver."""

from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
import argparse
import json
import secrets
import threading
import webbrowser
from uebersetzer import ROOT, Modell, Sitzung, validieren


class Anwendung:
    """Eine aktive Modellanfrage und genau einen aktuellen Entwurf verwalten."""

    def __init__(self, config):
        self.config = config
        self.modell = Modell(config)
        self.sitzung = Sitzung(config)
        self.token = secrets.token_urlsafe(32)
        self.anfrage_lock = threading.Lock()
        self.abbruch = threading.Event()
        self.generation = 0
        # Kurze Zustandsänderungen sind gegen gleichzeitige HTTP-Aufrufe geschützt.
        # Während der eigentlichen Übersetzung bleibt Abbrechen weiterhin erreichbar.
        self.lock = threading.RLock()

    def zuruecksetzen(self):
        """Auch ein verspätetes Ergebnis darf nach einem Abbruch nicht erscheinen."""
        with self.lock:
            self.generation += 1
            self.abbruch.set()
            self.sitzung.leeren()
            if self.anfrage_lock.locked():
                self.modell.stoppen()

    def uebersetzen(self, daten):
        """Eine neue Anfrage verwirft vorherige Ergebnisse und Freigaben."""
        # Auch ungültige neue Anfragen verwerfen einen alten Freigabestatus.
        with self.lock:
            if not self.anfrage_lock.acquire(blocking=False):
                raise ValueError("Eine Übersetzung läuft bereits. Bitte warten oder abbrechen.")
            self.sitzung.leeren()
            self.generation += 1
            generation = self.generation
            self.abbruch = threading.Event()
        try:
            eingabe = validieren(daten)
            roh, sekunden, usage = self.modell.uebersetzen(eingabe, self.abbruch)
            with self.lock:
                if self.abbruch.is_set() or generation != self.generation:
                    raise ValueError("Die Übersetzung wurde verworfen. Bitte erneut starten.")
                return self.sitzung.anlegen(eingabe, roh, sekunden, usage)
        finally:
            # Auch nach Fehlern muss ein neuer Versuch möglich sein.
            self.anfrage_lock.release()


def handler_fuer(app):
    """Den HTTP-Handler an diese Anwendung binden; Tests können eigene Instanzen nutzen."""

    class Handler(BaseHTTPRequestHandler):
        server_version = "Uebersetzungsassistent/2.2"

        def log_message(self, *_args):
            pass  # Keine Zugriffs- oder Inhaltsprotokolle.

        def host_ok(self):
            # Nur die feste Loopback-Adresse ist als Aufrufziel zugelassen.
            return self.headers.get("Host") == f'127.0.0.1:{app.config["oberflaeche_port"]}'

        def senden(self, status, inhalt, typ="application/json; charset=utf-8", extra=None):
            """Antworten einheitlich als UTF-8 senden und Browser-Caching verhindern."""
            if isinstance(inhalt, (dict, list)):
                inhalt = json.dumps(inhalt, ensure_ascii=False).encode("utf-8")
            elif isinstance(inhalt, str):
                inhalt = inhalt.encode("utf-8")
            self.send_response(status)
            self.send_header("Content-Type", typ)
            self.send_header("Content-Length", str(len(inhalt)))
            self.send_header("Cache-Control", "no-store")
            self.send_header("X-Content-Type-Options", "nosniff")
            self.send_header("Referrer-Policy", "no-referrer")
            self.send_header(
                "Content-Security-Policy",
                "default-src 'self'; script-src 'self'; style-src 'self'; connect-src 'self'; img-src 'self'; frame-ancestors 'none'; base-uri 'none'; form-action 'self'",
            )
            if extra:
                for key, value in extra.items():
                    self.send_header(key, value)
            self.end_headers()
            try:
                self.wfile.write(inhalt)
            except (BrokenPipeError, ConnectionResetError):
                pass

        def do_GET(self):
            # Es werden nur drei feste Oberflächendateien ausgeliefert.
            # Ein beliebiger Dateipfad aus einer URL wird niemals geöffnet.
            if not self.host_ok():
                return self.senden(403, {"fehler": "Ungültige lokale Adresse."})
            dateien = {
                "/": ("index.html", "text/html; charset=utf-8"),
                "/app.js": ("app.js", "text/javascript; charset=utf-8"),
                "/stil.css": ("stil.css", "text/css; charset=utf-8"),
            }
            if self.path == "/api/status":
                return self.senden(
                    200,
                    {
                        "bereit": True,
                        "version": app.config["version"],
                        "modell": "Qwen3-4B · Q4_K_M",
                        "modell_pid": app.modell.prozess.pid if app.modell.prozess else None,
                    },
                )
            if self.path in dateien:
                datei, typ = dateien[self.path]
                text = (ROOT / "oberflaeche" / datei).read_text(encoding="utf-8")
                return self.senden(200, text.replace("__SESSION_TOKEN__", app.token), typ)
            return self.senden(404, {"fehler": "Nicht gefunden."})

        def do_POST(self):
            # Das Sitzungstoken hält fremde Webseiten von schreibenden Aktionen ab.
            # Es ersetzt keine Benutzerverwaltung für einen Mehrnutzerbetrieb.
            origin = self.headers.get("Origin")
            if (
                not self.host_ok()
                or self.headers.get("X-Session-Token") != app.token
                or origin not in (None, f'http://127.0.0.1:{app.config["oberflaeche_port"]}')
            ):
                # Kleine bereits gesendete Nutzdaten vor dem Ablehnen lesen.
                # Sonst kann Windows die Verbindung zurücksetzen, bevor die
                # verständliche 403-Antwort beim Client ankommt.
                try:
                    self.connection.settimeout(1)
                    laenge = int(self.headers.get("Content-Length", "0"))
                    if 0 < laenge <= 100000:
                        self.rfile.read(laenge)
                except (ValueError, OSError):
                    pass
                return self.senden(
                    403, {"fehler": "Nur die lokale Sitzung darf diese Aktion ausführen."}
                )
            try:
                self.connection.settimeout(5)
                laenge = int(self.headers.get("Content-Length", "0"))
                if not 0 < laenge <= 100000:
                    raise ValueError("Ungültige Anfragegröße.")
                if self.headers.get_content_type() != "application/json":
                    raise ValueError("JSON-Eingabe erforderlich.")
                daten = json.loads(self.rfile.read(laenge))
                if not isinstance(daten, dict):
                    raise ValueError("JSON-Objekt erforderlich.")
                if self.path == "/api/translate":
                    return self.senden(200, app.uebersetzen(daten))
                if self.path in ("/api/reset", "/api/cancel"):
                    app.zuruecksetzen()
                    return self.senden(200, {"status": "Verworfen"})
                if self.path in ("/api/update", "/api/approve", "/api/export"):
                    ergebnis = app.sitzung.bearbeiten(daten, freigabe=self.path == "/api/approve")
                    return self.senden(200, ergebnis)
                if self.path == "/api/shutdown":
                    app.zuruecksetzen()
                    app.modell.stoppen()
                    self.senden(200, {"status": "Beendet"})
                    # shutdown darf nicht im Thread von serve_forever warten.
                    threading.Thread(target=self.server.shutdown, daemon=True).start()
                    return
                return self.senden(404, {"fehler": "Unbekannte Aktion."})
            except (ValueError, KeyError, TypeError, TimeoutError) as exc:
                return self.senden(400, {"fehler": str(exc)})

    return Handler


def main():
    """Mitgelieferte Konfiguration laden, lokal starten und beim Ende aufräumen."""
    parser = argparse.ArgumentParser()
    parser.add_argument("--ohne-browser", action="store_true")
    # Alternative lokale Ports erlauben eine getrennte Testinstanz.
    parser.add_argument("--port", type=int)
    parser.add_argument("--modell-port", type=int)
    args = parser.parse_args()
    config = json.loads((ROOT / "konfiguration.json").read_text(encoding="utf-8"))
    if args.port is not None:
        config["oberflaeche_port"] = args.port
    if args.modell_port is not None:
        config["modell_port"] = args.modell_port
    for name in ("oberflaeche_port", "modell_port"):
        if not 1024 <= config[name] <= 65535:
            raise SystemExit("Lokale Ports müssen zwischen 1024 und 65535 liegen.")
    if config["oberflaeche_port"] == config["modell_port"]:
        raise SystemExit("Oberfläche und Modellserver benötigen unterschiedliche Ports.")
    app = Anwendung(config)
    adresse = ("127.0.0.1", config["oberflaeche_port"])
    try:
        server = ThreadingHTTPServer(adresse, handler_fuer(app))
    except OSError:
        raise SystemExit(f"Port {adresse[1]} ist belegt. Bestehende Instanz schließen.")
    server.daemon_threads = True
    print(f"Lokaler Übersetzungsassistent: http://{adresse[0]}:{adresse[1]}", flush=True)
    print("Beenden über die Oberfläche oder Strg+C. Nur synthetische Daten verwenden.", flush=True)
    if not args.ohne_browser:
        webbrowser.open(f"http://{adresse[0]}:{adresse[1]}")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        app.zuruecksetzen()
        app.modell.stoppen()
        server.server_close()


if __name__ == "__main__":
    main()
