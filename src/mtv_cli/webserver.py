#!/usr/bin/env python3
# Mediathekview auf der Kommandozeile (Webinterface)
#
# Einfaches Webinterface auf Basis von Bottle
#
# Author: Bernhard Bablok, Max Görner
# License: GPL3
#
# Website: https://github.com/bablokb/mtv_cli
#


import configparser
import json
import os
import subprocess
from argparse import ArgumentParser
from multiprocessing import Process
from pathlib import Path
from typing import Optional

import bottle
from bottle import route
from loguru import logger

from mtv_cli import cli
from mtv_cli.constants import FILME_SQLITE, MTV_CLI_HOME
from mtv_cli.content_retrieval import LowMemoryFileSystemDownloader
from mtv_cli.storage_backend import FilmDB


class Options:
    pass


def get_webroot(pgm):
    pgm_dir = os.path.dirname(os.path.realpath(pgm))
    return os.path.realpath(os.path.join(pgm_dir, "..", "lib", "mtv_cli", "web"))


def get_webpath(path: str) -> Path:
    return WEB_ROOT / path


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


@route("/")
def main_page():
    tpl = bottle.SimpleTemplate(name="index.html", lookup=[WEB_ROOT])
    return tpl.render()


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
    logger.debug("Status: " + str(result))
    bottle.response.content_type = "application/json"
    return json.dumps(result)


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
    logger.debug("Suchbegriffe: " + str(such_args))

    # Film-DB abfragen
    filmDB: FilmDB = options.filmDB
    filme = list(filmDB.finde_filme(such_args))
    response = [film.dict() for film in filme]
    logger.debug("Anzahl Treffer: %d" % len(filme))
    bottle.response.content_type = "application/json"
    return json.dumps(response)


@route("/downloads", method="POST")
def downloads():
    # Film-DB abfragen
    rows = options.filmDB.read_downloads()
    if not rows:
        logger.debug("Keine vorgemerkten Filme vorhanden")
        return "{}"

    # Liste aufbereiten
    result = []
    for row in rows:
        item = {}
        item["DATUM"] = row["DATUM"].strftime("%d.%m.%y")
        item["DATUMSTATUS"] = row["DATUMSTATUS"].strftime("%d.%m.%y")
        for key in ["STATUS", "SENDER", "THEMA", "TITEL", "DAUER"]:
            item[key] = row[key]
        result.append(item)

    logger.debug("Anzahl Einträge in Downloadliste: %d" % len(result))
    bottle.response.content_type = "application/json"
    return json.dumps(result)


@route("/dateien", method="POST")
def dateien():
    # Film-DB abfragen
    filmDB: FilmDB = options.filmDB
    rows = filmDB.read_recs()
    if not rows:
        logger.debug("Keine Dateien gefunden")
        return "{[]}"

    # Liste aufbereiten
    result = []
    deleted = []
    for row in rows:
        dateiname = Path(row["DATEINAME"])
        if not dateiname.exists():
            logger.warning("Datei %s existiert nicht" % dateiname)
            deleted.append((dateiname,))
            continue

        item = {}
        item["DATEI"] = dateiname.name
        item["DATUMFILM"] = row["DATUMFILM"].strftime("%d.%m.%y")
        item["DATUMDATEI"] = row["DATUMDATEI"].strftime("%d.%m.%y")
        for key in ["SENDER", "TITEL", "BESCHREIBUNG", "DATEINAME"]:
            item[key] = row[key]
        result.append(item)

    # Löschen nicht mehr vorhandener Dateien
    if deleted:
        logger.debug("Lösche %d Einträge in Aufnahmelisteliste" % len(deleted))
        options.filmDB.delete_recs(deleted)

    # Ergebnis ausliefern
    logger.debug("Anzahl Einträge in Dateilisteliste: %d" % len(result))
    bottle.response.content_type = "application/json"
    return json.dumps(result)


@route("/del_datei", method="POST")
def del_datei():
    """Datei löschen"""

    maybe_dateiname: Optional[str] = bottle.request.forms.getunicode("name")
    if maybe_dateiname is None:
        msg = '"kein Dateiname angegeben"'
        bottle.response.status = 400  # bad request
        return '{"msg": ' + msg + "}"

    dateiname = Path(maybe_dateiname)
    logger.debug("Löschanforderung (Dateiname: %s)" % dateiname)

    bottle.response.content_type = "application/json"

    # Datei in der Aufname-DB suchen und dann löschen
    filmDB: FilmDB = options.filmDB
    rows = filmDB.read_recs(dateiname)
    if not rows:
        logger.warning("Dateiname %s nicht in Film-DB" % dateiname)
        msg = '"Ungültiger Dateiname"'
        bottle.response.status = 400  # bad request
    elif dateiname.exists():
        dateiname.unlink()
        filmDB.delete_recs([(dateiname,)])
        msg = '"Datei erfolgreich gelöscht"'
        bottle.response.status = 200  # OK
        logger.info("Dateiname %s gelöscht" % dateiname)
    else:
        msg = '"Datei existiert nicht"'
        bottle.response.status = 400  # bad request
        logger.warning("Dateiname %s existiert nicht" % dateiname)

    return '{"msg": ' + msg + "}"


