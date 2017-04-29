# -*- coding: utf-8 -*-
# --------------------------------------------------------------------------
# Mediathekview auf der Kommandozeile
#
# Konstanten
#
# Author: Bernhard Bablok
# License: GPL3
#
# Website: https://github.com/bablokb/mtv_cli
#
# --------------------------------------------------------------------------

BUFSIZE=8192

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

