#!/usr/bin/env python3
from __future__ import annotations

import configparser
import fcntl
import lzma
import os
import re
import sys
import urllib.request as request
from argparse import ArgumentParser
from typing import Iterable, Optional, TextIO

import ijson  # type: ignore[import]
from loguru import logger
from mtv_const import (
    DLL_FORMAT,
    DLL_TITEL,
    FILME_SQLITE,
    MTV_CLI_HOME,
    SEL_FORMAT,
    SEL_TITEL,
    URL_FILMLISTE,
    VERSION,
)
from mtv_download import download_filme
from mtv_filmdb import FilmDB
from mtv_filminfo import FilmlistenEintrag
from pick import pick

# Mediathekview auf der Kommandozeile
#
# Author: Bernhard Bablok, Max Görner
# License: GPL3
#
# Website: https://github.com/bablokb/mtv_cli
#


class Options:
    pass


def get_url_fp(url):
    """URL öffnen und Filepointer zurückgeben"""
    return request.urlopen(url)


def get_lzma_fp(url_fp) -> TextIO:
    """Filepointer des LZMA-Entpackers. Argument ist der FP der URL"""
    ret: TextIO = lzma.open(url_fp, "rt", encoding="utf-8")
    return ret


def extract_entries_from_filmliste(fh: TextIO) -> Iterable[FilmlistenEintrag]:
    """
    Extrahiere einzelne Einträge aus MediathekViews Filmliste

    Diese Funktion nimmt eine IO-Objekt und extrahiert aus diesem einzelne
    Filmeinträge. Es wird darauf geachtet, dabei möglichst sparsam mit dem
    Arbeitsspeicher umzugehen.
    """
    stream = ijson.parse(fh)
    start_item = ("X", "start_array", None)
    end_item = ("X", "end_array", None)
    entry_has_started = False
    last_entry: Optional[FilmlistenEintrag] = None
    for cur_item in stream:
        if cur_item == start_item:
            raw_entry: list[str] = []
            entry_has_started = True
        elif cur_item == end_item:
            entry_has_started = False
            cur_entry = FilmlistenEintrag.from_item_list(raw_entry).update(last_entry)
            last_entry = cur_entry
            yield cur_entry
        elif entry_has_started:
            raw_entry.append(cur_item[-1])


def do_update(options) -> None:
    """Update der Filmliste"""
    # TODO: Führe UpdateSource als ContextManager ein
    fh = get_update_source_file_handle(options.upd_src)
    entry_candidates = extract_entries_from_filmliste(fh)

    filmDB: FilmDB = options.filmDB
    filmDB.create_filmtable()
    filmDB.cursor.execute("BEGIN;")
    for entry in entry_candidates:
        if filmDB.is_on_ignorelist(entry):
            continue
        filmDB.insert_film(entry)
    filmDB.commit()
    filmDB.save_filmtable()

    fh.close()


def get_update_source_file_handle(update_source: str) -> TextIO:
    if update_source == "auto":
        src = URL_FILMLISTE
    elif update_source == "json":
        # existierende Filmliste verwenden
        src = os.path.join(MTV_CLI_HOME, "filme.json")
    else:
        src = update_source

    if src.startswith("http"):
        return get_lzma_fp(get_url_fp(src))
    else:
        return open(src, "r", encoding="utf-8")


def get_suche():
    suche_titel = "Auswahl Suchdetails"
    suche_opts = [
        "Weiter",
        "Global []",
        "Sender []",
        "Datum []",
        "Thema []",
        "Titel []",
        "Beschreibung []",
    ]
    while True:
        # suche_opts anzeigen
        # mit readline Suchebegriff abfragen, speichern in suche_wert
        # break, falls Auswahl "Ende"
        option, index = pick(suche_opts, suche_titel)
        if not index:
            break
        else:
            begriff = input("Suchbegriff: ")
            pos = option.find("[")
            suche_opts[index] = option[0:pos] + " [" + begriff + "]"

    # Ergebnis extrahieren
    if len(suche_opts[1]) > len("Global []"):
        return [re.split(r"\[|\]", suche_opts[1])[1]]
    else:
        result = []
        for opt in suche_opts[2:]:
            token = re.split(r"\[|\]", opt)
            if len(token[1]) > 0:
                result.append(token[0].strip() + ":" + token[1])
        return result


