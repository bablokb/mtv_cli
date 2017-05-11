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

import datetime, sys
from mtv_cfg import *

BUFSIZE=8192

MSG_LEVELS={
  "DEBUG":1,
  "INFO":2,
  "WARN":3,
  "ERROR":4
  }

SEL_FORMAT = "{:7.7} | {:15.15} | {:8.8} | {:8.8} | {:46.46}"
SEL_TITEL  = SEL_FORMAT.format("Sender","Thema","Datum","Dauer","Titel")

# --- Meldung ausgeben   ----------------------------------------------------

def msg(level,text,nl=True):
  if MSG_LEVELS[level] >= MSG_LEVELS[MSG_LEVEL]:
    if nl:
      now = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
      sys.stderr.write("[" + level + "] " + "[" + now + "] " + text + "\n")
    else:
      sys.stderr.write(text)
    sys.stderr.flush()


