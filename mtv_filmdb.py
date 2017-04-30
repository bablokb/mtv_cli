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
    self._id = 0
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
    """Neue Datenbank (temporär) erzeugen"""
    if os.path.isfile(self.dbfile+'.new'):
        os.remove(self.dbfile+'.new')
    self.db = sqlite3.connect(self.dbfile+'.new',
                              detect_types=sqlite3.PARSE_DECLTYPES)
    self.cursor = self.db.cursor()

    self.cursor.execute("""create table filme
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
      _id integer primary key )""")

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

      # Dummy-ID hinzufügen
      liste.append(0)
      film_info = FilmInfo(*liste)

      # zu alte Sätze ignorieren
      if film_info.datum < date_cutoff:
        return None

      # echte ID setzen
      self._id = self._id + 1
      film_info._id = self._id
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
    return self._id
  
  # ------------------------------------------------------------------------

  def save(self):
    """Temporäre Datenbank endgültig speichern"""
    self.db.commit()
    self.db.close()

    # Alte Datenbank löschen und neue umbenennen
    if os.path.isfile(self.dbfile):
      os.remove(self.dbfile)
    os.rename(self.dbfile+'.new',self.dbfile)

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
  
  def execute_query(self,suche):
    """Suche ausführen"""
    if not os.path.isfile(self.dbfile):
      msg("ERROR","Datenbank %s existiert nicht!" % self.dbfile)
      return None

    statement = self.get_query(suche)
    cursor = self.open()
    cursor.execute(statement)
    result = cursor.fetchall()
    self.close()
    return result


# --- MtvDB: Status-Datenbank   --------------------------------------------

class MtvDB(object):
  pass
