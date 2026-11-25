"use strict";

// Alle Texte bleiben in der aktuellen Sitzung. Erst der Export lädt eine Datei herunter.
const feld = (id) => document.getElementById(id);
const token = document.querySelector('meta[name="session-token"]').content;
const eingabeFelder = ["text", "richtung", "textsorte", "fall_id", "glossar", "prompt", "beispiel"];

let ergebnis = null;
let beschaeftigt = false;
let uebersetzungLaeuft = false;
let beendet = false;
let anfrageNummer = 0;

// Korrekturen werden der Reihe nach gespeichert. Freigabe und Export warten darauf.
// Dadurch kann eine ältere, langsame Antwort keine neue Freigabe rückgängig machen.
let letzteSpeicherung = Promise.resolve();
let letzteRuecksetzung = Promise.resolve();

async function api(pfad, daten = {}) {
    let antwort;
    try {
        antwort = await fetch(pfad, {
            method: "POST",
            headers: {
                "Content-Type": "application/json",
                "X-Session-Token": token
            },
            body: JSON.stringify(daten)
        });
    } catch (fehler) {
        throw new Error("Die lokale Anwendung ist nicht erreichbar. Bitte Starten.cmd erneut öffnen.");
    }
    const inhalt = await antwort.json();
    if (!antwort.ok) {
        throw new Error(inhalt.fehler || "Die Aktion ist fehlgeschlagen.");
    }
    return inhalt;
}

function meldung(text, istFehler = false) {
    feld("meldung").textContent = text;
    feld("meldung").classList.toggle("fehler", istFehler);
    feld("meldung").hidden = !text;
}

function eingabeLesen() {
    const glossar = [];
    for (const zeile of feld("glossar").value.split("\n")) {
        const text = zeile.trim();
        if (!text) continue;
        const trennung = text.indexOf("=");
        if (trennung < 1 || trennung === text.length - 1) {
            throw new Error("Glossar: Bitte pro Zeile Ausgangsbegriff = Zielbegriff eingeben.");
        }
        glossar.push({
            quelle: text.slice(0, trennung).trim(),
            ziel: text.slice(trennung + 1).trim()
        });
    }
    return {
        text: feld("text").value,
        richtung: feld("richtung").value,
        textsorte: feld("textsorte").value,
        fall_id: feld("fall_id").value,
        prompt: feld("prompt").value,
        glossar: glossar
    };
}

function ausgabeLesen() {
    if (!ergebnis) throw new Error("Bitte zuerst einen aktuellen Entwurf erstellen.");
    const daten = eingabeLesen();
    daten.id = ergebnis.id;
    daten.korrektur = feld("korrektur").value;
    daten.geprueft = feld("geprueft").checked;
    return daten;
}

function schalterAktualisieren() {
    for (const id of eingabeFelder) feld(id).disabled = beschaeftigt || beendet;
    feld("uebersetzen").disabled = beschaeftigt || beendet;
    feld("uebersetzen").textContent = uebersetzungLaeuft ? "Wird übersetzt …" : "Übersetzen";
    feld("abbrechen").disabled = !uebersetzungLaeuft || beendet;
    feld("abbrechen").hidden = !uebersetzungLaeuft || beendet;
    feld("leeren").disabled = beschaeftigt || beendet;
    feld("korrektur").disabled = !ergebnis || beschaeftigt || beendet;
    feld("korrektur").setAttribute("aria-busy", String(uebersetzungLaeuft));
    feld("geprueft").disabled = !ergebnis || beschaeftigt || beendet;
    feld("freigeben").disabled = !ergebnis || !feld("geprueft").checked ||
        ergebnis.status === "Freigegeben" || beschaeftigt || beendet;
    feld("exportieren").disabled = !ergebnis || beschaeftigt || beendet;
    feld("beenden").disabled = beendet;
    // Freigabe und Rohdaten werden erst dann gebraucht, wenn ein Ergebnis vorliegt.
    feld("freigabe").hidden = !ergebnis;
    feld("rohdaten").hidden = !ergebnis;
    feld("status").hidden = !ergebnis;
}

function statusZeigen(status) {
    feld("status").textContent = status;
    feld("status").classList.toggle("freigegeben", status === "Freigegeben");
}

