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

import os, sqlite3

from mtv_cfg   import *
from mtv_const import *

# --- FilmDB: Datenbank aller Filme   --------------------------------------

class FilmDB(object):
  """Datenbank aller Filme"""

  # ------------------------------------------------------------------------
  
  def __init__(self,dbfile):
    """Constructor"""
    self.dbfile = dbfile

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
      msg("ERROR","Datenbank existiert nicht!")
      return None

    db = sqlite3.connect(self.dbfile)
    cursor = db.cursor()
    statement = self.get_query(suche)
    cursor.execute(statement)
    result = cursor.fetchall()
    db.close()
    return result


# --- MtvDB: Status-Datenbank   --------------------------------------------

class MtvDB(object):
  pass
