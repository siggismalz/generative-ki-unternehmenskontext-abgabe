"""Lokaler Übersetzungskern ohne zusätzliche Python-Pakete.

Die Funktionen prüfen Eingaben und Ausgaben. Modell verwaltet den eigenen
llama.cpp-Prozess. Sitzung hält Original, Rohtext, Korrektur und Freigabe im RAM.
"""

from collections import Counter
from datetime import datetime, timezone
from decimal import Decimal, InvalidOperation
from pathlib import Path
import hashlib
import json
import os
import re
import secrets
import socket
import subprocess
import threading
import time
import urllib.error
import urllib.request

ROOT = Path(__file__).resolve().parent
SPRACHEN = {"DE-EN": ("German", "English"), "EN-DE": ("English", "German")}
TEXTSORTEN = ("Kundenanfrage", "Serviceantwort", "Produktkurztext")


def zeitpunkt():
    """UTC-Zeit mit Zeitzone verwenden, damit Exporte vergleichbar bleiben."""
    return datetime.now(timezone.utc).isoformat()


def validieren(daten):
    """Ungültige Eingaben ablehnen, bevor das Modell Rechenzeit benötigt."""
    if not isinstance(daten, dict):
        raise ValueError("Die Eingabe muss ein Objekt sein.")
    text = daten.get("text")
    if not isinstance(text, str) or not text.strip() or len(text) > 2000:
        raise ValueError("Bitte 1 bis 2.000 Zeichen eingeben. Leere Texte sind nicht zulässig.")
    if daten.get("richtung") not in SPRACHEN:
        raise ValueError("Nur Deutsch nach Englisch und Englisch nach Deutsch sind verfügbar.")
    if daten.get("textsorte") not in TEXTSORTEN:
        raise ValueError("Bitte eine der drei Textsorten wählen.")
    if daten.get("prompt") not in ("basis-v1", "handel-v2"):
        raise ValueError("Unbekannte Promptversion.")
    fall = daten.get("fall_id", "")
    if not isinstance(fall, str) or not re.fullmatch(r"[A-Za-z0-9_-]{1,40}", fall):
        raise ValueError(
            "Die Fall-ID benötigt 1 bis 40 Buchstaben, Ziffern, Bindestriche oder Unterstriche."
        )
    glossar = daten.get("glossar", [])
    if not isinstance(glossar, list) or len(glossar) > 20:
        raise ValueError("Das Glossar darf höchstens 20 Einträge enthalten.")
    for eintrag in glossar:
        if not isinstance(eintrag, dict) or set(eintrag) != {"quelle", "ziel"}:
            raise ValueError("Jeder Glossareintrag benötigt quelle und ziel.")
        for begriff in eintrag.values():
            if not isinstance(begriff, str) or not begriff.strip() or len(begriff) > 80:
                raise ValueError("Glossarbegriffe benötigen jeweils 1 bis 80 Zeichen.")
    # Nur diese Felder weitergeben: keine nutzerbestimmte Systemanweisung
    # und keine frei wählbare Serveradresse.
    return {
        "text": text,
        "richtung": daten["richtung"],
        "textsorte": daten["textsorte"],
        "prompt": daten["prompt"],
        "fall_id": fall,
        "glossar": glossar,
    }


def nachrichten(daten):
    """Feste Übersetzungsanweisung und Quelldaten getrennt übergeben."""
    quelle, ziel = SPRACHEN[daten["richtung"]]
    prompts = json.loads((ROOT / "prompts.json").read_text(encoding="utf-8"))
    # Nur die beiden Sprachfelder ersetzen. Geschweifte Platzhalter wie
    # {{ORDER_ID}} müssen in der Anweisung unverändert erhalten bleiben.
    system = prompts[daten["prompt"]].replace("{quelle}", quelle).replace("{ziel}", ziel)
    inhalt = json.dumps(
        {
            "source_text": daten["text"],
            "text_type": daten["textsorte"],
            "glossary": daten["glossar"],
        },
        ensure_ascii=False,
    )
    return [{"role": "system", "content": system}, {"role": "user", "content": inhalt}]


