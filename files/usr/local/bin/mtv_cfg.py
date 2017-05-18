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

import os, datetime

MSG_LEVEL="INFO"
DATE_CUTOFF=30   # die letzten x-Tage werden gespeichert
DAUER_CUTOFF=5   # nur Filme >= 5 Minuten werden gespeichert

NUM_DOWNLOADS=2
ZIEL_DOWNLOADS="/data/videos/{Sender}_{Datum}_{Thema}_{Titel}.{ext}"
CMD_DOWNLOADS="wget -q -c -O '{ziel}' '{url}'"
GROESSE_DOWNLOADS="LOW"    # HD, SD, LOW

# Pfade

MTV_CLI_HOME=os.path.join(os.path.expanduser("~"),".mediathek3")
FILME_SQLITE=os.path.join(MTV_CLI_HOME,"filme.sqlite")
MTV_CLI_SQLITE=os.path.join(MTV_CLI_HOME,"mtv_cli.sqlite")

# --- ab hier nichts ändern   -----------------------------------------------

# Downlaod-URLs

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

date_cutoff=datetime.date.today() - datetime.timedelta(days=DATE_CUTOFF)
