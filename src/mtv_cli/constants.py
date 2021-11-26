# Mediathekview auf der Kommandozeile
#
# Konstanten und globale Funktionen
#
# Author: Bernhard Bablok, Max Görner
# License: GPL3
#
# Website: https://github.com/bablokb/mtv_cli
#

import os
from pathlib import Path

VERSION = 2  # Erhöhung nur bei inkompatiblen Änderungen


SEL_FORMAT = "{:7.7}|{:15.15}|{:8.8}|{}|{:52.52}"
SEL_TITEL = SEL_FORMAT.format("Sender", "Thema", "Datum", "Dauer", "Titel")

DLL_FORMAT = "{:1.1}|{:8.8}|{:7.7}|{:8.8}|{:8.8}|{:8.8}|{:58.58}"
DLL_TITEL = ("St" + DLL_FORMAT).format(
    "a", "S-Datum", "Sender", "Thema", "Datum", "Dauer", "Titel"
)

DEFAULT_CONFIG_DIR = Path("~/.config/").expanduser()
DEFAULT_CACHE_DIR = Path("~/.cache/").expanduser()

MTV_CLI_HOME = Path("~").expanduser() / ".mediathek3"
MTV_CLI_CONFIG = Path(os.getenv("XDG_CONFIG_HOME", DEFAULT_CONFIG_DIR)) / "mtv-cli.cfg"
FILME_SQLITE = Path(os.getenv("XDG_CACHE_HOME", DEFAULT_CACHE_DIR)) / "mtv-cli.sqlite"

URL_FILMLISTE = "https://liste.mediathekview.de/Filmliste-akt.xz"
