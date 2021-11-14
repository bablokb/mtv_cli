# Mediathekview auf der Kommandozeile
#
# Konstanten und globale Funktionen
#
# Author: Bernhard Bablok, Max Görner
# License: GPL3
#
# Website: https://github.com/bablokb/mtv_cli
#

from pathlib import Path

VERSION = 2  # Erhöhung nur bei inkompatiblen Änderungen


SEL_FORMAT = "{:7.7}|{:15.15}|{:8.8}|{:8.8}|{:52.52}"
SEL_TITEL = SEL_FORMAT.format("Sender", "Thema", "Datum", "Dauer", "Titel")

DLL_FORMAT = "{:1.1}|{:8.8}|{:7.7}|{:8.8}|{:8.8}|{:8.8}|{:58.58}"
DLL_TITEL = ("St" + DLL_FORMAT).format(
    "a", "S-Datum", "Sender", "Thema", "Datum", "Dauer", "Titel"
)


MTV_CLI_HOME = Path("~").expanduser() / ".mediathek3"
FILME_SQLITE = MTV_CLI_HOME / "filme.sqlite"
MTV_CLI_SQLITE = MTV_CLI_HOME / "mtv_cli.sqlite"

URL_FILMLISTE = "https://liste.mediathekview.de/Filmliste-akt.xz"
