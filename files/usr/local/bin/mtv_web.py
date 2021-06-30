#!/usr/bin/python3
# -*- coding: utf-8 -*-
# ---------------------------------------------------------------------------
# Mediathekview auf der Kommandozeile (Webinterface)
#
# Einfaches Webinterface auf Basis von Bottle
#
# Author: Bernhard Bablok
# License: GPL3
#
# Website: https://github.com/bablokb/mtv_cli
#
# ---------------------------------------------------------------------------

# --- System-Imports   ------------------------------------------------------

import os, json, subprocess
from argparse import ArgumentParser
from multiprocessing import Process
import configparser

import bottle
from bottle import route

# --- eigene Imports   ------------------------------------------------------

import mtv_cli
from mtv_const import FILME_SQLITE, MTV_CLI_HOME
from mtv_filmdb import FilmDB as FilmDB
from mtv_msg import Msg as Msg
from mtv_download import download_filme

# --- Hilfsklasse für Optionen   --------------------------------------------


class Options(object):
    pass


# --- Webroot dynamisch bestimmen   -----------------------------------------


def get_webroot(pgm):
    pgm_dir = os.path.dirname(os.path.realpath(pgm))
    return os.path.realpath(os.path.join(pgm_dir, "..", "lib", "mtv_cli", "web"))


def get_webpath(path):
    return os.path.join(WEB_ROOT, path)


# --- Statische Routen   ----------------------------------------------------


@route("/css/<filepath:path>")
def css_pages(filepath):
    print(filepath)
    return bottle.static_file(filepath, root=get_webpath("css"))


@route("/js/<filepath:path>")
def js_pages(filepath):
    return bottle.static_file(filepath, root=get_webpath("js"))


@route("/images/<filepath:path>")
def images(filepath):
    return bottle.static_file(filepath, root=get_webpath("images"))


# --- Hauptseite   ----------------------------------------------------------


@route("/")
def main_page():
    tpl = bottle.SimpleTemplate(name="index.html", lookup=[WEB_ROOT])
    return tpl.render()


# --- Status   --------------------------------------------------------------


@route("/status")
def status():
    result = {"_akt": "00.00.0000", "_anzahl": "0"}
    try:
        rows = options.filmDB.read_status(["_akt", "_anzahl"])
        for row in rows:
            key = row["key"]
            if key == "_akt":
                tstamp = row["Zeit"].strftime("%d.%m.%Y %H:%M:%S")
                result[key] = tstamp
            else:
                text = row["text"]
                result[key] = text
    except:
        pass
    Msg.msg("DEBUG", "Status: " + str(result))
    bottle.response.content_type = "application/json"
    return json.dumps(result)


# --- Suche   ---------------------------------------------------------------


@route("/suche", method="POST")
def suche():
    # Auslesen Request-Parameter
    such_args = []
    token = bottle.request.forms.getunicode("global")
    if token:
        such_args.append(token)
    for arg in ["sender", "thema", "datum", "titel", "bechreibung"]:
        token = bottle.request.forms.getunicode(arg)
        if token:
            such_args.append(arg + ":" + token)
    Msg.msg("DEBUG", "Suchbegriffe: " + str(such_args))

    # Film-DB abfragen
    statement = options.filmDB.get_query(such_args)
    rows = options.filmDB.execute_query(statement)

    # Ergebnis aufbereiten
    result = []
    for row in rows:
        item = {}
        item["DATUM"] = row["DATUM"].strftime("%d.%m.%y")
        for key in ["SENDER", "THEMA", "TITEL", "DAUER", "BESCHREIBUNG", "_ID"]:
            item[key] = row[key]
        result.append(item)

    Msg.msg("DEBUG", "Anzahl Treffer: %d" % len(result))
    bottle.response.content_type = "application/json"
    return json.dumps(result)


# --- Downloads   -----------------------------------------------------------


@route("/downloads", method="POST")
def downloads():
    # Film-DB abfragen
    rows = options.filmDB.read_downloads()
    if not rows:
        Msg.msg("DEBUG", "Keine vorgemerkten Filme vorhanden")
        return "{}"

    # Liste aufbereiten
    result = []
    for row in rows:
        item = {}
        item["DATUM"] = row["DATUM"].strftime("%d.%m.%y")
        item["DATUMSTATUS"] = row["DATUMSTATUS"].strftime("%d.%m.%y")
        for key in ["STATUS", "SENDER", "THEMA", "TITEL", "DAUER", "_ID"]:
            item[key] = row[key]
        result.append(item)

    Msg.msg("DEBUG", "Anzahl Einträge in Downloadliste: %d" % len(result))
    bottle.response.content_type = "application/json"
    return json.dumps(result)


