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

# Downlaod-URLs

URL_FILMLISTE="http://download10.onlinetvrecorder.com/mediathekview/Filmliste-akt.xz"
NUM_DOWNLOADS=2
ZIEL_DOWNLOADS="/data/videos/{Sender}_{Datum}_{Thema}_{Titel}.mp4"

# Pfade

MTV_CLI_HOME=os.path.join(os.path.expanduser("~"),".mediathek3")
FILME_SQLITE=os.path.join(MTV_CLI_HOME,"filme.sqlite")
MTV_CLI_SQLITE=os.path.join(MTV_CLI_HOME,"mtv_cli.sqlite")

# --- ab hier nichts ändern   -----------------------------------------------

date_cutoff=datetime.date.today() - datetime.timedelta(days=DATE_CUTOFF)
