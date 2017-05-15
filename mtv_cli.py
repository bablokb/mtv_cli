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
import sys, os, re, lzma, datetime
import urllib.request as request
from pick import pick

# --- eigene Imports   ------------------------------------------------------

from mtv_const import *
from mtv_cfg import *
from mtv_download import *
from mtv_filmdb import FilmDB as FilmDB

# --- Hilfsklasse für Optionen   --------------------------------------------

class Options(object):
  pass

# --- Stream der Filmliste   ------------------------------------------------

def get_url_fp(url):
  """ URL öffnen und Filepointer zurückgeben"""
  # TODO: Austausch, da request.urlopen keine Server-SSLs überprüft
  return request.urlopen(url)

# --- Stream des LZMA-Entpackers   ------------------------------------------

def get_lzma_fp(url_fp):
  """ Fileponter des LZMA-Entpackers. Argument ist der FP der URL"""
  return lzma.open(url_fp,"rt",encoding='utf-8')

# --- Split der Datei   -----------------------------------------------------

def split_content(fpin,filmDB):
  """Inhalt aufteilen"""
  
  have_header=False
  last_rec = ""

  filmDB.create()
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
      msg("INFO",'.',False)

    # Verarbeitung Dateiende (verbliebenen Satz schreiben)
    if len(buffer) == 0:
      if len(last_rec):
        total = total + 1
        filmDB.insert(last_rec[0:-1])
        break

    # Sätze aufspalten
    records = regex.split(last_rec+str(buffer))
    msg("DEBUG","Anzahl Sätze: %d" % len(records))

    # Sätze ausgeben. Der letzte Satz ist entweder leer, 
    # oder er ist eigentlich ein Satzanfang und wird aufgehoben
    last_rec = records[-1]
    for record in records[0:-1]:
      msg("DEBUG",record)
      if not have_header:
        have_header = True
        continue
      total = total + 1
      filmDB.insert(record)

  # Datensätze speichern und Datenbank schließen
  filmDB.commit()
  filmDB.save()

  msg("INFO","\n",False)
  msg("INFO","Anzahl Buffer:              %d" % buf_count)
  msg("INFO","Anzahl Sätze (gesamt):      %d" % total)
  msg("INFO","Anzahl Sätze (gespeichert): %d" % filmDB.get_count())

    
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
    split_content(fpin,options.filmDB)
  finally:
    fpin.close()

# --- Interaktiv Suchbegriffe festlegen   -----------------------------------

def get_suche():
  suche_titel = "Auswahl Suchdetails"
  suche_opts  = ['Weiter','Global []', 'Sender []','Datum []','Thema []',
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
  if len(suche_opts[1]) > len('Global []'):
    return [re.split("\[|\]",suche_opts[1])[1]]
  else:
    result = []
    for opt in suche_opts[2:]:
      token  = re.split("\[|\]",opt)
      if len(token[1]) > 0:
        result.append(token[0].strip()+"="+token[1])
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
  rows = filme_suchen(options)
  if options.doBatch:
    selected = [('dummy',i) for i in range(len(rows))]
  else:
    selected = zeige_liste(rows)
  changes = save_selected(options.filmDB,rows,selected,"V")
  msg("INFO","%d von %d Filme vorgemerkt für den Download" % (changes,len(selected)))

# --- Filmliste anzeigen, sofortiger Download nach Auswahl   ----------------

def do_now(options):
  """Filmliste anzeigen, sofortiger Download nach Auswahl"""
  rows = filme_suchen(options)
  if options.doBatch:
    selected = [('dummy',i) for i in range(len(rows))]
  else:
    selected = zeige_liste(rows)
  changes = save_selected(options.filmDB,rows,selected,"S")
  msg("INFO","%d von %d Filme vorgemerkt für Sofort-Download" % (changes,len(selected)))

  # Anstoß Downlaod
  if changes > 0:
    do_download(options)

# --- Download vorgemerkter Filme   -----------------------------------------

def do_download(options):
  """Download vorgemerkter Filme"""
  if options.doNow:
    # Aufruf aus do_now
    download_filme(options.filmDB,status="'S'")
  else:
    download_filme(options.filmDB)

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

# --- Downloadliste anzeigen und editieren   --------------------------------

def do_edit(options):
  """Downloadliste anzeigen und editieren"""

  # Liste lesen
  rows = options.filmDB.read_downloads()
  if not rows:
    msg("INFO","Keine vorgemerkten Filme vorhanden")
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
  msg("INFO","%d vorgemerkte Filme gelöscht" % changes)


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

if __name__ == '__main__':
  parser = get_parser()
  options = parser.parse_args(namespace=Options)

  # Verzeichnis HOME/.mediathek3 anlegen
  if not os.path.exists(MTV_CLI_HOME):
    os.mkdir(MTV_CLI_HOME)

  if not options.upd_src and not os.path.isfile(options.dbfile):
    msg("ERROR","Datenbank %s existiert nicht!" % options.dbfile)
    sys.exit(3)

  # Globale Objekte anlegen
  options.filmDB = FilmDB(options.dbfile)

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
    do_search(options)
  sys.exit(0)

