# --------------------------------------------------------------------------
# Mediathekview auf der Kommandozeile
#
# Class FilmDB, MtvDB: Alles rund um Datenbanken
#
# Author: Bernhard Bablok, Max Görner
# License: GPL3
#
# Website: https://github.com/bablokb/mtv_cli
#
# --------------------------------------------------------------------------

import datetime
import sqlite3
from dataclasses import astuple
from multiprocessing import Lock

from loguru import logger
from mtv_filminfo import FilmInfo, FilmlistenEintrag

# --- FilmDB: Datenbank aller Filme   --------------------------------------


class FilmDB:
    """Datenbank aller Filme"""

    # ------------------------------------------------------------------------

    def __init__(self, options):
        """Constructor"""
        self.config = options.config
        self.dbfile = options.dbfile
        self.last_liste = None
        self.lock = Lock()
        self.total = 0
        self.date_cutoff = datetime.date.today() - datetime.timedelta(
            days=self.config["DATE_CUTOFF"]
        )

    # ------------------------------------------------------------------------

    def open(self):
        """Datenbank öffnen und Cursor zurückgeben"""
        self.db = sqlite3.connect(self.dbfile, detect_types=sqlite3.PARSE_DECLTYPES)
        self.db.row_factory = sqlite3.Row
        self.cursor = self.db.cursor()
        return self.cursor

    # ------------------------------------------------------------------------

    def close(self):
        """Datenbank schließen"""
        self.db.close()

    # ------------------------------------------------------------------------

    def create_filmtable(self):
        """Tabelle Filme löschen und neu erzeugen"""
        self.db = sqlite3.connect(self.dbfile, detect_types=sqlite3.PARSE_DECLTYPES)
        self.cursor = self.db.cursor()

        self.cursor.execute("DROP TABLE IF EXISTS filme")
        self.cursor.execute(
            """CREATE TABLE filme
      (Sender text,
      Thema text,
      Titel text,
      Datum date,
      Zeit text,
      Dauer text,
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
      DatumL text,
      Url_History text,
      Geo text,
      neu text,
      _id text primary key )"""
        )

    # ------------------------------------------------------------------------

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

    def insert_film(self, eintrag: FilmlistenEintrag) -> None:
        """Satz zur Datenbank hinzufügen"""
        INSERT_STMT = "INSERT INTO filme VALUES (" + 20 * "?," + "?)"
        self.total += 1
        self.cursor.execute(INSERT_STMT, astuple(eintrag))

    def commit(self):
        """Commit durchführen"""
        self.db.commit()

    # ------------------------------------------------------------------------

    def save_filmtable(self):
        """Filme speichern und Index erstellen"""
        self.db.commit()
        self.cursor.execute("CREATE index id_index ON filme(_id)")
        self.cursor.execute("CREATE index sender_index ON filme(sender)")
        self.cursor.execute("CREATE index thema_index ON filme(thema)")
        self.db.close()
        self.save_status("_akt")
        self.save_status("_anzahl", str(self.total))

    # ------------------------------------------------------------------------

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

    # ------------------------------------------------------------------------

    def get_query(self, suche):
        """Aus Suchbegriff eine SQL-Query erzeugen"""
        # Basisausdruck
        select_clause = "select * from Filme where "

        if not len(suche):
            return select_clause[0:-7]  # remove " where "
        elif suche[0].lower().startswith("select"):
            # Suchausdruck ist fertige Query
            return " ".join(suche)

        where_clause = ""
        op = ""
        for token in suche:
            if token in ["(", "und", "oder", "and", "or", ")"]:
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
        return select_clause + where_clause

    # ------------------------------------------------------------------------

    def execute_query(self, statement):
        """Suche ausführen"""
        cursor = self.open()
        cursor.execute(statement)
        result = cursor.fetchall()
        self.close()
        return result

    # ------------------------------------------------------------------------

    def save_downloads(self, rows):
        """Downloads, sichern.
        rows ist eine Liste von (_id,Datum,Status)-Tupeln"""

        CREATE_STMT = """CREATE TABLE IF NOT EXISTS downloads (
                     _id          text primary key,
                     Datum        date,
                     status       text,
                     DatumStatus  date)"""
        INSERT_STMT = """INSERT OR IGNORE INTO downloads Values (?,?,?,?)"""

        # Aktuelles Datum an Werte anfügen
        today = datetime.date.today()
        for val_list in rows:
            val_list.append(today)

        # Tabelle bei Bedarf erstellen
        cursor = self.open()
        cursor.execute(CREATE_STMT)
        self.commit()

        # Ein Lock ist hier nicht nötig, da Downloads bei -V immer in
        # einem eigenen Aufruf von mtv_cli stattfinden und bei -S immer
        # nach save_downloads

        cursor.executemany(INSERT_STMT, rows)
        changes = self.db.total_changes
        self.commit()
        self.close()
        return changes

    # ------------------------------------------------------------------------

    def delete_downloads(self, rows):
        """Downloads löschen"""
        DEL_STMT = "DELETE FROM downloads where _id=?"

        logger.debug("rows: " + str(rows))

        # Ein Lock ist hier nicht nötig, da Downloads immer in
        # einem eigene Aufruf von mtv_cli stattfinden

        cursor = self.open()
        cursor.executemany(DEL_STMT, rows)
        changes = self.db.total_changes
        self.commit()
        self.close()
        return changes

    # ------------------------------------------------------------------------

    def update_downloads(self, _id, status):
        """Status eines Satzes ändern"""
        UPD_STMT = "UPDATE downloads SET status=?,DatumStatus=? where _id=?"
        with self.lock:
            cursor = self.open()
            cursor.execute(UPD_STMT, (status, datetime.date.today(), _id))
            self.commit()
            self.close()

    # ------------------------------------------------------------------------

    def read_downloads(self, ui=True, status="'V','S','A','F','K'"):
        """Downloads auslesen. Falls ui=True, Subset für Anzeige.
        Bedeutung der Status-Codes:
        V - Vorgemerkt
        S - Sofort
        A - Aktiv
        F - Fehler
        K - Komplett
        """

        # SQL-Teile
        if ui:
            SEL_STMT = (
                """SELECT d.status      as status,
                           d.DatumStatus as DatumStatus,
                           d._id         as _id,
                           f.sender      as sender,
                           f.thema       as thema,
                           f.titel       as titel,
                           f.dauer       as dauer,
                           f.datum       as datum
                      FROM filme as f, downloads as d
                        WHERE f._id = d._id AND d.status in (%s)
                        ORDER BY DatumStatus DESC"""
                % status
            )
        else:
            SEL_STMT = (
                """SELECT f.*
                      FROM filme as f, downloads as d
                        WHERE f._id = d._id AND d.status in (%s)"""
                % status
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
        else:
            return [FilmInfo(*row) for row in rows]

    # ------------------------------------------------------------------------

    def save_status(self, key, text=None):
        """Status in Status-Tabelle speichern"""

        CREATE_STMT = """CREATE TABLE IF NOT EXISTS status (
                     key          text primary key,
                     Zeit         timestamp,
                     text         text)"""
        INSERT_STMT = """INSERT OR REPLACE INTO status Values (?,?,?)"""

        # Zeitstempel
        now = datetime.datetime.now()

        # Tabelle bei Bedarf erstellen
        with self.lock:
            cursor = self.open()
            cursor.execute(CREATE_STMT)
            self.commit()
            cursor.execute(INSERT_STMT, (key, now, text))
            self.commit()
            self.close()

    # ------------------------------------------------------------------------

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

    # ------------------------------------------------------------------------

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
        SEL_STMT = """SELECT sender,
                            titel,
                            beschreibung,
                            datum
                      FROM filme
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
                cursor.execute(
                    INSERT_STMT, tuple(row) + (Dateiname, datetime.date.today())
                )
                self.commit()
        except sqlite3.OperationalError as e:
            logger.debug("SQL-Fehler: %s" % e)
        self.close()

    # ------------------------------------------------------------------------

    def delete_recs(self, rows):
        """Aufnahme löschen.
        rows ist Array von Tuplen: [(name,),(name,), ...]"""
        DEL_STMT = "DELETE FROM recordings where Dateiname=?"

        logger.debug("rows: " + str(rows))

        # Ein Lock ist hier nicht nötig, da Downloads immer in
        # einem eigene Aufruf von mtv_cli stattfinden

        cursor = self.open()
        cursor.executemany(DEL_STMT, rows)
        changes = self.db.total_changes
        self.commit()
        self.close()
        return changes

    # ------------------------------------------------------------------------

    def read_recs(self, Dateiname=None):
        """Aufnahmen auslesen."""

        if Dateiname:
            SEL_STMT = "SELECT * from recordings where Dateiname=?"
        else:
            SEL_STMT = "SELECT * from recordings"

        logger.debug("SQL-Query: %s" % SEL_STMT)
        cursor = self.open()
        try:
            if Dateiname:
                cursor.execute(SEL_STMT, (Dateiname,))
            else:
                cursor.execute(SEL_STMT)
            rows = cursor.fetchall()
        except sqlite3.OperationalError as e:
            logger.debug("SQL-Fehler: %s" % e)
            rows = None
        self.close()
        return rows