def zahlen(text):
    """Ziffernfolgen zählen; 19,90 und 19.90 dabei gleich behandeln.

    Counter erhält die Häufigkeiten. Tausender- und Datumsformate können
    mehrdeutig bleiben und benötigen weiterhin eine menschliche Prüfung.
    """
    result = []
    for wert in re.findall(r"(?<![\w])\d+(?:[.,]\d+)*(?![\w])", text):
        wert = wert.replace(" ", "")
        if "," in wert and "." in wert:
            dezimal = "," if wert.rfind(",") > wert.rfind(".") else "."
            wert = wert.replace("." if dezimal == "," else ",", "").replace(dezimal, ".")
        elif "," in wert:
            wert = wert.replace(",", ".")
        try:
            result.append(str(Decimal(wert).normalize()))
        except InvalidOperation:
            result.append(wert)
    return Counter(result)


def auffaelligkeiten(original, entwurf):
    """Nur einfache Abweichungen erkennen, keine vollständige Sprachprüfung."""
    hinweise = []
    if zahlen(original) != zahlen(entwurf):
        hinweise.append(
            "Zahlen unterscheiden sich. Beträge, Mengen und Datumsangaben manuell prüfen."
        )
    muster = r"\{\{[^{}]+\}\}|\{[A-Za-z_][A-Za-z0-9_]*\}"
    if Counter(re.findall(muster, original)) != Counter(re.findall(muster, entwurf)):
        hinweise.append("Platzhalter fehlen, wurden hinzugefügt oder verändert.")
    ids = r"\b[A-Z]{1,8}-\d+[A-Z0-9-]*\b"
    if Counter(re.findall(ids, original)) != Counter(re.findall(ids, entwurf)):
        hinweise.append("Kennungen wie Bestell- oder Produkt-IDs unterscheiden sich.")
    return hinweise


def ausgabe_pruefen(antwort):
    """Abgebrochene, unvollständige oder erkennbare Denkausgaben sperren."""
    try:
        choice = antwort["choices"][0]
        message = choice["message"]
        text = message.get("content")
    except (KeyError, IndexError, TypeError, AttributeError) as fehler:
        raise ValueError("Der Modellserver hat eine unvollständige Antwort geliefert.") from fehler
    if choice.get("finish_reason") != "stop":
        raise ValueError(
            "Die Modellausgabe wurde nicht regulär beendet. Bitte kürzeren Text versuchen."
        )
    if message.get("tool_calls") or message.get("reasoning_content"):
        raise ValueError("Die Ausgabe enthält Werkzeugaufrufe oder Denktext und wird gesperrt.")
    if not isinstance(text, str) or not text.strip() or len(text) > 12000:
        raise ValueError("Das Modell hat keinen verwendbaren Übersetzungsentwurf geliefert.")
    if re.search(
        r"</?think>|<\|im_start\|>|```|^(?:analysis|reasoning|translation|übersetzung)\s*:",
        text,
        re.I,
    ):
        raise ValueError(
            "Die Ausgabe enthält Denktext, Markierungen oder einen Kommentar und wird gesperrt."
        )
    return text.strip()