@route("/get_datei", method="GET")
def get_datei():
    """Datei herunterladen"""

    # get name-parameter
    maybe_dateiname: Optional[str] = bottle.request.query.getunicode("name")
    logger.debug("Downloadanforderung (Dateiname: %s)" % maybe_dateiname)
    bottle.response.content_type = "application/json"

    if maybe_dateiname is None:
        msg = '"kein Dateiname angegeben"'
        bottle.response.status = 400  # bad request
        return '{"msg": ' + msg + "}"
    dateiname = Path(maybe_dateiname)

    # Überprüfen, ob Dateiname in Film-DB existiert
    filmDB: FilmDB = options.filmDB
    rows = filmDB.read_recs(dateiname)
    if not rows:
        logger.warning("Dateiname %s nicht in Film-DB" % dateiname)
        msg = '"Ungültiger Dateiname"'
        bottle.response.status = 400  # bad request
        return '{"msg": ' + msg + "}"

    if not dateiname.exists():
        msg = '"Dateiname existiert nicht"'
        bottle.response.status = 404  # not found
        return '{"msg": ' + msg + "}"

    # Datei roh herunterladen
    bottle.response.content_type = "application/mp4"
    f = f'"{dateiname.name}"'
    bottle.response.set_header("Content-Disposition", "attachment; filename=%s" % f)
    return subprocess.check_output(["cat", dateiname])


@route("/vormerken", method="POST")
def vormerken():
    # Auslesen Request-Parameter
    ids = bottle.request.forms.get("ids").split(" ")
    dates = bottle.request.forms.get("dates").split(" ")
    logger.debug("IDs: " + str(ids))
    logger.debug("Datum: " + str(dates))

    inserts = []
    i = 0
    for id in ids:
        inserts.append((id, dates[i], "V"))
        i += 1
    logger.debug("inserts: " + str(inserts))
    changes = options.filmDB.save_downloads(inserts)
    logger.debug("changes: " + str(changes))

    bottle.response.content_type = "application/json"
    msg = '"%d von %d Filme vorgemerkt für den Download"' % (changes, len(ids))
    return '{"msg": ' + msg + "}"


@route("/aktualisieren", method="GET")
def aktualisieren():
    p = Process(target=cli.do_update, args=(options,))
    p.start()
    bottle.response.content_type = "application/json"
    return '{"msg": "Aktualisierung angestoßen"}'


@route("/download", method="GET")
def download():
    retriever = LowMemoryFileSystemDownloader(
        root=Path("~/Videos").expanduser(),
        quality="HD",
    )
    p = Process(target=cli.do_download, args=(options, retriever))
    p.start()
    bottle.response.content_type = "application/json"
    return '{"msg": "Download angestoßen (Qualität: HD)"}'


@route("/loeschen", method="POST")
def loeschen():
    # Auslesen Request-Parameter
    ids = bottle.request.forms.get("ids").split(" ")
    logger.debug("IDs: " + str(ids))

    if len(ids):
        # delete_downloads braucht Array von Tuplen
        changes = options.filmDB.delete_downloads([(id,) for id in ids])
    else:
        changes = 0
    logger.info("%d vorgemerkte Filme gelöscht" % changes)

    bottle.response.content_type = "application/json"
    msg = '"%d vorgemerkte Filme gelöscht"' % changes
    return '{"msg": ' + msg + "}"


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


def get_config(parser, config):
    if parser.has_section("WEB"):
        config["PORT"] = parser.getint("WEB", "PORT")
        config["HOST"] = parser.get("WEB", "HOST")
    else:
        config["PORT"] = 8026
        config["HOST"] = "0.0.0.0"


def main() -> None:
    # Konfiguration lesen
    config_parser = configparser.RawConfigParser()
    config_parser.read("/etc/mtv_cli.conf")
    config = cli.get_config(config_parser)
    get_config(config_parser, config)

    # Optionen lesen
    opt_parser = get_parser()
    options = opt_parser.parse_args(namespace=Options)

    # Message-Klasse konfigurieren
    log_level = options.level if options.level else config["MSG_LEVEL"]
    logger.level(log_level)

    # Verzeichnis HOME/.mediathek3 anlegen
    MTV_CLI_HOME.mkdir(exist_ok=True, parents=True)

    # Globale Objekte anlegen
    options.upd_src = "auto"
    options.config = config
    options.filmDB = FilmDB(options.dbfile)

    # Server starten
    WEB_ROOT = Path(get_webroot(__file__))
    logger.debug("Web-Root Verzeichnis: %s" % WEB_ROOT)
    if log_level == "DEBUG":
        logger.debug("Starte den Webserver im Debug-Modus")
        bottle.run(host="localhost", port=config["PORT"], debug=True, reloader=True)
    else:
        bottle.run(
            host=config["HOST"], port=config["PORT"], debug=False, reloader=False
        )


if __name__ == "__main__":
    main()