def get_select(rows):
    select_liste = []
    for row in rows:
        sender = row["SENDER"]
        thema = row["THEMA"]
        titel = row["TITEL"]
        datum = row["DATUM"].strftime("%d.%m.%y")
        dauer = row["DAUER"]
        select_liste.append(SEL_FORMAT.format(sender, thema, datum, dauer, titel))
    return select_liste


def filme_suchen(options):
    """Filme gemäß Vorgabe suchen"""
    if not options.suche:
        options.suche = get_suche()

    filmDB: FilmDB = options.filmDB
    statement = filmDB.get_query(options.suche)
    return filmDB.execute_query(statement)


def zeige_liste(rows):
    """Filmliste anzeigen, Auswahl zurückgeben"""
    return pick(get_select(rows), "  " + SEL_TITEL, multi_select=True)


def save_selected(filmDB, rows, selected, status):
    """Auswahl speichern"""

    # Datenstruktuer erstellen
    inserts = []
    for sel_text, sel_index in selected:
        row = rows[sel_index]
        inserts.append((row["_ID"], row["DATUM"], status))
    return filmDB.save_downloads(inserts)


def do_later(options):
    """Filmliste anzeigen, Auswahl für späteren Download speichern"""
    _do_now_later_common_body(options, do_now=False)


def do_now(options):
    """Filmliste anzeigen, sofortiger Download nach Auswahl"""

    num_changes = _do_now_later_common_body(options, do_now=True)
    if num_changes > 0:
        do_download(options)


def _do_now_later_common_body(options, do_now):
    save_selected_status, when_download_wording = (
        ("S", "Sofort-") if do_now else ("V", "Download")
    )
    rows = filme_suchen(options)
    if not rows:
        logger.info("Keine Suchtreffer")
        return 0

    if options.doBatch:
        selected = [("dummy", i) for i in range(len(rows))]
    else:
        selected = zeige_liste(rows)

    filmDB: FilmDB = options.filmDB
    num_changes = save_selected(filmDB, rows, selected, save_selected_status)
    logger.info(
        "%d von %d Filme vorgemerkt für %sDownload"
        % (num_changes, len(selected), when_download_wording),
    )
    return num_changes


def do_download(options):
    """Download vorgemerkter Filme"""
    if options.doNow:
        # Aufruf aus do_now
        download_filme(options, status="'S'")
    else:
        download_filme(options)


def do_search(options):
    """Suche ohne Download"""

    rows = filme_suchen(options)
    if rows:
        if options.doBatch:
            print("[")
            for row in rows:
                rdict = dict(row)
                if "Datum" in rdict:
                    rdict["Datum"] = rdict["Datum"].strftime("%d.%m.%y")
                print(rdict, end="")
                print(",")
            print("]")
        else:
            print(SEL_TITEL)
            print(len(SEL_TITEL) * "_")
            for row in get_select(rows):
                print(row)
        return True
    else:
        return False


def do_edit(options):
    """Downloadliste anzeigen und editieren"""

    # Liste lesen
    filmDB: FilmDB = options.filmDB
    rows = filmDB.read_downloads()
    if not rows:
        logger.info("Keine vorgemerkten Filme vorhanden")
        return

    # Liste aufbereiten
    select_liste = []
    for row in rows:
        status = row["STATUS"]
        datum_status = row["DATUMSTATUS"].strftime("%d.%m.%y")
        sender = row["SENDER"]
        thema = row["THEMA"]
        titel = row["TITEL"]
        dauer = row["DAUER"]
        datum = row["DATUM"].strftime("%d.%m.%y")

        select_liste.append(
            DLL_FORMAT.format(status, datum_status, sender, thema, datum, dauer, titel)
        )
    selected = pick(select_liste, DLL_TITEL, multi_select=True)

    # IDs extrahieren und Daten löschen
    deletes = []
    for sel_text, sel_index in selected:
        row = rows[sel_index]
        deletes.append((row["_ID"],))
    if len(deletes):
        changes = filmDB.delete_downloads(deletes)
    else:
        changes = 0
    logger.info("%d vorgemerkte Filme gelöscht" % changes)