class Modell:
    """Nur den lokalen Modellserver starten und lokal ansprechen."""

    def __init__(self, config):
        self.config = config
        self.prozess = None
        self.schluessel = secrets.token_urlsafe(32)
        self.prozess_lock = threading.RLock()
        # Lokale Modellaufrufe sollen keinen eventuell eingerichteten Proxy nutzen.
        self.opener = urllib.request.build_opener(urllib.request.ProxyHandler({}))

    def stoppen(self):
        """Ausschließlich den eigenen Prozess beenden, keine fremde Instanz."""
        with self.prozess_lock:
            prozess = self.prozess
            self.prozess = None
            if prozess and prozess.poll() is None:
                prozess.terminate()
                try:
                    prozess.wait(timeout=3)
                except subprocess.TimeoutExpired:
                    prozess.kill()
                    prozess.wait(timeout=3)

    def starten(self, abbruch, ende):
        """Das Modell beim ersten Aufruf laden und auf Bereitschaft warten."""
        with self.prozess_lock:
            if not self.prozess or self.prozess.poll() is not None:
                if abbruch.is_set():
                    raise ValueError("Die Übersetzung wurde abgebrochen.")
                exe = ROOT / "laufzeit" / "llama" / "llama-server.exe"
                modell = ROOT / self.config["modell_datei"]
                if not exe.is_file() or not modell.is_file():
                    raise ValueError(
                        "Modell oder llama-Laufzeit fehlt. Bitte zuerst Einrichten.cmd ausführen."
                    )
                port = self.config["modell_port"]
                with socket.socket() as probe:
                    try:
                        probe.bind(("127.0.0.1", port))
                    except OSError as exc:
                        raise ValueError(
                            f"Modellport {port} ist belegt. Andere Instanz schließen."
                        ) from exc
                # Lokale Modelldatei, CPU-Betrieb und keine Agentenwerkzeuge.
                # Der Schlüssel wird pro Programmstart neu erzeugt.
                argumente = [
                    str(exe),
                    "-m",
                    str(modell),
                    "--host",
                    "127.0.0.1",
                    "--port",
                    str(port),
                    "-t",
                    str(self.config["threads"]),
                    "-tb",
                    str(self.config["threads"]),
                    "-c",
                    str(self.config["kontext_tokens"]),
                    "-np",
                    "1",
                    "-ngl",
                    "0",
                    "--cache-ram",
                    "0",
                    "--no-cache-idle-slots",
                    "--no-context-shift",
                    "--no-webui",
                    "--no-slots",
                    "--log-disable",
                    "--no-agent",
                    "--reasoning",
                    "off",
                    "--chat-template-kwargs",
                    '{"enable_thinking":false}',
                    "--api-key",
                    self.schluessel,
                ]
                # Fremde LLAMA-Umgebungsvariablen dürfen keine Tools/Cloudwege einschalten.
                umgebung = {}
                for name, wert in os.environ.items():
                    if not name.startswith(("LLAMA_", "HF_")):
                        umgebung[name] = wert
                self.prozess = subprocess.Popen(
                    argumente,
                    cwd=exe.parent,
                    env=umgebung,
                    stdin=subprocess.DEVNULL,
                    stdout=subprocess.DEVNULL,
                    stderr=subprocess.DEVNULL,
                    creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0),
                )
        # Auch beim Laden kann der Nutzer abbrechen; das Zeitlimit läuft bereits.
        while time.monotonic() < ende and not abbruch.is_set():
            if not self.prozess or self.prozess.poll() is not None:
                raise ValueError(
                    "Der lokale Modellprozess wurde beendet. Laufzeit und freie Ressourcen prüfen."
                )
            try:
                with self.opener.open(
                    f'http://127.0.0.1:{self.config["modell_port"]}/health', timeout=0.5
                ) as response:
                    if response.status == 200:
                        return
            except (OSError, urllib.error.URLError):
                abbruch.wait(0.1)
        raise ValueError("Abbruch oder Zeitlimit beim Modellstart.")

    def uebersetzen(self, daten, abbruch):
        """Laden und Übersetzen teilen sich dieselbe maximale Laufzeit."""
        start = time.monotonic()
        ende = start + self.config["zeitlimit_sekunden"]
        timeout = threading.Event()

        def frist():
            # Der Timer beendet auch einen festhängenden Modellprozess.
            timeout.set()
            abbruch.set()
            self.stoppen()

        timer = threading.Timer(self.config["zeitlimit_sekunden"], frist)
        timer.daemon = True
        timer.start()
        try:
            self.starten(abbruch, ende)
            payload = {
                "messages": nachrichten(daten),
                "stream": False,
                "cache_prompt": False,
                "max_tokens": self.config["ausgabe_tokens"],
                "temperature": self.config["temperatur"],
                "seed": self.config["seed"],
                "top_p": 0.8,
                "top_k": 20,
                "chat_template_kwargs": {"enable_thinking": False},
            }
            request = urllib.request.Request(
                f'http://127.0.0.1:{self.config["modell_port"]}/v1/chat/completions',
                data=json.dumps(payload).encode("utf-8"),
                headers={
                    "Content-Type": "application/json",
                    "Authorization": "Bearer " + self.schluessel,
                },
            )
            with self.opener.open(request, timeout=max(0.1, ende - time.monotonic())) as response:
                antwort = json.loads(response.read(200000))
            if abbruch.is_set():
                raise ValueError("Die Übersetzung wurde abgebrochen.")
            text = ausgabe_pruefen(antwort)
            return text, round(time.monotonic() - start, 3), antwort.get("usage", {})
        except (OSError, urllib.error.URLError, KeyError, ValueError, TypeError) as exc:
            if timeout.is_set() or time.monotonic() >= ende:
                raise ValueError(
                    f'Die Übersetzung hat das Zeitlimit von {self.config["zeitlimit_sekunden"]:g} Sekunden überschritten.'
                ) from exc
            if abbruch.is_set():
                raise ValueError("Die Übersetzung wurde abgebrochen.") from exc
            if isinstance(exc, ValueError):
                raise
            raise ValueError(
                "Der lokale Modellaufruf ist fehlgeschlagen. Bitte erneut versuchen."
            ) from exc
        finally:
            timer.cancel()
            if abbruch.is_set():
                self.stoppen()


