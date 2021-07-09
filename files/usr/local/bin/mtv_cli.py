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

# --- System-Imports   -----------------------------------------------------

from argparse import ArgumentParser
import sys, os, re, lzma, random, fcntl
import urllib.request as request
import ssl
import configparser

from pick import pick

# --- eigene Imports   ------------------------------------------------------

from mtv_const    import (
    BUFSIZE,
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
from mtv_filmdb   import FilmDB as FilmDB
from mtv_msg      import Msg as Msg

# --- Hilfsklasse für Optionen   --------------------------------------------

class Options:
  pass

# --- Stream der Filmliste   ------------------------------------------------

def get_url_fp(url):
  """ URL öffnen und Filepointer zurückgeben"""
  return request.urlopen(url,context=ssl.SSLContext())

# --- Stream des LZMA-Entpackers   ------------------------------------------

def get_lzma_fp(url_fp):
  """ Filepointer des LZMA-Entpackers. Argument ist der FP der URL"""
  return lzma.open(url_fp,"rt",encoding='utf-8')

# --- Split der Datei   -----------------------------------------------------

def split_content(fpin,filmDB):
  """Inhalt aufteilen"""

  have_header=False
  last_rec = ""

  filmDB.create_filmtable()
  filmDB.isolation_level = None
  filmDB.cursor.execute("BEGIN;")

  total = 0
  buf_count =  0
  regex = re.compile(',\n? *"X" ?: ?')
  while True:
    # Buffer neu lesen
    buffer = fpin.read(BUFSIZE)
    buf_count = buf_count + 1
    if not buf_count%100:
      Msg.msg("INFO",'.',False)

    # Verarbeitung Dateiende (verbliebenen Satz schreiben)
    if len(buffer) == 0:
      if len(last_rec):
        total = total + 1
        filmDB.insert_film(last_rec[0:-1])
        break

    # Sätze aufspalten
    records = regex.split(last_rec+str(buffer))
    Msg.msg("DEBUG","Anzahl Sätze: %d" % len(records))

    # Sätze ausgeben. Der letzte Satz ist entweder leer,
    # oder er ist eigentlich ein Satzanfang und wird aufgehoben
    last_rec = records[-1]
    for record in records[0:-1]:
      Msg.msg("TRACE",record)
      if not have_header:
        have_header = True
        continue
      total = total + 1
      filmDB.insert_film(record)

  # Datensätze speichern und Datenbank schließen
  filmDB.commit()
  filmDB.save_filmtable()

  Msg.msg("INFO","\n",False)
  Msg.msg("INFO","Anzahl Buffer:              %d" % buf_count)
  Msg.msg("INFO","Anzahl Sätze (gesamt):      %d" % total)
  Msg.msg("INFO","Anzahl Sätze (gespeichert): %d" % filmDB.get_count())


# --- Update verarbeiten   --------------------------------------------------

def do_update(options):
  """Update der Filmliste"""

  if options.upd_src == "auto":
    src = random.choice(URL_FILMLISTE)
  elif options.upd_src == "json":
    # existierende Filmliste verwenden
    src = os.path.join(MTV_CLI_HOME,"filme.json")
  else:
    src = options.upd_src

  Msg.msg("INFO","Erzeuge %s aus %s" % (options.dbfile,src))
  fpin = None
  try:
    if src.startswith("http"):
      fpin = get_lzma_fp(get_url_fp(src))
    else:
      fpin = open(src,"r",encoding='utf-8')
    split_content(fpin,options.filmDB)
  except Exception as e:
    Msg.msg("ERROR","Update der Filmliste gescheitert. Fehler: %s" % e)
  finally:
    if fpin is not None:
      fpin.close()

# --- Interaktiv Suchbegriffe festlegen   -----------------------------------

def get_suche():
  suche_titel = "Auswahl Suchdetails"
  suche_opts  = ['Weiter','Global []', 'Sender []','Datum []','Thema []',
                 'Titel []', 'Beschreibung []']
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
  if len(suche_opts[1]) > len('Global []'):
    return [re.split(r"\[|\]",suche_opts[1])[1]]
  else:
    result = []
    for opt in suche_opts[2:]:
      token  = re.split(r"\[|\]",opt)
      if len(token[1]) > 0:
        result.append(token[0].strip()+":"+token[1])
    return result

# --- Auswahlliste formatieren   --------------------------------------------

def get_select(rows):
  select_liste = []
  for row in rows:
    sender=row['SENDER']
    thema=row['THEMA']
    titel=row['TITEL']
    datum=row['DATUM'].strftime("%d.%m.%y")
    dauer=row['DAUER']
    select_liste.append(SEL_FORMAT.format(sender,thema,datum,dauer,titel))
  return select_liste

# --- Filme suchen   --------------------------------------------------------

def filme_suchen(options):
  """Filme gemäß Vorgabe suchen"""
  if not options.suche:
    options.suche = get_suche()

  statement = options.filmDB.get_query(options.suche)
  return options.filmDB.execute_query(statement)

# --- Filme zur Auswahl anzeigen   ------------------------------------------

def zeige_liste(rows):
  """ Filmliste anzeigen, Auswahl zurückgeben"""
  return pick(get_select(rows), "  "+SEL_TITEL,multi_select=True)

# --- Ergebnisse für späteren Download speichern   --------------------------

def save_selected(filmDB,rows,selected,status):
  """ Auswahl speichern """

  # Datenstruktuer erstellen
  inserts = []
  for sel_text,sel_index in selected:
    row = rows[sel_index]
    inserts.append((row['_ID'],row['DATUM'],status))
  return filmDB.save_downloads(inserts)

# --- Filmliste anzeigen, Auswahl für späteren Download speichern    --------

def do_later(options):
  """Filmliste anzeigen, Auswahl für späteren Download speichern"""
  _do_now_later_common_body(options, do_now=False)

# --- Filmliste anzeigen, sofortiger Download nach Auswahl   ----------------

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
    Msg.msg("INFO","Keine Suchtreffer")
    return 0

  if options.doBatch:
    selected = [('dummy',i) for i in range(len(rows))]
  else:
    selected = zeige_liste(rows)
  num_changes = save_selected(options.filmDB,rows,selected,save_selected_status)
  Msg.msg("INFO","%d von %d Filme vorgemerkt für %sDownload" % (num_changes,len(selected),when_download_wording))
  return num_changes


# --- Download vorgemerkter Filme   -----------------------------------------

def do_download(options):
  """Download vorgemerkter Filme"""
  if options.doNow:
    # Aufruf aus do_now
    download_filme(options,status="'S'")
  else:
    download_filme(options)

# --- Suche ohne Download   -------------------------------------------------

def do_search(options):
  """Suche ohne Download"""

  rows = filme_suchen(options)
  if rows:
    if options.doBatch:
      print("[")
      for row in rows:
        rdict = dict(row)
        if 'Datum' in rdict:
          rdict['Datum'] = rdict['Datum'].strftime("%d.%m.%y")
        print(rdict,end='')
        print(",")
      print("]")
    else:
      print(SEL_TITEL)
      print(len(SEL_TITEL)*'_')
      for row in get_select(rows):
        print(row)
    return True
  else:
    return False

# --- Downloadliste anzeigen und editieren   --------------------------------

def do_edit(options):
  """Downloadliste anzeigen und editieren"""

  # Liste lesen
  rows = options.filmDB.read_downloads()
  if not rows:
    Msg.msg("INFO","Keine vorgemerkten Filme vorhanden")
    return

  # Liste aufbereiten
  select_liste = []
  for row in rows:
    status=row['STATUS']
    datum_status=row['DATUMSTATUS'].strftime("%d.%m.%y")
    sender=row['SENDER']
    thema=row['THEMA']
    titel=row['TITEL']
    dauer=row['DAUER']
    datum=row['DATUM'].strftime("%d.%m.%y")

    select_liste.append(DLL_FORMAT.format(status,datum_status,
                                          sender,thema,datum,dauer,titel))
  selected = pick(select_liste, DLL_TITEL,multi_select=True)

  # IDs extrahieren und Daten löschen
  deletes = []
  for sel_text,sel_index in selected:
    row = rows[sel_index]
    deletes.append((row['_ID'],))
  if len(deletes):
    changes = options.filmDB.delete_downloads(deletes)
  else:
    changes = 0
  Msg.msg("INFO","%d vorgemerkte Filme gelöscht" % changes)


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
  parser.add_argument('-E', '--edit', action='store_true',
    dest='doEdit',
    help='Downloadliste bearbeiten')

  parser.add_argument('-D', '--download', action='store_true',
    dest='doDownload',
    help='Vorgemerkte Filme herunterladen')
  parser.add_argument('-Q', '--query', action='store_true',
    dest='doSearch',
    help='Filme suchen')

  parser.add_argument('-b', '--batch', action='store_true',
    dest='doBatch',
    help='Ausführung ohne User-Interface (zusammen mit -V, -Q und -S)')
  parser.add_argument('-d', '--db', metavar='Datei',
    dest='dbfile', default=FILME_SQLITE,
    help='Datenbankdatei')

  parser.add_argument('-q', '--quiet', default=False, action='store_true',
    dest='quiet',
    help='Keine Meldungen ausgeben')
  parser.add_argument('-l', '--level', metavar='Log-Level',
    dest='level', default=None,
    help='Meldungen ab angegebenen Level ausgeben')
  parser.add_argument('--version', action='store_true',
    dest='doVersionInfo',
    help='Ausgabe Versionsnummer')
  parser.add_argument('-h', '--hilfe', action='help',
    help='Diese Hilfe ausgeben')

  parser.add_argument('suche', nargs='*', metavar='Suchausdruck',
    help='Suchausdruck')
  return parser

# --- Lock anfordern  -------------------------------------------------------

def get_lock(datei):
  global fd_datei

  if not os.path.isfile(datei):
    return True

  fd_datei = open(datei,"r")
  try:
    lock = fcntl.flock(fd_datei,fcntl.LOCK_NB | fcntl.LOCK_EX)
    return True
  except IOError:
    return False

# --- Konfigurationsobjekt erzeugen   ---------------------------------------

def get_config(parser):
  return {
    "MSG_LEVEL":         parser.get('CONFIG',"MSG_LEVEL"),
    "DATE_CUTOFF":       parser.getint('CONFIG',"DATE_CUTOFF"),
    "DAUER_CUTOFF":      parser.getint('CONFIG',"DAUER_CUTOFF"),
    "NUM_DOWNLOADS":     parser.getint('CONFIG',"NUM_DOWNLOADS"),
    "ZIEL_DOWNLOADS":    parser.get('CONFIG',"ZIEL_DOWNLOADS"),
    "CMD_DOWNLOADS":     parser.get('CONFIG',"CMD_DOWNLOADS"),
    "CMD_DOWNLOADS_M3U": parser.get('CONFIG',"CMD_DOWNLOADS_M3U"),
    "QUALITAET":         parser.get('CONFIG',"QUALITAET")
    }

# --- Hauptprogramm   -------------------------------------------------------

if __name__ == '__main__':

  config_parser = configparser.RawConfigParser()
  config_parser.read('/etc/mtv_cli.conf')
  try:
    config = get_config(config_parser)
  except Exception as e:
    print("Konfiguration fehlerhaft!")
    print("Fehler: %s" % e.message)
    sys.exit(3)

  opt_parser = get_parser()
  options = opt_parser.parse_args(namespace=Options)
  if options.doVersionInfo:
    print("Version: %s" % VERSION)
    sys.exit(0)

  # Message-Klasse konfigurieren
  if options.level:
    Msg.level = options.level
  else:
    Msg.level = config["MSG_LEVEL"]

  # Verzeichnis HOME/.mediathek3 anlegen
  if not os.path.exists(MTV_CLI_HOME):
    os.mkdir(MTV_CLI_HOME)

  if not options.upd_src and not os.path.isfile(options.dbfile):
    Msg.msg("ERROR","Datenbank %s existiert nicht!" % options.dbfile)
    sys.exit(3)

  # Lock anfordern
  if not get_lock(options.dbfile):
    Msg.msg("ERROR","Datenbank %s ist gesperrt" % options.dbfile)
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