# --- Dateien   -------------------------------------------------------------


@route("/dateien", method="POST")
def dateien():
    # Film-DB abfragen
    rows = options.filmDB.read_recs()
    if not rows:
        Msg.msg("DEBUG", "Keine Dateien gefunden")
        return "{[]}"

    # Liste aufbereiten
    result = []
    deleted = []
    for row in rows:
        dateiname = row["DATEINAME"]
        if not os.path.exists(dateiname):
            Msg.msg("WARN", "Datei %s existiert nicht" % dateiname)
            deleted.append((dateiname,))
            continue

        item = {}
        item["DATEI"] = os.path.basename(dateiname)
        item["DATUMFILM"] = row["DATUMFILM"].strftime("%d.%m.%y")
        item["DATUMDATEI"] = row["DATUMDATEI"].strftime("%d.%m.%y")
        for key in ["SENDER", "TITEL", "BESCHREIBUNG", "DATEINAME"]:
            item[key] = row[key]
        result.append(item)

    # Löschen nicht mehr vorhandener Dateien
    if deleted:
        Msg.msg("DEBUG", "Lösche %d Einträge in Aufnahmelisteliste" % len(deleted))
        options.filmDB.delete_recs(deleted)

    # Ergebnis ausliefern
    Msg.msg("DEBUG", "Anzahl Einträge in Dateilisteliste: %d" % len(result))
    bottle.response.content_type = "application/json"
    return json.dumps(result)


# --- Datei löschen   -------------------------------------------------------


@route("/del_datei", method="POST")
def del_datei():
    """Datei löschen"""

    # get name-parameter
    dateiname = bottle.request.forms.getunicode("name")
    Msg.msg("DEBUG", "Löschanforderung (Dateiname: %s)" % dateiname)

    bottle.response.content_type = "application/json"

    if dateiname is None:
        msg = '"kein Dateiname angegeben"'
        bottle.response.status = 400  # bad request
        return '{"msg": ' + msg + "}"

    # Datei in der Aufname-DB suchen und dann löschen
    rows = options.filmDB.read_recs(dateiname)
    if not rows:
        Msg.msg("WARN", "Dateiname %s nicht in Film-DB" % dateiname)
        msg = '"Ungültiger Dateiname"'
        bottle.response.status = 400  # bad request
    elif os.path.exists(dateiname):
        os.unlink(dateiname)
        options.filmDB.delete_recs([(dateiname,)])
        msg = '"Datei erfolgreich gelöscht"'
        bottle.response.status = 200  # OK
        Msg.msg("INFO", "Dateiname %s gelöscht" % dateiname)
    else:
        msg = '"Datei existiert nicht"'
        bottle.response.status = 400  # bad request
        Msg.msg("WARN", "Dateiname %s existiert nicht" % dateiname)

    return '{"msg": ' + msg + "}"


# --- Datei herunterladen   -------------------------------------------------


@route("/get_datei", method="GET")
def get_datei():
    """Datei herunterladen"""

    # get name-parameter
    dateiname = bottle.request.query.getunicode("name")
    Msg.msg("DEBUG", "Downloadanforderung (Dateiname: %s)" % dateiname)

    bottle.response.content_type = "application/json"

    if dateiname is None:
        msg = '"kein Dateiname angegeben"'
        bottle.response.status = 400  # bad request
        return '{"msg": ' + msg + "}"

    # Überprüfen, ob Dateiname in Film-DB existiert
    rows = options.filmDB.read_recs(dateiname)
    if not rows:
        Msg.msg("WARN", "Dateiname %s nicht in Film-DB" % dateiname)
        msg = '"Ungültiger Dateiname"'
        bottle.response.status = 400  # bad request
        return '{"msg": ' + msg + "}"

    if not os.path.exists(dateiname):
        msg = '"Dateiname existiert nicht"'
        bottle.response.status = 404  # not found
        return '{"msg": ' + msg + "}"

    # Datei roh herunterladen
    bottle.response.content_type = "application/mp4"
    f = '"' + os.path.basename(dateiname) + '"'
    bottle.response.set_header("Content-Disposition", "attachment; filename=%s" % f)
    return subprocess.check_output(["cat", dateiname])


# --- Vormerken   -----------------------------------------------------------


