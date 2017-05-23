#!/usr/bin/python3
# -*- coding: utf-8 -*-
# --------------------------------------------------------------------------
# Mediathekview auf der Kommandozeile
#
# Definition der Klasse Msg
#
# Author: Bernhard Bablok
# License: GPL3
#
# Website: https://github.com/bablokb/mtv_cli
#
# --------------------------------------------------------------------------

import datetime, sys

class Msg(object):
  """Simple Klasse für Meldungen"""

  MSG_LEVELS={
    "TRACE":0,
    "DEBUG":1,
    "INFO":2,
    "WARN":3,
    "ERROR":4
    }

  level = "INFO"    # beim Initialisieren überschreiben

  # --- Ausgabe einer Meldung   ---------------------------------------------
  
  def msg(msg_level,text,nl=True):
    """Ausgabe einer Meldung"""
    if Msg.MSG_LEVELS[msg_level] >= Msg.MSG_LEVELS[Msg.level]:
      if nl:
        now = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        sys.stderr.write("[" + msg_level + "] " + "[" + now + "] " + text + "\n")
      else:
        sys.stderr.write(text)
        sys.stderr.flush()


