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
from pick import pick

# --- Konfiguration   -------------------------------------------------------

BUFSIZE=8192
MSG_LEVEL="INFO"
DATE_CUTOFF=30   # die letzten x-Tage werden gespeichert

URL_FILMLISTE="http://download10.onlinetvrecorder.com/mediathekview/Filmliste-akt.xz"

MTV_CLI_HOME=os.path.join(os.path.expanduser("~"),".mediathek3")
FILME_SQLITE=os.path.join(MTV_CLI_HOME,"filme.sqlite")
MTV_CLI_SQLITE=os.path.join(MTV_CLI_HOME,"mtv_cli.sqlite")

# --- Konstanten   ----------------------------------------------------------

MSG_LEVELS={
  "DEBUG":1,
  "INFO":2,
  "WARN":3,
  "ERROR":4
  }

COLS={
  "SENDER":          0,
  "THEMA":           1,
  "TITEL":           2,
  "DATUM":           3,
  "ZEIT":            4,
  "DAUER":           5,
  "GROESSE":         6,
  "BESCHREIBUNG":    7,
  "URL":             8,
  "WEBSITE":         9,
  "URL_UNTERTITEL": 10,
  "URL_RTMP":       11,
  "URL_KLEIN":      12,
  "URL_RTMP_KLEIN": 13,
  "URL_HD":         14,
  "URL_RTMP_HD":    15,
  "DATUML":         16,
  "URL_HISTORY":    17,
  "GEO":            18,
  "NEU":            19,
  "_ID":            20
  }

COLS_SEL={
  "SENDER":          0,
  "THEMA":           1,
  "TITEL":           2,
  "DATUM":           3,
  "BESCHREIBUNG":    4,
  "_ID":             5
  }

SEL_FORMAT = "{:7.7} | {:15.15} | {:8.8} | {:54.54}"
SEL_TITEL  = SEL_FORMAT.format("Sender","Thema","Datum", "Titel")

# --- Hilfsklasse für Optionen   --------------------------------------------

class Options(object):
  pass

# --- Meldung ausgeben   ----------------------------------------------------