@route("/vormerken", method="POST")
def vormerken():
    # Auslesen Request-Parameter
    ids = bottle.request.forms.get("ids").split(" ")
    dates = bottle.request.forms.get("dates").split(" ")
    Msg.msg("DEBUG", "IDs: " + str(ids))
    Msg.msg("DEBUG", "Datum: " + str(dates))

    inserts = []
    i = 0
    for id in ids:
        inserts.append((id, dates[i], "V"))
        i += 1
    Msg.msg("DEBUG", "inserts: " + str(inserts))
    changes = options.filmDB.save_downloads(inserts)
    Msg.msg("DEBUG", "changes: " + str(changes))

    bottle.response.content_type = "application/json"
    msg = '"%d von %d Filme vorgemerkt für den Download"' % (changes, len(ids))
    return '{"msg": ' + msg + "}"


# --- Aktualisieren   -------------------------------------------------------


@route("/aktualisieren", method="GET")
def aktualisieren():
    p = Process(target=mtv_cli.do_update, args=(options,))
    p.start()
    bottle.response.content_type = "application/json"
    return '{"msg": "Aktualisierung angestoßen"}'


# --- Download   ------------------------------------------------------------


@route("/download", method="GET")
def download():
    p = Process(target=download_filme, args=(options,))
    p.start()
    bottle.response.content_type = "application/json"
    return '{"msg": "Download angestoßen"}'


# --- Vorgemerkte Downloads löschen   ---------------------------------------


@route("/loeschen", method="POST")
def loeschen():
    # Auslesen Request-Parameter
    ids = bottle.request.forms.get("ids").split(" ")
    Msg.msg("DEBUG", "IDs: " + str(ids))

    if len(ids):
        # delete_downloads braucht Array von Tuplen
        changes = options.filmDB.delete_downloads([(id,) for id in ids])
    else:
        changes = 0
    Msg.msg("INFO", "%d vorgemerkte Filme gelöscht" % changes)

    bottle.response.content_type = "application/json"
    msg = '"%d vorgemerkte Filme gelöscht"' % changes
    return '{"msg": ' + msg + "}"


# --- Kommandozeilenparser   ------------------------------------------------


def get_parser():
    parser = ArgumentParser(
        add_help=False,
        description="Simpler Webserver für Mediathekview auf der Kommandozeile",
    )

    parser.add_argument(
        "-d",
        "--db",
        metavar="Datei",
        dest="dbfile",
        default=FILME_SQLITE,
        help="Datenbankdatei",
    )
    parser.add_argument(
        "-l",
        "--level",
        metavar="Log-Level",
        dest="level",
        default=None,
        help="Meldungen ab angegebenen Level ausgeben",
    )
    parser.add_argument("-h", "--hilfe", action="help", help="Diese Hilfe ausgeben")
    return parser


# --- Konfiguration auslesen (mtv_web spezifisch)   -------------------------


def get_config(parser, config):
    if parser.has_section("WEB"):
        config["PORT"] = parser.getint("WEB", "PORT")
        config["HOST"] = parser.get("WEB", "HOST")
    else:
        config["PORT"] = 8026
        config["HOST"] = "0.0.0.0"


# --- Hauptprogramm   -------------------------------------------------------

if __name__ == "__main__":
    # Konfiguration lesen
    config_parser = configparser.RawConfigParser()
    config_parser.read("/etc/mtv_cli.conf")
    config = mtv_cli.get_config(config_parser)
    get_config(config_parser, config)

    # Optionen lesen
    opt_parser = get_parser()
    options = opt_parser.parse_args(namespace=Options)

    # Message-Klasse konfigurieren
    if options.level:
        Msg.level = options.level
    else:
        Msg.level = config["MSG_LEVEL"]

    # Verzeichnis HOME/.mediathek3 anlegen
    if not os.path.exists(MTV_CLI_HOME):
        os.mkdir(MTV_CLI_HOME)

    # Globale Objekte anlegen
    options.upd_src = "auto"
    options.config = config
    options.filmDB = FilmDB(options)

    # Server starten
    WEB_ROOT = get_webroot(__file__)
    Msg.msg("DEBUG", "Web-Root Verzeichnis: %s" % WEB_ROOT)
    if Msg.level == "DEBUG":
        Msg.msg("DEBUG", "Starte den Webserver im Debug-Modus")
        bottle.run(host="localhost", port=config["PORT"], debug=True, reloader=True)
    else:
        bottle.run(
            host=config["HOST"], port=config["PORT"], debug=False, reloader=False
        )
