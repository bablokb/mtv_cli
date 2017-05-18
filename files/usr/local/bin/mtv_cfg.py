# -*- coding: utf-8 -*-
# --------------------------------------------------------------------------
# Mediathekview auf der Kommandozeile
#
# Konfigurationseinstellungen
#
# Author: Bernhard Bablok
# License: GPL3
#
# Website: https://github.com/bablokb/mtv_cli
#
# --------------------------------------------------------------------------

MSG_LEVEL="INFO"
DATE_CUTOFF=30   # die letzten x-Tage werden gespeichert
DAUER_CUTOFF=5   # nur Filme >= 5 Minuten werden gespeichert

NUM_DOWNLOADS=2
ZIEL_DOWNLOADS="/data/videos/{Sender}_{Datum}_{Thema}_{Titel}.{ext}"
CMD_DOWNLOADS="wget -q -c -O '{ziel}' '{url}'"
GROESSE_DOWNLOADS="LOW"    # HD, SD, LOW
