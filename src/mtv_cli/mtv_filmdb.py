# Mediathekview auf der Kommandozeile
#
# Class FilmDB, MtvDB: Alles rund um Datenbanken
#
# Author: Bernhard Bablok, Max Görner
# License: GPL3
#
# Website: https://github.com/bablokb/mtv_cli
#

from __future__ import annotations

import datetime as dt
import hashlib
import sqlite3
from multiprocessing import Lock
from pathlib import Path
from typing import Iterable, Literal, Optional, Union

from loguru import logger
from mtv_filminfo import FilmlistenEintrag

# Bedeutung der Status-Codes:
# V - Vorgemerkt
# S - Sofort
# A - Aktiv
# F - Fehler
# K - Komplett
DownloadStatus = Union[
    Literal["V"], Literal["S"], Literal["A"], Literal["F"], Literal["K"]
]


class FilmDB:
    """Datenbank aller Filme"""

    def __init__(self, options):
        """Constructor"""
        self.config = options.config
        self.dbfile = options.dbfile
        self.last_liste = None
        self.lock = Lock()
        self.total = 0
        self.date_cutoff = dt.date.today() - dt.timedelta(
            days=self.config["DATE_CUTOFF"]
        )
        self.filmdb = "filme"
        self.downloadsdb = "downloads"

    def open(self):
        """Datenbank öffnen und Cursor zurückgeben"""
        self.db = sqlite3.connect(self.dbfile, detect_types=sqlite3.PARSE_DECLTYPES)
        self.db.row_factory = sqlite3.Row
        self.cursor = self.db.cursor()
        return self.cursor

    def close(self):
        """Datenbank schließen"""
        self.db.close()

    def create_filmtable(self):
        """Tabelle Filme löschen und neu erzeugen"""
        self.db = sqlite3.connect(self.dbfile, detect_types=sqlite3.PARSE_DECLTYPES)
        self.cursor = self.db.cursor()

        self.cursor.execute(f"DROP TABLE IF EXISTS {self.filmdb}")
        self.cursor.execute(
            f"""CREATE TABLE {self.filmdb}
      (Sender text,
      Thema text,
      Titel text,
      Datum date,
      Zeit text,
      Dauer integer,
      Groesse integer,
      Beschreibung text,
      Url text,
      Website text,
      Url_Untertitel text,
      Url_RTMP text,
      Url_Klein text,
      Url_RTMP_Klein text,
      Url_HD text,
      Url_RTMP_HD text,
      DatumL int,
      Url_History text,
      Geo text,
      neu bool,
      _id text primary key )"""
        )

    def is_on_ignorelist(self, eintrag: FilmlistenEintrag) -> bool:
        """Gibt True zurück für Filme, die ausgeschlossen werden sollen

        Momentan werden Filme wegen einem von drei Gründen ausgeschlossen:

            * Es fehlt ein Datum (Livestreams)
            * zu alt
            * zu kurz
        """

        if eintrag.datum is None:
            return True
        if eintrag.datum < self.date_cutoff:
            return True
        if eintrag.dauer_as_minutes() < self.config["DAUER_CUTOFF"]:
            return True
        return False

    def insert_film(self, film: FilmlistenEintrag) -> None:
        """Satz zur Datenbank hinzufügen"""
        INSERT_STMT = f"INSERT INTO {self.filmdb} VALUES (" + 20 * "?," + "?)"
        as_dict = film.dict()
        as_dict["_id"] = self.get_film_id(film)
        as_dict["zeit"] = None if film.zeit is None else film.zeit.strftime("%H:%M")
        as_dict["dauer"] = film.dauer_as_minutes()
        self.total += 1
        self.cursor.execute(INSERT_STMT, tuple(as_dict.values()))

    def commit(self):
        """Commit durchführen"""
        self.db.commit()

    def save_filmtable(self):
        """Filme speichern und Index erstellen"""
        self.db.commit()
        self.cursor.execute(f"CREATE index id_index ON {self.filmdb}(_id)")
        self.cursor.execute(f"CREATE index sender_index ON {self.filmdb}(sender)")
        self.cursor.execute(f"CREATE index thema_index ON {self.filmdb}(thema)")
        self.db.close()
        self.save_status("_akt")
        self.save_status("_anzahl", str(self.total))

    def iso_date(self, datum):
        """Deutsches Datum in ISO-Datum umwandeln"""
        parts = datum.split(".")
        return (
            ("20" if len(parts[2]) == 2 else "")
            + parts[2]
            + "-"
            + parts[1]
            + "-"
            + parts[0]
        )

    def get_query(self, suche: list[str]) -> str:
        """Aus Suchbegriff eine SQL-Query erzeugen"""

        if len(suche) == 0:
            return f"SELECT * FROM {self.filmdb}"
        if suche[0].lower().startswith("select"):
            # Suchausdruck ist fertige Query
            return " ".join(suche)

        where_clause = ""
        op = ""
        for token in suche:
            if token in {"(", "und", "oder", "and", "or", ")"}:
                if op:
                    where_clause = where_clause + op
                op = " %s " % token
                continue
            if ":" in token:
                # Suche per Schlüsselwort
                key, value = token.split(":")
                if where_clause:
                    where_clause = where_clause + (op if op else " and ")
                if key.upper() == "DATUM":
                    # Sonderbehandlung Datum:
                    if (">" in value) or ("<" in value) or ("=" in value):
                        # datum:=xxx, datum:>xxx, datum:>=xxx usw.
                        if value[1] in ["<", ">", "="]:
                            date_op = value[0:2]
                            value = value[2:]
                        else:
                            date_op = value[0]
                            value = value[1:]
                        where_clause = where_clause + "(%s %s '%s')" % (
                            key,
                            date_op,
                            self.iso_date(value),
                        )
                    elif "-" in value:
                        # datum:start-end
                        limits = value.split("-")
                        where_clause = where_clause + (
                            "(%s >= '%s' and %s <= '%s')"
                            % (
                                key,
                                self.iso_date(limits[0]),
                                key,
                                self.iso_date(limits[1]),
                            )
                        )
                    else:
                        # datum:xxx (identisch zu datum:=xxx)
                        where_clause = where_clause + "(%s='%s')" % (
                            key,
                            self.iso_date(value),
                        )
                else:
                    where_clause = where_clause + "(%s like '%%%s%%')" % (key, value)
            else:
                # Volltextsuche
                if where_clause:
                    where_clause = where_clause + (op if op else " or ")
                where_clause = where_clause + (
                    """(Sender       like '%%%s%%' or
          Thema        like '%%%s%%' or
          Titel        like '%%%s%%' or
          Beschreibung like '%%%s%%')"""
                    % (token, token, token, token)
                )
            op = ""

        # falls noch ein Operator übrig ist:
        if op:
            where_clause = where_clause + op
        logger.debug("SQL-Where: %s" % where_clause)
        return f"SELECT * FROM {self.filmdb} WHERE {where_clause}"

    def finde_filme(self, criteria: list[str]) -> Iterable[FilmlistenEintrag]:
        """Finde alle Filme, die auf Suchkriterium passen"""

        query = self.get_query(criteria)
        cursor = self.open()
        cursor.execute(query)
        for item in cursor.fetchall():
            as_dict = {key.lower(): item[key] for key in item.keys()}
            del as_dict["_id"]
            if as_dict["zeit"] is not None:
                as_dict["zeit"] = dt.datetime.strptime(as_dict["zeit"], "%H:%M").time()
            else:
                logger.info("Zeit ist None")
            if as_dict["dauer"] is not None:
                as_dict["dauer"] = dt.timedelta(minutes=as_dict["dauer"])
            else:
                logger.info("Dauer ist None")
            as_dict["neu"] = bool(as_dict["neu"])
            film = FilmlistenEintrag.parse_obj(as_dict)
            yield film
        self.close()

    def save_downloads(
        self, filme: list[FilmlistenEintrag], status=DownloadStatus
    ) -> int:
        """Downloads sichern."""

        CREATE_STMT = f"""CREATE TABLE IF NOT EXISTS {self.downloadsdb} (
                     _id          integer primary key,
                     Datum        date,
                     status       text,
                     DatumStatus  date)"""
        INSERT_STMT = f"""INSERT OR IGNORE INTO {self.downloadsdb} Values (?,?,?,?)"""

        # Aktuelles Datum an Werte anfügen
        today = dt.date.today()
        query_values = [
            (self.get_film_id(film), film.datum, status, today) for film in filme
        ]

        # Tabelle bei Bedarf erstellen
        cursor = self.open()
        cursor.execute(CREATE_STMT)
        self.commit()

        # Ein Lock ist hier nicht nötig, da Downloads bei -V immer in
        # einem eigenen Aufruf von mtv_cli stattfinden und bei -S immer
        # nach save_downloads

        cursor.executemany(INSERT_STMT, query_values)
        changes: int = self.db.total_changes
        self.commit()
        self.close()
        return changes

    def delete_downloads(self, rows):
        """Downloads löschen"""
        DEL_STMT = f"DELETE FROM {self.downloadsdb} where _id=?"

        logger.debug("rows: " + str(rows))

        # Ein Lock ist hier nicht nötig, da Downloads immer in
        # einem eigene Aufruf von mtv_cli stattfinden

        cursor = self.open()
        cursor.executemany(DEL_STMT, rows)
        changes = self.db.total_changes
        self.commit()
        self.close()
        return changes

    def update_downloads(self, film: FilmlistenEintrag, status: DownloadStatus):
        """Status eines Satzes ändern"""
        UPD_STMT = f"UPDATE {self.downloadsdb} SET status=?,DatumStatus=? where _id=?"
        film_id = self.get_film_id(film)
        with self.lock:
            cursor = self.open()
            cursor.execute(UPD_STMT, (status, dt.date.today(), film_id))
            self.commit()
            self.close()

    def read_downloads(self, ui=True, status=list[DownloadStatus]):
        """Downloads auslesen. Falls ui=True, Subset für Anzeige."""

        status_query_str = ",".join(f"'{cur}'" for cur in status)
        # SQL-Teile
        if ui:
            SEL_STMT = (
                f"""SELECT d.status      as status,
                           d.DatumStatus as DatumStatus,
                           d._id         as _id,
                           f.sender      as sender,
                           f.thema       as thema,
                           f.titel       as titel,
                           f.dauer       as dauer,
                           f.datum       as datum
                      FROM {self.filmdb} as f, {self.downloadsdb} as d
                        WHERE f._id = d._id AND d.status in (%s)
                        ORDER BY DatumStatus DESC"""
                % status_query_str
            )
        else:
            SEL_STMT = (
                f"""SELECT f.*
                      FROM {self.filmdb} as f, {self.downloadsdb} as d
                        WHERE f._id = d._id AND d.status in (%s)"""
                % status_query_str
            )

        logger.debug("SQL-Query: %s" % SEL_STMT)
        cursor = self.open()
        try:
            cursor.execute(SEL_STMT)
            rows = cursor.fetchall()
        except sqlite3.OperationalError as e:
            logger.debug("SQL-Fehler: %s" % e)
            rows = None
        self.close()
        if ui:
            return rows
        return [FilmlistenEintrag.from_item_list(row) for row in rows]

    def save_status(self, key, text=None):
        """Status in Status-Tabelle speichern"""

        CREATE_STMT = """CREATE TABLE IF NOT EXISTS status (
                     key          text primary key,
                     Zeit         timestamp,
                     text         text)"""
        INSERT_STMT = """INSERT OR REPLACE INTO status Values (?,?,?)"""

        # Zeitstempel
        now = dt.datetime.now()

        # Tabelle bei Bedarf erstellen
        with self.lock:
            cursor = self.open()
            cursor.execute(CREATE_STMT)
            self.commit()
            cursor.execute(INSERT_STMT, (key, now, text))
            self.commit()
            self.close()

    def read_status(self, keys):
        """Status aus Status-Tabelle auslesen"""

        SEL_STMT = "SELECT * FROM status WHERE key in %s" % str(tuple(keys))
        rows = None
        try:
            with self.lock():
                cursor = self.open()
                cursor.execute(SEL_STMT)
                rows = cursor.fetchall()
                self.close()
        except sqlite3.OperationalError as e:
            logger.debug("SQL-Fehler: %s" % e)
        return rows

    def save_recs(self, id, Dateiname):
        """Aufnahme sichern."""

        logger.info("Sichere Aufnahmen: %s,%s" % (id, Dateiname))
        CREATE_STMT = """CREATE TABLE IF NOT EXISTS recordings (
                     Sender       text,
                     Titel        text,
                     Beschreibung text,
                     DatumFilm    date,
                     Dateiname    text primary key,
                     DatumDatei   date)"""
        INSERT_STMT = """INSERT OR IGNORE INTO recordings Values (?,?,?,?,?,?)"""
        SEL_STMT = f"""SELECT sender,
                            titel,
                            beschreibung,
                            datum
                      FROM {self.filmdb}
                        WHERE _id = ?"""

        # ausgewählte Felder aus Film-DB lesen
        cursor = self.open()
        try:
            logger.debug("SQL-Query: %s" % SEL_STMT)
            cursor.execute(SEL_STMT, (id,))
            row = cursor.fetchone()
        except sqlite3.OperationalError as e:
            logger.debug("SQL-Fehler: %s" % e)
            row = None

        if not row:
            self.close()
            return
        for r in row:
            logger.info("row: %r" % r)

        # Tabelle bei Bedarf erstellen
        logger.debug("SQL-Create: %s" % CREATE_STMT)
        cursor.execute(CREATE_STMT)
        self.commit()

        # ohne Lock, da Insert mit neuem Schlüssel
        try:
            with self.lock:
                logger.debug("SQL-Insert: %s" % INSERT_STMT)
                cursor.execute(INSERT_STMT, tuple(row) + (Dateiname, dt.date.today()))
                self.commit()
        except sqlite3.OperationalError as e:
            logger.debug("SQL-Fehler: %s" % e)
        self.close()

    def delete_recs(self, rows: list[tuple[Path]]) -> int:
        """Aufnahme löschen.
        rows ist Array von Tuplen: [(name,),(name,), ...]"""
        DEL_STMT = "DELETE FROM recordings where Dateiname=?"

        logger.debug("rows: " + str(rows))

        # Ein Lock ist hier nicht nötig, da Downloads immer in
        # einem eigene Aufruf von mtv_cli stattfinden

        cursor = self.open()
        cursor.executemany(DEL_STMT, rows)
        changes: int = self.db.total_changes
        self.commit()
        self.close()
        return changes

    def read_recs(self, dateiname: Optional[Path] = None) -> Optional[list[dict]]:
        """Aufnahmen auslesen."""

        if dateiname is None:
            SEL_STMT = "SELECT * from recordings"
        else:
            SEL_STMT = "SELECT * from recordings where Dateiname=?"

        logger.debug("SQL-Query: %s" % SEL_STMT)
        cursor = self.open()
        rows: Optional[list[dict]] = None
        try:
            if dateiname is None:
                cursor.execute(SEL_STMT)
            else:
                cursor.execute(SEL_STMT, (str(dateiname),))
            rows = cursor.fetchall()
        except sqlite3.OperationalError as e:
            logger.debug("SQL-Fehler: %s" % e)
        self.close()
        return rows

    @staticmethod
    def get_film_id(film: FilmlistenEintrag) -> str:
        datum = "" if film.datum is None else film.datum.isoformat()
        zeit = "" if film.zeit is None else film.zeit.isoformat()
        id_str = ",".join([film.sender, film.thema, film.titel, datum, zeit, film.url])
        id_bytes = id_str.encode("utf-8")
        hexdigest = hashlib.md5(id_bytes).hexdigest()
        return hexdigest