class Sitzung:
    """Ein Ergebnis im Arbeitsspeicher; Änderungen heben eine Freigabe auf."""

    def __init__(self, config):
        self.config = config
        self.ergebnis = None
        self.lock = threading.RLock()

    def leeren(self):
        """Altes Ergebnis einschließlich seiner Freigabe verwerfen."""
        with self.lock:
            self.ergebnis = None

    def anlegen(self, daten, roh, sekunden, usage):
        """Rohübersetzung einmalig übernehmen; Korrekturen bleiben getrennt."""
        with self.lock:
            prompt_sha = hashlib.sha256((ROOT / "prompts.json").read_bytes()).hexdigest()
            self.ergebnis = {
                "id": secrets.token_hex(12),
                **daten,
                "rohuebersetzung": roh,
                "korrektur": roh,
                "status": "Entwurf",
                "freigegeben_am": None,
                "erstellt_am": zeitpunkt(),
                "sekunden": sekunden,
                "tokenverbrauch": usage,
                "modell": "Qwen3-4B-Q4_K_M",
                "modell_sha256": self.config["modell_sha256"],
                "promptdatei_sha256": prompt_sha,
                "llama_build": self.config["llama_build"],
                "app_version": self.config["version"],
                "sampling": {
                    k: self.config[k]
                    for k in ("seed", "temperatur", "kontext_tokens", "ausgabe_tokens", "threads")
                },
            }
            return self.anzeigen()

    def anzeigen(self):
        """Eine Kopie mit aktuellen Zahlen- und Platzhalterhinweisen liefern."""
        if not self.ergebnis:
            raise ValueError("Kein aktueller Entwurf vorhanden. Bitte zuerst übersetzen.")
        result = dict(self.ergebnis)
        result["hinweise"] = auffaelligkeiten(result["text"], result["korrektur"])
        return result

    def bearbeiten(self, daten, freigabe=False):
        """Eine Freigabe gilt nur für genau den aktuellen Text und seine Eingaben."""
        with self.lock:
            if not self.ergebnis or daten.get("id") != self.ergebnis["id"]:
                raise ValueError("Dieser Entwurf ist nicht mehr aktuell. Bitte neu übersetzen.")
            for key in ("text", "richtung", "textsorte", "prompt", "fall_id", "glossar"):
                if daten.get(key) != self.ergebnis[key]:
                    self.leeren()
                    raise ValueError("Die Eingabe wurde geändert. Bitte neu übersetzen.")
            korrektur = daten.get("korrektur")
            if not isinstance(korrektur, str) or not korrektur.strip() or len(korrektur) > 12000:
                raise ValueError("Der Entwurf benötigt 1 bis 12.000 Zeichen.")
            # Der unveränderte Rohtext wird an keiner Stelle überschrieben.
            if korrektur != self.ergebnis["korrektur"]:
                self.ergebnis.update(korrektur=korrektur, status="Entwurf", freigegeben_am=None)
            if not freigabe and daten.get("geprueft") is False:
                self.ergebnis.update(status="Entwurf", freigegeben_am=None)
            if freigabe:
                if daten.get("geprueft") is not True:
                    raise ValueError("Bitte die menschliche Prüfung bewusst bestätigen.")
                self.ergebnis.update(status="Freigegeben", freigegeben_am=zeitpunkt())
            return self.anzeigen()
