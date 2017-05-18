# -*- coding: utf-8 -*-
# --------------------------------------------------------------------------
# Mediathekview auf der Kommandozeile
#
# Konstanten und globale Funktionen
#
# Author: Bernhard Bablok
# License: GPL3
#
# Website: https://github.com/bablokb/mtv_cli
#
# --------------------------------------------------------------------------

import os, datetime, sys
from mtv_cfg import *

BUFSIZE=8192

# --- Titel   ---------------------------------------------------------------

SEL_FORMAT = "{:7.7}|{:15.15}|{:8.8}|{:8.8}|{:52.52}"
SEL_TITEL  = SEL_FORMAT.format("Sender","Thema","Datum","Dauer","Titel")

DLL_FORMAT = "{:1.1}|{:8.8}|{:7.7}|{:8.8}|{:8.8}|{:8.8}|{:58.58}"
DLL_TITEL  = ("St"+DLL_FORMAT).format("a","S-Datum","Sender","Thema","Datum","Dauer","Titel")

# --- Pfade   ---------------------------------------------------------------

MTV_CLI_HOME=os.path.join(os.path.expanduser("~"),".mediathek3")
FILME_SQLITE=os.path.join(MTV_CLI_HOME,"filme.sqlite")
MTV_CLI_SQLITE=os.path.join(MTV_CLI_HOME,"mtv_cli.sqlite")

# --- Meldung ausgeben   ----------------------------------------------------

MSG_LEVELS={
  "DEBUG":1,
  "INFO":2,
  "WARN":3,
  "ERROR":4
  }

def msg(level,text,nl=True):
  if MSG_LEVELS[level] >= MSG_LEVELS[MSG_LEVEL]:
    if nl:
      now = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
      sys.stderr.write("[" + level + "] " + "[" + now + "] " + text + "\n")
    else:
      sys.stderr.write(text)
    sys.stderr.flush()


# --- Downlaod-URLs   --------------------------------------------------------

URL_FILMLISTE=[
  "http://verteiler4.mediathekview.de/Filmliste-akt.xz",
  "http://verteiler5.mediathekview.de/Filmliste-akt.xz",
  "http://verteiler6.mediathekview.de/Filmliste-akt.xz",
  "http://download10.onlinetvrecorder.com/mediathekview/Filmliste-akt.xz",
  "http://mediathekview.jankal.me/Filmliste-akt.xz",
  "http://verteiler1.mediathekview.de/Filmliste-akt.xz",
  "http://verteiler2.mediathekview.de/Filmliste-akt.xz",
  "http://verteiler3.mediathekview.de/Filmliste-akt.xz"
  ]