def msg(level,text,nl=True):
  if MSG_LEVELS[level] >= MSG_LEVELS[MSG_LEVEL]:
    if nl:
      now = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
      sys.stderr.write("[" + level + "] " + "[" + now + "] " + text + "\n")
    else:
      sys.stderr.write(text)
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
      neu text,
      _id integer primary key )""")
  return 'INSERT INTO filme VALUES (' + 20 * '?,' + '?)'

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
_id = 1
def rec2tuple(record):
  """Ein Record in ein Tuple umwandeln. Dazu erzeugt der JSON-Parser erste
     eine Liste, die anschließend in ein Tuple umgewandelt wird. Damit die
     Datenbank nicht zu groß wird, werden nur Sätze der letzten x Tage
     zurückgegeben."""
  global last_liste, date_cutoff, _id
  try:
    liste = json.loads(record)
    if last_liste:
      # ersetzen leerer Werte durch Werte aus dem Satz davor
      for i in range(len(liste)):
        if not liste[i]:
          liste[i] = last_liste[i]
    last_liste = liste

    # Datum ins ISO-Format umwandeln und Cutoff
    datum_obj = to_date(liste[COLS['DATUM']])
    if datum_obj < date_cutoff:
      return None
    liste[COLS['DATUM']] = datum_obj.isoformat()


    # ID hinzufügen
    liste.append(_id)
    _id = _id + 1
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
    records = re.split(',\n? *"X" ?: ?',last_rec+str(buffer))
    msg("DEBUG","Anzahl Sätze: %d" % len(records))

    # Sätze ausgeben. Der letzte Satz ist entweder leer, 
    # oder er ist eigentlich ein Satzanfang und wird aufgehoben
    last_rec = records[-1]
    for record in records[0:-1]:
      msg("DEBUG",record)
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
  msg("INFO","\n",False)
  msg("INFO","Anzahl Buffer:              %d" % buf_count)
  msg("INFO","Anzahl Sätze (gesamt):      %d" % total)
  msg("INFO","Anzahl Sätze (gespeichert): %d" % total_add)

  # Alte Datenbank löschen und neue umbenennen
  if os.path.isfile(dbfile):
    os.remove(dbfile)
  os.rename(dbfile+'.new',dbfile)
  
    
# --- Update verarbeiten   --------------------------------------------------

def do_update(options):
  """Update der Filmliste"""

  if options.upd_src == "auto":
    # TODO: download-url aus Liste von Servern
    src = URL_FILMLISTE
  elif options.upd_src == "json":
    # existierende Filmliste verwenden
    src = os.path.join(MTV_CLI_HOME,"filme.json")
  else:
    src = options.upd_src

  msg("INFO","Erzeuge %s aus %s" % (options.dbfile,src))
  try:
    if src.startswith("http"):
      fpin = get_lzma_fp(get_url_fp(src))
    else:
      fpin = open(src,"r",encoding='utf-8')
    split_content(fpin,options.dbfile)
  finally:
    fpin.close()

# --- Interaktiv Suchbegriffe festlegen   -----------------------------------

def get_suche():
  suche_titel = "Auswahl Suchdetails"
  suche_opts  = ['Ende','Überall []', 'Sender []','Thema []',
                 'Titel []', 'Beschreibung []']
  suche_werte = {}
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
      suche_opts[index] = option[0:pos]  + " [" + begriff + "]"

  # Ergebnis extrahieren
  if len(suche_opts[1]) > len('Überall []'):
    return [re.split("\[|\]",suche_opts[1])[1]]
  else:
    result = []
    for opt in suche_opts[2:]:
      token  = re.split("\[|\]",opt)
      if len(token[1]) > 0:
        result.append(token[0].strip()+"="+token[1])
    return result

# --- Auswahlliste formatieren   --------------------------------------------

def get_select(result):
  select_liste = []
  for rec in result:
    sender=rec[COLS_SEL['SENDER']]
    thema=rec[COLS_SEL['THEMA']]
    titel=rec[COLS_SEL['TITEL']]
    datum=rec[COLS_SEL['DATUM']][8:10]+'.'+rec[3][5:7]+'.'+rec[3][2:4]
    select_liste.append(SEL_FORMAT.format(sender,thema,datum,titel))
  return select_liste
  
# --- Filmliste anzeigen, Auswahl für späteren Download speichern    --------

def do_later(options):
  """Filmliste anzeigen, Auswahl für späteren Download speichern"""
  if not options.suche:
    options.suche = get_suche()
  result = execute_query(options)
  selected = pick(get_select(result), "  "+SEL_TITEL,multi_select=True)
  print(selected)

# --- Filmliste anzeigen, sofortiger Download nach Auswahl   ----------------

def do_now(options):
  """Filmliste anzeigen, sofortiger Download nach Auswahl"""
  print("Sofort noch nicht implementiert")

# --- Download vorgemerkter Filme   -----------------------------------------

def do_download(options):
  """Download vorgemerkter Filme"""
  print("Download noch nicht implementiert")

# --- SQL-Query erzeugen   --------------------------------------------------

def get_query(suche):
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

# --- Suche ausführen, Ergebnis in Liste zurückgeben   ----------------------

def execute_query(options):
  """Suche ausführen"""
  if not os.path.isfile(options.dbfile):
    msg("ERROR","Datenbank existiert nicht!")
    return None

  db = sqlite3.connect(options.dbfile)
  cursor = db.cursor()
  statement = get_query(options.suche)
  cursor.execute(statement)
  result = cursor.fetchall()
  db.close()
  return result

# --- Suche ohne Download   -------------------------------------------------

def do_search(options):
  """Suche ohne Download"""
  result = execute_query(options)
  if result:
    if options.doBatch:
      for rec in result:
        print(rec)
    else:
      print(SEL_TITEL)
      print(len(SEL_TITEL)*'_')
      for line in get_select(result):
        print(line)

# --- Kommandozeilenparser   ------------------------------------------------

def get_parser():
  parser = ArgumentParser(add_help=False,
    description='Mediathekview auf der Kommandozeile')

  parser.add_argument('-A', '--akt', metavar='Quelle',
    dest='upd_src', nargs="?", default=None, const="auto",
    help='Filmliste aktualisieren (Quelle: auto|json|Url|Datei)')
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
    help='Ausführung ohne User-Interface (zusammen mit -V, -Q und -S)')
  parser.add_argument('-z', '--ziel', metavar='dir', nargs=1,
    dest='target_dir',
    help='Zielverzeichnis')
  parser.add_argument('-d', '--db', metavar='Datei',
    dest='dbfile', default=FILME_SQLITE,
    help='Datenbankdatei')
  parser.add_argument('-q', '--quiet', default=False, action='store_true',
    dest='quiet',
    help='Keine Meldungen ausgeben')
  parser.add_argument('-h', '--hilfe', action='help',
    help='Diese Hilfe ausgeben')

  parser.add_argument('suche', nargs='*', metavar='Suchausdruck',
    help='Sucheausdruck')
  return parser

# --- Hauptprogramm   -------------------------------------------------------

parser = get_parser()
options = parser.parse_args(namespace=Options)

# Verzeichnis HOME/.mediathek3 anlegen
if not os.path.exists(MTV_CLI_HOME):
  os.mkdir(MTV_CLI_HOME)

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