function hinweiseZeigen(hinweise) {
    feld("warnungen").replaceChildren();
    for (const text of hinweise) {
        const absatz = document.createElement("p");
        absatz.textContent = text;
        feld("warnungen").append(absatz);
    }
    feld("warnungen").hidden = hinweise.length === 0;
}

function ergebnisZeigen(daten) {
    ergebnis = daten;
    statusZeigen(daten.status);
    feld("roh").textContent = daten.rohuebersetzung;
    feld("laufzeit").textContent = daten.sekunden.toFixed(2) + " s · " + daten.modell + " · " + daten.prompt;
    hinweiseZeigen(daten.hinweise);
    schalterAktualisieren();
}

function lokalLeeren() {
    ergebnis = null;
    feld("korrektur").value = "";
    feld("roh").textContent = "";
    feld("rohdaten").open = false;
    feld("geprueft").checked = false;
    hinweiseZeigen([]);
    statusZeigen("Noch kein Entwurf");
    feld("laufzeit").textContent = "";
    schalterAktualisieren();
}

function zaehlerAktualisieren() {
    // Wie Python zählt Array.from vollständige Unicode-Zeichen statt UTF-16-Einheiten.
    const laenge = Array.from(feld("text").value).length;
    feld("zaehler").textContent = laenge + " / 2.000";
    feld("zaehler").classList.toggle("fehler", laenge > 2000);
    feld("text").setAttribute("aria-invalid", String(laenge > 2000));
}

function eingabeGeaendert() {
    anfrageNummer += 1;
    const altesErgebnisVorhanden = ergebnis !== null || beschaeftigt;
    lokalLeeren();
    zaehlerAktualisieren();
    meldung("");
    if (altesErgebnisVorhanden) {
        letzteRuecksetzung = letzteSpeicherung
            .catch(() => {})
            .then(() => api("/api/reset"));
        letzteRuecksetzung.catch((fehler) => meldung(fehler.message, true));
    }
}

function bearbeitungSpeichern() {
    if (!ergebnis) return;
    const daten = ausgabeLesen();
    letzteSpeicherung = letzteSpeicherung
        .catch(() => {})
        .then(() => api("/api/update", daten));
    letzteSpeicherung.then((antwort) => {
        // Bei einer inzwischen neuen Eingabe sind diese Hinweise bereits veraltet.
        if (ergebnis && ergebnis.id === antwort.id && feld("korrektur").value === antwort.korrektur) {
            hinweiseZeigen(antwort.hinweise);
        }
    }).catch((fehler) => meldung(fehler.message, true));
}

for (const id of eingabeFelder) {
    if (id !== "beispiel") {
        feld(id).addEventListener("input", () => {
            // Nach manueller Bearbeitung darf kein anderes Beispiel als aktiv erscheinen.
            feld("beispiel").value = "";
            eingabeGeaendert();
        });
    }
}

feld("korrektur").addEventListener("input", () => {
    if (!ergebnis) return;
    ergebnis.status = "Entwurf";
    feld("geprueft").checked = false;
    statusZeigen("Entwurf");
    schalterAktualisieren();
    bearbeitungSpeichern();
});

feld("geprueft").addEventListener("change", () => {
    if (ergebnis && !feld("geprueft").checked) {
        ergebnis.status = "Entwurf";
        statusZeigen("Entwurf");
        bearbeitungSpeichern();
    }
    schalterAktualisieren();
});

feld("formular").addEventListener("submit", async (ereignis) => {
    ereignis.preventDefault();
    if (beschaeftigt || beendet) return;
    anfrageNummer += 1;
    const aktuelleNummer = anfrageNummer;
    lokalLeeren();
    beschaeftigt = true;
    uebersetzungLaeuft = true;
    schalterAktualisieren();
    meldung("Übersetzung läuft. Beim ersten Aufruf wird das Modell geladen.");

    try {
        await letzteRuecksetzung;
        // Eine neue Übersetzung ersetzt den alten Entwurf auch dann,
        // wenn dessen letzte (z. B. leere) Korrektur abgewiesen wurde.
        await letzteSpeicherung.catch(() => {});
        letzteSpeicherung = Promise.resolve();
        const daten = await api("/api/translate", eingabeLesen());
        if (aktuelleNummer !== anfrageNummer) return;
        feld("korrektur").value = daten.korrektur;
        ergebnisZeigen(daten);
        meldung("");
    } catch (fehler) {
        if (aktuelleNummer === anfrageNummer) {
            lokalLeeren();
            meldung(fehler.message, true);
        }
    } finally {
        beschaeftigt = false;
        uebersetzungLaeuft = false;
        schalterAktualisieren();
    }
});

