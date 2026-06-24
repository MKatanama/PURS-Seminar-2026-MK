from datetime import datetime
import json
import time

import MySQLdb
from flask import Flask, g, redirect, render_template, request, session, url_for

from instrument import (
    iskljuci_lampu,
    ocitaj_ccd,
    ocitaj_temperaturu,
    pomakni_na_kivetu,
    pripremi_mehatroniku,
    provjeri_vrata,
    ukljuci_lampu,
)


app = Flask("Spektrofotometar")
app.secret_key = "purs_spektrofotometar"


BAZA_HOST = "localhost"
BAZA_USER = "app"
BAZA_PASSWORD = "1234"
BAZA_NAME = "spektrofotometar"


@app.before_request
def prije_zahtjeva():
    if request.path.startswith("/static"):
        return

    g.connection = MySQLdb.connect(
        host=BAZA_HOST,
        user=BAZA_USER,
        passwd=BAZA_PASSWORD,
        db=BAZA_NAME,
        charset="utf8mb4",
    )
    g.cursor = g.connection.cursor()

    if request.path == "/login":
        return

    if session.get("username") is None:
        return redirect(url_for("login_stranica"))


@app.after_request
def poslije_zahtjeva(response):
    if hasattr(g, "connection"):
        g.connection.commit()
        g.cursor.close()
        g.connection.close()

    return response


@app.get("/")
def pocetna_stranica():
    return render_template("index.html", title="Pocetna stranica")


@app.get("/login")
def login_stranica():
    return render_template("login.html", title="Prijava")


@app.post("/login")
def login():
    username = request.form.get("username")
    password = request.form.get("password")

    korisnik = dohvati_korisnika(username, password)

    if korisnik is not None:
        session["username"] = korisnik["username"]
        session["ime"] = korisnik["ime"]
        session["prezime"] = korisnik["prezime"]
        return redirect(url_for("pocetna_stranica"))

    return render_template(
        "login.html",
        title="Prijava",
        greska="Uneseni su pogresni podatci",
    )


@app.get("/logout")
def logout():
    session.pop("username", None)
    session.pop("ime", None)
    session.pop("prezime", None)
    return redirect(url_for("login_stranica"))


@app.post("/mjerenje")
def pokreni_mjerenje():
    broj_kivete = int(request.form.get("broj_kivete"))

    mehatronika = pripremi_mehatroniku()
    try:
        provjeri_vrata(mehatronika)
        pomakni_na_kivetu(mehatronika, broj_kivete)
        temperatura = ocitaj_temperaturu(mehatronika)
        ukljuci_lampu(mehatronika)
        time.sleep(5)
        ccd_podaci = ocitaj_ccd()
    finally:
        try:
            iskljuci_lampu(mehatronika)
        except Exception:
            pass
        mehatronika.close()

    datum_vrijeme = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    spremi_mjerenje(
        session.get("ime"),
        session.get("prezime"),
        datum_vrijeme,
        temperatura,
        broj_kivete,
        ccd_podaci,
    )

    return redirect(url_for("prikazi_mjerenja"))


@app.get("/mjerenja")
def prikazi_mjerenja():
    return render_template(
        "mjerenja.html",
        title="Mjerenja",
        mjerenja=dohvati_mjerenja(),
    )


@app.get("/korisnici")
def prikazi_korisnike():
    return render_template(
        "korisnici.html",
        title="Korisnici",
        korisnici=dohvati_korisnike(),
    )


def dohvati_korisnika(username, password):
    upit = """
        SELECT id, username, ime, prezime
        FROM korisnik
        WHERE username = %s AND password = %s
    """
    g.cursor.execute(upit, (username, password))
    redak = g.cursor.fetchone()

    if redak is None:
        return None

    return {
        "id": redak[0],
        "username": redak[1],
        "ime": redak[2],
        "prezime": redak[3],
    }


def dohvati_korisnike():
    upit = """
        SELECT id, username, ime, prezime
        FROM korisnik
        ORDER BY id
    """
    g.cursor.execute(upit)
    retci = g.cursor.fetchall()

    korisnici = []
    for redak in retci:
        korisnici.append(
            {
                "id": redak[0],
                "username": redak[1],
                "ime": redak[2],
                "prezime": redak[3],
            }
        )

    return korisnici


def spremi_mjerenje(
    ime_operatera,
    prezime_operatera,
    datum_vrijeme,
    temperatura,
    broj_kivete,
    ccd_podaci,
):
    upit = """
        INSERT INTO mjerenje
        (ime_operatera, prezime_operatera, datum_vrijeme, temperatura, broj_kivete, ccd_podaci)
        VALUES (%s, %s, %s, %s, %s, %s)
    """
    g.cursor.execute(
        upit,
        (
            ime_operatera,
            prezime_operatera,
            datum_vrijeme,
            temperatura,
            broj_kivete,
            json.dumps(ccd_podaci),
        ),
    )


def dohvati_mjerenja():
    upit = """
        SELECT id, ime_operatera, prezime_operatera, datum_vrijeme, temperatura, broj_kivete, ccd_podaci
        FROM mjerenje
        ORDER BY id DESC
    """
    g.cursor.execute(upit)
    retci = g.cursor.fetchall()

    mjerenja = []
    for redak in retci:
        ccd_podaci = json.loads(redak[6])
        mjerenja.append(
            {
                "id": redak[0],
                "ime_operatera": redak[1],
                "prezime_operatera": redak[2],
                "datum_vrijeme": redak[3],
                "temperatura": redak[4],
                "broj_kivete": redak[5],
                "broj_ccd_vrijednosti": len(ccd_podaci),
            }
        )

    return mjerenja


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)
