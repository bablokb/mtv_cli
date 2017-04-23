#!/usr/bin/python3
# -*- coding: utf-8 -*-
# --------------------------------------------------------------------------
# Mediathekview auf der Kommandozeile
#
# Author: Bernhard Bablok
# License: GPL3
#
# Website: https://github.com/bablokb/mtv_cli
#
# --------------------------------------------------------------------------

from argparse import ArgumentParser
import sys, os, re, lzma, json, datetime
import urllib.request as request
import sqlite3

BUFSIZE=8192
DATE_CUTOFF=30   # die letzten x-Tage werden gespeichert
URL_FILMLISTE="http://download10.onlinetvrecorder.com/mediathekview/Filmliste-akt.xz"
SQLITE_DB_FILE="Filmliste.sqlite"
MSG_LEVEL="INFO"

class Options(object):
  pass

# --- Meldung ausgeben   ----------------------------------------------------

MSG_LEVELS={
  "DEBUG":1,
  "INFO":2,
  "WARN":3,
  "ERROR":4
  }

def msg(level,text,nl=True):
  if MSG_LEVELS[level] >= MSG_LEVELS[MSG_LEVEL]:
    sys.stderr.write(text)
    if nl:
      sys.stderr.write("\n")
    sys.stderr.flush()

# --- Stream der Filmliste   ------------------------------------------------

def get_url_fp(url):
  """ URL öffnen und Filepointer zurückgeben"""
  # TODO: Austausch, da request.urlopen keine Server-SSLs überprüft
  return request.urlopen(url)

# --- Stream des LZMA-Entpackers   ------------------------------------------

def get_lzma_fp(url_fp):
  """ Fileponter des LZMA-Entpackers. Argument ist der FP der URL"""
  return lzma.open(url_fp,"rt",encoding='utf-8')

# --- Header verarbeiten   --------------------------------------------------

def handle_header(record,cursor):
  """Header der Filmliste verarbeiten.
     Wir verzichten darauf, da der Header nicht ohne große Klimmzüge
     verwertet kann (theoretisch könnte man die Spalten der Datenbank
     aus der Header-Information füllen)
  """
  # Statische Definition der Tabellenspalten
  cursor.execute("""create table filme
     (Sender text,
      Thema text,
      Titel text,
      Datum text,
      Zeit text,
      Dauer text,
      Groesse text,
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
      neu text)""")
  return 'INSERT INTO filme VALUES (' + 19 * '?,' + '?)'

# --- Datum in ein Date-Objekt umwandeln   ----------------------------------

def to_date(datum):
  """Datumsstring in ein Date-Objekt umwandeln"""
  if '.' in datum:
    return datetime.datetime.strptime(datum,"%d.%m.%Y").date()
  else:
    # schon im ISO-Format
    return datetime.datetime.strptime(datum,"%Y-%m-%d").date()
  
# --- Record in ein Tuple umwandeln   ---------------------------------------

last_liste=None
date_cutoff=datetime.date.today() - datetime.timedelta(days=DATE_CUTOFF)
def rec2tuple(record):
  """Ein Record in ein Tuple umwandeln. Dazu erzeugt der JSON-Parser erste
     eine Liste, die anschließend in ein Tuple umgewandelt wird. Damit die
     Datenbank nicht zu groß wird, werden nur Sätze der letzten x Tage
     zurückgegeben."""
  global last_liste, date_cutoff
  try:
    liste = json.loads(record)
    if last_liste:
      # ersetzen leerer Werte durch Werte aus dem Satz davor
      for i in range(len(liste)):
        if not liste[i]:
          liste[i] = last_liste[i]
    last_liste = liste

    # Datum ins ISO-Format umwandeln und Cutoff
    datum_obj = to_date(liste[3])
    if datum_obj < date_cutoff:
      return None
    liste[3] = datum_obj.isoformat()
    return tuple(liste)
  except:
    print(record)
    raise

# --- Split der Datei   -----------------------------------------------------