def get_parser():
    parser = ArgumentParser(
        add_help=False, description="Mediathekview auf der Kommandozeile"
    )

    parser.add_argument(
        "-A",
        "--akt",
        metavar="Quelle",
        dest="upd_src",
        nargs="?",
        default=None,
        const="auto",
        help="Filmliste aktualisieren (Quelle: auto|json|Url|Datei)",
    )
    parser.add_argument(
        "-V",
        "--vormerken",
        action="store_true",
        dest="doLater",
        help="Filmauswahl im Vormerk-Modus",
    )
    parser.add_argument(
        "-S",
        "--sofort",
        action="store_true",
        dest="doNow",
        help="Filmauswahl im Sofort-Modus",
    )
    parser.add_argument(
        "-E",
        "--edit",
        action="store_true",
        dest="doEdit",
        help="Downloadliste bearbeiten",
    )

    parser.add_argument(
        "-D",
        "--download",
        action="store_true",
        dest="doDownload",
        help="Vorgemerkte Filme herunterladen",
    )
    parser.add_argument(
        "-Q", "--query", action="store_true", dest="doSearch", help="Filme suchen"
    )

    parser.add_argument(
        "-b",
        "--batch",
        action="store_true",
        dest="doBatch",
        help="Ausführung ohne User-Interface (zusammen mit -V, -Q und -S)",
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
        "-q",
        "--quiet",
        default=False,
        action="store_true",
        dest="quiet",
        help="Keine Meldungen ausgeben",
    )
    parser.add_argument(
        "-l",
        "--level",
        metavar="Log-Level",
        dest="level",
        default=None,
        help="Meldungen ab angegebenen Level ausgeben",
    )
    parser.add_argument(
        "--version",
        action="store_true",
        dest="doVersionInfo",
        help="Ausgabe Versionsnummer",
    )
    parser.add_argument("-h", "--hilfe", action="help", help="Diese Hilfe ausgeben")

    parser.add_argument("suche", nargs="*", metavar="Suchausdruck", help="Suchausdruck")
    return parser


def get_lock(datei):
    global fd_datei

    if not os.path.isfile(datei):
        return True

    fd_datei = open(datei, "r")
    try:
        lock = fcntl.flock(fd_datei, fcntl.LOCK_NB | fcntl.LOCK_EX)
        return True
    except IOError:
        return False


def get_config(parser):
    return {
        "MSG_LEVEL": parser.get("CONFIG", "MSG_LEVEL"),
        "DATE_CUTOFF": parser.getint("CONFIG", "DATE_CUTOFF"),
        "DAUER_CUTOFF": parser.getint("CONFIG", "DAUER_CUTOFF"),
        "NUM_DOWNLOADS": parser.getint("CONFIG", "NUM_DOWNLOADS"),
        "ZIEL_DOWNLOADS": parser.get("CONFIG", "ZIEL_DOWNLOADS"),
        "CMD_DOWNLOADS": parser.get("CONFIG", "CMD_DOWNLOADS"),
        "CMD_DOWNLOADS_M3U": parser.get("CONFIG", "CMD_DOWNLOADS_M3U"),
        "QUALITAET": parser.get("CONFIG", "QUALITAET"),
    }


if __name__ == "__main__":

    config_parser = configparser.RawConfigParser()
    config_parser.read("/etc/mtv_cli.conf")
    try:
        config = get_config(config_parser)
    except Exception as e:
        logger.error(f"Konfiguration fehlerhaft! Fehler: {e}")
        sys.exit(3)

    opt_parser = get_parser()
    options = opt_parser.parse_args(namespace=Options)
    if options.doVersionInfo:
        print("Version: %s" % VERSION)
        sys.exit(0)

    logger.level(options.level if options.level else config["MSG_LEVEL"])

    # Verzeichnis HOME/.mediathek3 anlegen
    if not os.path.exists(MTV_CLI_HOME):
        os.mkdir(MTV_CLI_HOME)

    if not options.upd_src and not os.path.isfile(options.dbfile):
        logger.error("Datenbank %s existiert nicht!" % options.dbfile)
        sys.exit(3)

    # Lock anfordern
    if not get_lock(options.dbfile):
        logger.error("Datenbank %s ist gesperrt" % options.dbfile)
        sys.exit(3)

    # Globale Objekte anlegen
    options.config = config
    options.filmDB = FilmDB(options)

    if options.upd_src:
        do_update(options)
    elif options.doEdit:
        do_edit(options)
    elif options.doLater:
        do_later(options)
    elif options.doNow:
        do_now(options)
    elif options.doDownload:
        do_download(options)
    elif options.doSearch:
        if do_search(options):
            sys.exit(0)
        else:
            sys.exit(1)
    sys.exit(0)
