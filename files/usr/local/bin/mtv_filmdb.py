#!/usr/bin/python3
# -*- coding: utf-8 -*-
# --------------------------------------------------------------------------
# Mediathekview auf der Kommandozeile
#
# Class FilmDB, MtvDB: Alles rund im Datenbanken
#
# Author: Bernhard Bablok
# License: GPL3
#
# Website: https://github.com/bablokb/mtv_cli
#
# --------------------------------------------------------------------------

import os, sqlite3, json
from multiprocessing import Lock

from mtv_cfg      import *
from mtv_const    import *
from mtv_filminfo import *

# --- FilmDB: Datenbank aller Filme   --------------------------------------

class FilmDB(object):
  """Datenbank aller Filme"""

  # ------------------------------------------------------------------------
  
  def __init__(self,dbfile):
    """Constructor"""
    self.dbfile = dbfile
    self.last_liste = None
    self.lock = Lock()
    self.total = 0

  # ------------------------------------------------------------------------

  def open(self):
    """Datenbank öffnen und Cursor zurückgeben"""
    self.db = sqlite3.connect(self.dbfile,
                              detect_types=sqlite3.PARSE_DECLTYPES)
    self.db.row_factory = sqlite3.Row
    self.cursor = self.db.cursor()
    return self.cursor

  # ------------------------------------------------------------------------

  def close(self):
    """Datenbank schließen"""
    self.db.close()

  # ------------------------------------------------------------------------

  def create(self):
    """Tabelle Filme löschen und neu erzeugen"""
    self.db = sqlite3.connect(self.dbfile,
                              detect_types=sqlite3.PARSE_DECLTYPES)
    self.cursor = self.db.cursor()

    self.cursor.execute("DROP TABLE IF EXISTS filme")
    self.cursor.execute("""CREATE TABLE filme
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
      _id text primary key )""")

  # ------------------------------------------------------------------------

  def blacklist(film_info):
    """Gibt True zurück für Filme, die eingeschlossen werden sollen"""
    return (film_info.datum < date_cutoff or
          film_info.dauer_as_minutes() >= DAUER_CUTOFF)

  # ------------------------------------------------------------------------

  def rec2FilmInfo(self,record):
    """Ein Record in ein FilmInfo-Objekt umwandeln.
       Dazu erzeugt der JSON-Parser erste eine Liste,
       die anschließend an den Constructor übergeben wird. Damit die
       Datenbank nicht zu groß wird, werden nur Sätze der letzten x Tage
       zurückgegeben."""

    try:
      liste = json.loads(record)
      if self.last_liste:
        # ersetzen leerer Werte durch Werte aus dem Satz davor
        for i in range(len(liste)):
          if not liste[i]:
            liste[i] = self.last_liste[i]

      # Liste für nächsten Durchgang speichern
      self.last_liste = liste

      film_info = FilmInfo(*liste)

      # Sätze per blacklist aussortieren (def in mtv_cfg)
      if self.blacklist(film_info):
        return None
      else:
        return film_info
    except:
      print(record)
      raise

  # ------------------------------------------------------------------------

  def insert(self,record):
    """Satz zur Datenbank hinzufügen"""
    INSERT_STMT = 'INSERT INTO filme VALUES (' + 20 * '?,' + '?)'

    film_info = self.rec2FilmInfo(record)
    if film_info:
      self.total += 1
      self.cursor.execute(INSERT_STMT,film_info.asTuple())
  
  # ------------------------------------------------------------------------

  def commit(self):
    """Commit durchführen"""
    self.db.commit()
    
  # ------------------------------------------------------------------------

  def get_count(self):
    """Anzahl der schon eingefügten Sätze zurückgeben"""
    return self.total
  
  # ------------------------------------------------------------------------

  def save(self):
    """Filme speichern und Index erstellen"""
    self.db.commit()
    self.cursor.execute("CREATE index id_index ON filme(_id)")
    self.cursor.execute("CREATE index sender_index ON filme(sender)")
    self.cursor.execute("CREATE index thema_index ON filme(thema)")
    self.db.close()

  # ------------------------------------------------------------------------

  def iso_date(self,datum):
    """Deutsches Datum in ISO-Datum umwandeln"""
    parts=datum.split(".")
    return ("20" if len(parts[2]) == 2 else "") + \
           parts[2] + "-" + parts[1] + "-" + parts[0]

  # ------------------------------------------------------------------------
  
  def get_query(self,suche):
    """Aus Suchbegriff eine SQL-Query erzeugen"""
    #Basisausdruck
    select_clause = "select * from Filme where "

    if not len(suche):
      return select_clause[0:-7]                 # remove " where "
    elif suche[0].lower().startswith("select"):
      # Suchausdruck ist fertige Query
      return ' '.join(suche)

    where_clause = ""
    op = ""
    for token in suche:
      if token in ["(","und","oder","and","or",")"]:
        if op:
          where_clause = where_clause + op
        op = " %s " % token
        continue
      if ':' in token:
        # Suche per Schlüsselwort
        key,value = token.split(":")
        if where_clause:
          where_clause = where_clause +  (op if op else " and ")
        if key.upper() == "DATUM":
          # Sonderbehandlung Datum:
          if (">" in value) or ("<" in value) or ("=" in value):
            # datum:=xxx, datum:>xxx, datum:>=xxx usw.
            if value[1] in ["<",">","="]:
              date_op = value[0:2]
              value = value[2:]
            else:
              date_op = value[0]
              value = value[1:]
            where_clause = where_clause + "(%s %s '%s')" % \
                           (key,date_op,self.iso_date(value))
          elif "-" in value:
            # datum:start-end
            limits = value.split("-")
            where_clause = where_clause + (
              "(%s >= '%s' and %s <= '%s')" % (key,self.iso_date(limits[0])
                                           ,key,self.iso_date(limits[1])))
          else:
            # datum:xxx (identisch zu datum:=xxx)
            where_clause = where_clause + "(%s='%s')" % (key,self.iso_date(value))
        else:
          where_clause = where_clause + "(%s like '%%%s%%')" % (key,value)
      else:
        # Volltextsuche
        if where_clause:
          where_clause = where_clause + (op if op else " or ")
        where_clause = where_clause + (
          """(Sender       like '%%%s%%' or
          Thema        like '%%%s%%' or
          Titel        like '%%%s%%' or
          Beschreibung like '%%%s%%')""" % (token,token,token,token))
      op = ""
    msg("DEBUG","SQL-Where: %s" % where_clause)
    return select_clause + where_clause

  # ------------------------------------------------------------------------
  
  def execute_query(self,statement):
    """Suche ausführen"""
    cursor = self.open()
    cursor.execute(statement)
    result = cursor.fetchall()
    self.close()
    return result

  # ------------------------------------------------------------------------

  def read_filme(self,index_liste):
    """Alle Filme lesen, deren _id in index_liste ist"""

    # Zeilen lesen
    cursor = self.open()
    statement = "select * from Filme where _id in %s" % str(tuple(index_liste))
    cursor.execute(statement)
    rows = cursor.fetchall()
    self.close()

    # Zeilen als Liste von FilmInfo-Objekten zurückgeben
    return [FilmInfo(*row) for row in rows]

  # ------------------------------------------------------------------------

  def save_downloads(self,rows):
    """Downloads, sichern.
       rows ist eine Liste von (_id,Datum,Status)-Tupeln"""

    CREATE_STMT = """CREATE TABLE IF NOT EXISTS downloads (
                     _id          text primary key,
                     Datum        date,
                     status       text,
                     DatumStatus  date)"""
    INSERT_STMT = """INSERT OR IGNORE INTO downloads Values (?,?,?,?)"""

    # Aktuelles Datum an Werte anfügen
    for i in range(len(rows)):
      rows[i] = rows[i] +(datetime.date.today(),)

    # Tabelle bei Bedarf erstellen
    cursor = self.open()
    cursor.execute(CREATE_STMT)
    self.commit()

    # Ein Lock ist hier nicht nötig, da Downloads bei -V immer in
    # einem eigene Aufruf von mtv_cli stattfinden und bei -S immer
    # nach save_downloads

    cursor.executemany(INSERT_STMT,rows)
    changes = self.db.total_changes
    self.commit()
    self.close()
    return changes

  # ------------------------------------------------------------------------

  def delete_downloads(self,rows):
    """Downloads löschen"""
    DEL_STMT = "DELETE FROM downloads where _id=?"

    # Ein Lock ist hier nicht nötig, da Downloads immer in
    # einem eigene Aufruf von mtv_cli stattfinden

    cursor = self.open()
    cursor.executemany(DEL_STMT,rows)
    changes = self.db.total_changes
    self.commit()
    self.close()
    return changes

  # ------------------------------------------------------------------------

  def update_downloads(self,_id,status):
    """Status eines Satzes ändern"""
    UPD_STMT = "UPDATE downloads SET status=?,DatumStatus=? where _id=?"
    try:
      self.lock.acquire()
      cursor = self.open()
      cursor.execute(UPD_STMT,(status,datetime.date.today(),_id))
      self.commit()
      self.close()
    finally:
      self.lock.release()

  # ------------------------------------------------------------------------

  def read_downloads(self,ui=True,status="'V','S','A','F','K'"):
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
      SEL_STMT = """SELECT d.status      as status,
                           d.DatumStatus as DatumStatus,
                           d._id         as _id,
                           f.sender      as sender,
                           f.thema       as thema,
                           f.titel       as titel,
                           f.dauer       as dauer,
                           f.datum       as datum
                      FROM filme as f, downloads as d
                        WHERE f._id = d._id AND d.status in (%s)
                        ORDER BY DatumStatus DESC""" % status
    else:
      SEL_STMT = """SELECT f.*
                      FROM filme as f, downloads as d
                        WHERE f._id = d._id AND d.status in (%s)""" % status

    cursor = self.open()
    try:
      cursor.execute(SEL_STMT)
      rows = cursor.fetchall()
    except sqlite3.OperationalError as e:
      msg("DEBUG","SQL-Fehler: %s" % e)
      rows = None
    self.close()
    if ui:
      return rows
    else:
      return [FilmInfo(*row) for row in rows]

# --------------------------------------------------------------------------

class MtvDB(object):
  pass