def split_content(fpin,dbfile):
  """Inhalt aufteilen"""
  
  have_header=False
  last_rec = ""
  if os.path.isfile(dbfile+'.new'):
    os.remove(dbfile+'.new')
  db = sqlite3.connect(dbfile+'.new')
  cursor = db.cursor()

  total = 0
  total_add = 0
  buf_count =  0
  while True:
    # Buffer neu lesen
    buffer = fpin.read(BUFSIZE)
    buf_count = buf_count + 1
    if not buf_count%100:
      msg("INFO",'.',False)

    # Verarbeitung Dateiende (verbliebenen Satz schreiben)
    if len(buffer) == 0:
      if len(last_rec):
        total = total + 1
        tup = rec2tuple(last_rec[0:-1])
        if tup:
          total_add = total_add + 1
          cursor.execute(insert_stmt,tup)
        break

    # Sätze aufspalten
    records = re.split(',\n? +"X" ?: ?',last_rec+str(buffer))

    # Sätze ausgeben. Der letzte Satz ist entweder leer, 
    # oder er ist eigentlich ein Satzanfang und wird aufgehoben
    last_rec = records[-1]
    for record in records[0:-1]:
      if not have_header:
        insert_stmt = handle_header(record,cursor)
        have_header = True
        continue
      tup = rec2tuple(record)
      total = total + 1
      if tup:
        total_add = total_add + 1
        cursor.execute(insert_stmt,tup)

    # ein Commit pro BUFSIZE
    db.commit()

  # Datensätze speichern und Datenbank schließen
  db.commit()
  db.close()
  msg("INFO","\nAnzahl Buffer:              %d\n" % buf_count)
  msg("INFO","Anzahl Sätze (gesamt):      %d\n" % total)
  msg("INFO","Anzahl Sätze (gespeichert): %d\n" % total_add)

  # Alte Datenbank löschen und neue umbenennen
  if os.path.isfile(dbfile):
    os.remove(dbfile)
  os.rename(dbfile+'.new',dbfile)
  
    
# --- Update verarbeiten   --------------------------------------------------

def do_update(options):
  """Update der Filmliste"""

  if options.upd_src == "auto":
    # TODO: get download-url from list
    src = URL_FILMLISTE
  else:
    src = options.upd_src

  try:
    if src.startswith("http"):
      fpin = get_lzma_fp(get_url_fp(src))
    else:
      fpin = open(src,"r",encoding='utf-8')
    split_content(fpin,options.dbfile)
  finally:
    fpin.close()

# --- Filmliste anzeigen, Auswahl für späteren Download speichern    --------

def do_later(options):
  """Filmliste anzeigen, Auswahl für späteren Download speichern"""
  print("Vormerken noch nicht implementiert")

# --- Filmliste anzeigen, sofortiger Download nach Auswahl   ----------------

def do_now(options):
  """Filmliste anzeigen, sofortiger Download nach Auswahl"""
  print("Sofort noch nicht implementiert")

# --- Download vorgemerkter Filme   ------------------------------------------

def do_download(options):
  """Download vorgemerkter Filme"""
  print("Download noch nicht implementiert")

# --- Suche ohne Download   ---------------------------------------------------

def do_search(options):
  """Suche ohne Download"""
  print("Suche ohne Download noch nicht implementiert")

# --- Kommandozeilenparser   ------------------------------------------------

def get_parser():
  parser = ArgumentParser(add_help=False,
    description='Mediathekview auf der Kommandozeile')

  parser.add_argument('-A', '--akt', metavar='Quelle',
    dest='upd_src', nargs="?", default=None, const="auto",
    help='Filmliste aktualisieren (Quelle: auto|Url|Datei)')
  parser.add_argument('-V', '--vormerken', action='store_true',
    dest='doLater',
    help='Filmauswahl im Vormerk-Modus')
  parser.add_argument('-S', '--sofort', action='store_true',
    dest='doNow',
    help='Filmauswahl im Sofort-Modus')
  
  parser.add_argument('-D', '--download', action='store_true',
    dest='doDownload',
    help='Vorgemerkte Filme herunterladen')
  parser.add_argument('-Q', '--query', action='store_true',
    dest='doSearch',
    help='Filme suchen')

  parser.add_argument('-b', '--batch', action='store_true',
    dest='doBatch',
    help='Ausführung ohne User-Interface (zusammen mit -V und -S)')
  parser.add_argument('-z', '--ziel', metavar='dir', nargs=1,
    dest='target_dir',
    help='Zielverzeichnis')
  parser.add_argument('-d', '--db', metavar='Datei',
    dest='dbfile', default=SQLITE_DB_FILE,
    help='Datenbankdatei')
  parser.add_argument('-q', '--quiet', default=False, action='store_true',
    dest='quiet',
    help='Keine Meldungen ausgeben')
  parser.add_argument('-h', '--hilfe', action='help',
    help='Diese Hilfe ausgeben')

  parser.add_argument('suche', nargs='?', metavar='Suchausdruck',
    help='Sucheausdruck')
  return parser

# --- Hauptprogramm   -------------------------------------------------------

parser = get_parser()
options = parser.parse_args(namespace=Options)

if options.upd_src:
  do_update(options)
elif options.doLater:
  do_later(options)
elif options.doNow:
  do_now(options)
elif options.doDownload:
  do_download(options)
elif options.doSearch:
  do_search(options)
sys.exit(0)

