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

from mtv_cfg      import *
from mtv_filminfo import *

# --- FilmDB: Datenbank aller Filme   --------------------------------------

class FilmDB(object):
  """Datenbank aller Filme"""

  # ------------------------------------------------------------------------
  
  def __init__(self,dbfile):
    """Constructor"""
    self.dbfile = dbfile
    self.last_liste = None
    self.total = 0
    self.INSERT_STMT = 'INSERT INTO filme VALUES (' + 20 * '?,' + '?)'

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

      # zu alte Sätze ignorieren
      if film_info.datum < date_cutoff:
        return None

      # Anzahl Sätze aufsummieren
      self.total += 1
      return film_info
    except:
      print(record)
      raise

  # ------------------------------------------------------------------------

  def insert(self,record):
    """Satz zur Datenbank hinzufügen"""
    film_info = self.rec2FilmInfo(record)
    if film_info:
      self.cursor.execute(self.INSERT_STMT,film_info.asTuple())
  
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
  
  def get_query(self,suche):
    """Aus Suchbegriff eine SQL-Query erzeugen"""
    #Basisausdruck
    select_clause = "select Sender,Thema,Titel,Datum,Beschreibung,_id from Filme where "

    if not len(suche):
      return select_clause[0:-7]                 # remove " where "
    elif suche[0].lower().startswith("select"):
      # Suchausdruck ist fertige Query
      return ' '.join(suche)

    where_clause = ""
    if '=' in suche[0]:
      # Suche per Schlüsselwort
      for token in suche:
        key,value = token.split("=")
        if where_clause:
          where_clause = where_clause + " and "
        where_clause = where_clause + key + " like '%" + value + "%'"
    else:
      # Volltextsuche
      for token in suche:
        if where_clause:
          where_clause = where_clause + " or "
        where_clause = where_clause + (
          """Sender       like '%%%s%%' or
          Thema        like '%%%s%%' or
          Titel        like '%%%s%%' or
          Beschreibung like '%%%s%%'""" % (token,token,token,token))
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
                     _id       text primary key,
                     Datum     date,
                     status    text,
                     DatumNeu  date)"""
    INSERT_STMT = """INSERT OR IGNORE INTO downloads Values (?,?,?,?)"""

    # Aktuelles Datum an Werte anfügen
    for i in range(len(rows)):
      rows[i] = rows[i] +(datetime.date.today(),)

    # Tabelle bei Bedarf erstellen
    cursor = self.open()
    cursor.execute(CREATE_STMT)
    self.commit()
    cursor.executemany(INSERT_STMT,rows)
    changes = self.db.total_changes
    self.commit()
    self.close()
    return changes

  # ------------------------------------------------------------------------

  def read_downloads(self,status="'V','S','A','R','F'"):
    """Downloads auslesen.
       Bedeutung der Status-Codes:
       V - Vorgemerkt
       S - Sofort
       A - Aktiv
       F - Fehler
       K - Komplett
    """

    # SQL-Teile
    SEL_STMT = """SELECT d.status as status,
                         f.sender as sender,
                         f.thema  as thema,
                         f.titel  as titel,
                         f.datum  as datum
                    FROM filme as f, downloads as d
                      WHERE f._id = d._id AND d.status in (%s)""" % status
    cursor = self.open()
    cursor.execute(SEL_STMT)
    rows = cursor.fetchall()
    self.close()
    return rows

# --------------------------------------------------------------------------

class MtvDB(object):
  pass