feld("abbrechen").addEventListener("click", async () => {
    anfrageNummer += 1;  // Eine später eintreffende Modellausgabe wird dadurch verworfen.
    lokalLeeren();
    meldung("Übersetzung wird abgebrochen …");
    try {
        await api("/api/cancel");
        meldung("Übersetzung abgebrochen.");
    } catch (fehler) {
        meldung(fehler.message, true);
    }
});

feld("leeren").addEventListener("click", async () => {
    eingabeGeaendert();
    feld("text").value = "";
    feld("beispiel").value = "";
    zaehlerAktualisieren();
    try {
        await letzteRuecksetzung;
        meldung("Texte geleert.");
    } catch (fehler) {
        meldung(fehler.message, true);
    }
});

feld("freigeben").addEventListener("click", async () => {
    beschaeftigt = true;
    schalterAktualisieren();
    try {
        await letzteSpeicherung;
        const daten = await api("/api/approve", ausgabeLesen());
        ergebnisZeigen(daten);
        meldung("");
    } catch (fehler) {
        meldung(fehler.message, true);
    } finally {
        beschaeftigt = false;
        schalterAktualisieren();
    }
});

feld("exportieren").addEventListener("click", async () => {
    beschaeftigt = true;
    schalterAktualisieren();
    try {
        await letzteSpeicherung;
        const daten = await api("/api/export", ausgabeLesen());
        ergebnisZeigen(daten);
        const datei = new Blob([JSON.stringify(daten, null, 2)], {type: "application/json;charset=utf-8"});
        const adresse = URL.createObjectURL(datei);
        const link = document.createElement("a");
        link.href = adresse;
        link.download = daten.fall_id + "_" + daten.richtung + "_" + daten.status + ".json";
        link.click();
        setTimeout(() => URL.revokeObjectURL(adresse), 1000);
        meldung("JSON-Export heruntergeladen.");
    } catch (fehler) {
        meldung(fehler.message, true);
    } finally {
        beschaeftigt = false;
        schalterAktualisieren();
    }
});

// Das Laden eines Beispiels füllt nur die Felder. Es startet kein Modell.
feld("beispiel").addEventListener("change", async () => {
    const beispiele = {
        anfrage: {
            text: "Ist der Vorratsbehälter mit 1,5 Litern noch verfügbar? Ich benötige zwei Stück.",
            richtung: "DE-EN", textsorte: "Kundenanfrage"
        },
        service: {
            text: "Your order {{ORDER_ID}} has not been shipped yet. We will notify you when it leaves our warehouse.",
            richtung: "EN-DE", textsorte: "Serviceantwort"
        },
        produkt: {
            text: "Edelstahl-Trinkflasche mit 750 ml Fassungsvermögen. Nicht für die Spülmaschine geeignet.",
            richtung: "DE-EN", textsorte: "Produktkurztext"
        }
    };
    const beispiel = beispiele[feld("beispiel").value];
    if (!beispiel) return;
    eingabeGeaendert();
    await letzteRuecksetzung;
    feld("text").value = beispiel.text;
    feld("richtung").value = beispiel.richtung;
    feld("textsorte").value = beispiel.textsorte;
    zaehlerAktualisieren();
    meldung("Beispiel geladen.");
});

feld("beenden").addEventListener("click", async () => {
    anfrageNummer += 1;
    try {
        await api("/api/shutdown");
        beendet = true;
        lokalLeeren();
        meldung("Anwendung beendet. Dieses Fenster kann geschlossen werden.");
    } catch (fehler) {
        meldung(fehler.message, true);
    }
});

// Eine aus dem Browserverlauf wiederhergestellte Ansicht darf keinen alten Entwurf freigeben.
window.addEventListener("pageshow", (ereignis) => {
    if (ereignis.persisted) {
        lokalLeeren();
        letzteRuecksetzung = api("/api/reset");
        letzteRuecksetzung.catch((fehler) => meldung(fehler.message, true));
    }
});
schalterAktualisieren();
