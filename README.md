Mediathekview auf der Kommandozeile
===================================

Mediathekview ist eine sehr gute Anwendung, ist aber nicht auf der
Kommandozeile verwendbar.

Das Kommando `mtv-cli` läuft dagegen auch ohne grafische Oberfläche,
etwa wenn man sich per SSH auf einen Pi mit Kodi-Distribution einlogged.

Die Kommandozeilenversion von Mediathekview wird nie den Funktionsumfang des
Originals erhalten. Es geht um eine einfache, schlanke Lösung die sich eher
an Experten, denn an absolute Laien richtet.

Die Anwendung verwendet die Mediathekview-Filmliste, allerdings konvertiert
in ein richtiges Datenbankformat.


Installation
------------

Das Programm kann wie jedes andere Python-Projekt auch installiert werden. Es
wird angeraten, dafür `pipx` zu verwenden, da `pipx` für jedes Programm
eine eigene virtuelle Umgebung pflegt.

    poetry build
    pipx install dist/mtv-cli*tar.gz

Danach steht das Programm als `mtv-cli` zur Verfügung.

Um die Filmlistenauffrischung und das Herunterladen vorgemerkter Filme
mit Cron zu automatisieren, kann das Skript `tools/registriere-cronjobs`
ausgeführt werden.

Status/Neuigkeiten
------------------

### Version 8 / ??? ###
  - Erstellung neuer Kommandozeilenschnittstelle mit Unterkommandos
  - Installation des Programmes zu `pip` bzw. `pipx` kompatibel gemacht
  - Abhängigkeit zu externem Downloadprogramm entfernt
  - Konfigurationsdatei und Filmdatenbank werden XDG-konform abgelegt
  - Einige Vereinfachungen / Modernisierungen des Quellcodes

### Version 7 / 09.07.21 ###

  - Codebereinigungen und Fixe (implementiert von MaxG87)
  - Anpassungen Verteilerliste (implementiert von MaxG87)

### Version 6 / 30.03.20 ###

  - Support für Docker (implementiert von Skyr)

### Version 5 / 13.02.19 ###

  - Neuer Hauptmenüpunkt "Dateien". Filmdateien auf dem Server können
    heruntergeladen oder gelöscht werden. Alte Aufnahmen sind in der
    Dateiliste nicht sichtbar, sondern nur Filme, die seit dem Update
    heruntergeladen wurden.

### Version 4 / 18.11.18 ###

  - Unterstützung von m3u-Links (Playlisten). Manche Sender bieten keine
    kompletten mp4-Dateien mehr zum Download an, sondern nur ein Playliste
    mit einer Liste von Fragmenten. Diese werden jetzt auf einmal
    heruntergeladen und zusammengesetzt. **Nach dem Update mit
    `sudo tools/install-mtv_cli` muss noch die eigene `/etc/mtv_cli.conf`
    angepasst werden (Variable `CMD_DOWNLOADS_M3U` von der
    `/etc/mtv_cli.conf.neu` übernehmen).**

### Version 3 / 12.12.17 ###

  - Beschreibung der Sendung (Tooltip Mouse-over beim Titel). Funktioniert
    leider nicht bei mobilen Browsern.

### Version 2 / 02.07.17 ###

  - Die Bearbeitung der Vormerkliste funktioniert jetzt auch.

### Version 2 / 30.06.17 ###

  - Das Webinterface ist fast komplett, man kann jetzt Filme für den Download
    vormerken, den Download anstoßen und auch eine Aktualisierung der
    Filmliste aus dem Webinterface heraus starten. Nur die Bearbeitung der
    Vormerkliste funktioniert nicht.
  - Die Installation legt Crontab-Einträge für die automatische Aktualisierung
    und den Download an.
  - Die Konfiguration des Beispielskripts `mtv_sendinfo` wurde nach
    `/etc/mtv_sendinfo.rc` bzw. `~/.mtv_sendinforc` ausgelagert.
  - Die Versionsnummer bleibt bei 2, da sich keine strukturellen Änderungen
    am Datenmodell ergeben haben. Es scheint aber leider so zu sein,
    dass auch die neue ID-Funktion nicht stabil ist - hier ist noch eine
    Änderung zu erwarten.


### Version 2 / 15.06.17 ###

Diese Version enthält hauptsächlich Bugfixes und kleinere Optimierungen.
Desweiteren enthält diese Version ein rudimentäres Webinterface. Aktuell
funktioniert nur die Suche (allerdings noch mit unbefriedigendem Layout).

Die Version 2 ändert die intern generierte ID der Filme. Diese hat sich in
der vorherigen Version nicht als stabil erwiesen. Als Folge sind alle in
der Download-Tabelle gespeicherten Einträge nicht mehr gültig. Es wird
deshalb empfohlen, alle vorgemerkten Filme noch mit der alten Version
herunterzuladen, danach den Update durchzuführen und dann die Datei
`~/.mediathek3/filme.sqlite` zu löschen. Momentan wird noch untersucht, ob
die neue ID-Funktion funktioniert.

### Version 1 ###

Erstes Release mit der Grundfunktionalität.

Installation
------------

Voraussetzungen:

  - Python3
  - python3-curses
  - python3-bottle
  - pick

Das Skript `tools/install-mtv_cli` (per sudo aufrufen) installiert das
Programm und alle Voraussetzungen automatisch. **Wer einen anderen
Standarduser anstatt `pi` verwendet, muss die Variable `MTV_CLI_USER` im
Installationsskript anpassen**.

Während der Installation wird ein neuer Systemd-Service angelegt:
`mtv_web.service`. Die Konfiguration erfolgt in `/etc/mtv_cli.conf`, Abschnitt
`[WEB]` (momentan ist das nur Port und IP-Bereich). Der Default-Port
für den Webserver ist 8026. Gestartet wird der Service über

    sudo systemctl start mtv_web.service

oder durch einen Reboot. Wer den Service nicht nutzen will, schaltet ihn mit

    sudo systemctl disable mtv_web.service

ab.

Außerdem legt das Installationsskript in `/etc/cron.d/mtv_cli` Einträge
für die Aktualisierung der Filmliste und den Download der vorgemerkten
Filme an. Damit nicht jede Installation die Filmliste zum selben Zeitpunkt
aktualisiert, wählt die Installation einen zufälligen Zeitpunkt. Die
Datei ist deshalb an eigene Bedürfnisse anzupassen.

**Nach der Installation sollte auf alle Fälle die Variable `ZIEL_DOWNLOADS`
in der Konfiguration angepasst werden!** Details zur Konfiguration sind
weiter unten beschrieben.


Verwendung
----------

Über die Option `-h` gibt das Programm die verfügbaren Optionen aus:


    usage: mtv_cli.py [-A [Quelle]] [-V] [-S] [-D] [-Q] [-b] [-z dir] [-d Datei]
                      [-q] [-l Log-Level] [--version] [-h]
                      [Suchausdruck [Suchausdruck ...]]]

    Mediathekview auf der Kommandozeile

    positional arguments:
      Suchausdruck          Suchausdruck

    optional arguments:
      -A [Quelle], --akt [Quelle]
                            Filmliste aktualisieren (Quelle: auto|json|Url|Datei)
      -V, --vormerken       Filmauswahl im Vormerk-Modus
      -S, --sofort          Filmauswahl im Sofort-Modus
      -E, --edit            Downloadliste bearbeiten
      -D, --download        Vorgemerkte Filme herunterladen
      -Q, --query           Filme suchen
      -b, --batch           Ausführung ohne User-Interface (zusammen mit -V, -Q
                            und -S)
      -d Datei, --db Datei  Datenbankdatei
      -q, --quiet           Keine Meldungen ausgeben
      -l Log-Level, --level Log-Level
                            Meldungen ab angegebenen Level ausgeben
      --version             Ausgabe der Versionsnummer
      -h, --hilfe           Diese Hilfe ausgeben


Beim Aufruf mit `-A` (aktualisieren) kann ein zusätzlicher Parameter mitgegeben
werden. `auto` holt die Daten aus dem Netz mit einer zufälligen URL. Der
Parameter `json` sorgt dafür, dass die `filmliste.json` (Heruntergeladen
mit der Originalanwendung) als Quelle dient. Alternativ kann noch eine
spezifische Url oder ein Dateiname angegeben werden.

Die Option `-S` startet den Download direkt nach der Filmauswahl. `-V` dagegen
trägt die Filme in eine Vormerkliste ein. Hier muss der Download explizit
per `-D` angestoßen werden (idealerweise per Cronjob). Mit `-E` können
Filme aus der Vormerkliste gelöscht werden.

Im Batch-Modus `-b` gibt es keine Interaktion mit dem Benutzer. Hier müssen
unbedingt Suchbegriffe auf der Kommandozeile angegeben werden.

Die Option `-l` (bzw. `--level`) überschreibt den Wert von `MSG_LEVEL` in
der Konfigurationsdatei `/etc/mtv_cli.conf`. Über die Option kann kurzfristig
für Debugzwecke die Geschwätzigkeit des Skripts angepasst werden.


Syntax für die Suche
--------------------

Für die Suche gibt es zwei Möglichkeiten, die Eingabe auf der Kommandozeile
oder in eine Suchmaske. Letztere wird eingeblendet, wenn kein Suchausdruck
auf der Kommandozeile angegeben wird.

Auf der Kommandozeile unterscheidet das Programm drei mögliche Arten der
Sucheingabe:

  - rohes SQL, eingeleitet durch ein `select`
  - die globale generische Volltextsuche
  - Suche in einzelnen Feldern

Die erste Möglichkeit ist etwas für Experten. Die zweite Möglichkeit sucht
in den Feldern Sender, Thema, Titel und Beschreibung:

    > mtv_cli.py -Q Terra X
    > mtv_cli.py -Q "Terra X"

Der erste Aufruf sucht nach "Terra" oder "X" ohne Berücksichtigung von
Groß-/Kleinschreibung. Der zweite Aufruf sucht nach "Terra X". Es wird
automatisch mit Wildcards gesucht, deshalb führt ein "\*Terra X\*" oder
"%Terra X%" nicht zum Erfolg.

Die Suche kann auf einzelne Felder (Sender, Thema, Datum, Titel, Beschreibung)
begrenzt werden:

    > mtv_cli.py -Q thema:"Terra X" "datum:<01.05.17"

Das Datumsfeld ist speziell, als hier die Operatoren "<",">", "<=", ">=", "="
und "von-bis" unterstützt werden. Das einzelne "="-Zeichen kann auch
weggelassen werden. Auf ordentliches Quoting in der Shell
ist zu achten, da die Kleiner- und Größerzeichen von der Shell als
Umleitungen interpretiert werden.

Suchbegriffe können jeweils mit Klammern sowie "und/and/oder/or" verknüpft
werden. Ohne Angabe von Operatoren werden generische Suchbegriffe mit
"oder" angehängt und die Suche in Feldern mit "und".


Konfiguration
-------------

In der Datei `/etc/mtv_cli.conf` gibt es im Abschnitt `[CONFIG]`
eine Reihe von Konfigurationsvariablen:

  - `MAX_ALTER`: Filme die älter sind, landen bei der Aktualisierung nicht
     in der Datenbank
  - `MIN_DAUER`: Filme die kürzer sind, landen bei der Aktualisierung nicht
     in der Datenbank
  - `MSG_LEVEL`: Steuert die Ausgaben des Programms. Gültige Werte:
     `TRACE`, `DEBUG`, `INFO`, `WARN`, `ERROR`
  - `ZIEL_DOWNLOADS`: Maske für Dateinamen
  - `CMD_DOWNLOADS`: Download-Kommando
  - `QUALITAET`: Download-Qualität ("LOW", "SD", "HD")

**Nach der Installation sollte auf alle Fälle die Variable `ZIEL_DOWNLOADS`
angepasst werden!**

Der Abschnitt `[WEB]` steuert die Webserver:

  - `PORT`: Portnummer, auf den der Webserver auf Verbindungen wartet
            (Default: 8026)
  - `HOST`: IP-Adresse, von der Anfragen entgegen genommen werden. Der
            Default `0.0.0.0` lässt Anfragen von überall zu. Soll der
            Webserver hinter einem anderen lokal laufenden Server arbeiten,
            ist hier `127.0.0.1` der richtige Wert.


Anwendungsfälle
---------------

Die typischen Anwendungsszenarien von `mtv_cli` sehen so aus:

  - Automatische Aktualisierung der Filmliste (`mtv_cli.py aktualisiere-filmliste`)
    mit einem Cronjob.
  - Einplanung des Downloads (`mtv_cli.py filme-vormerken`) ebenfalls per
    Cronjob.
  - Automatisierte Suche mit Versand des Ergebnisses per Mail, z.B.

        mtv_cli.py suche thema:"erlebnis erde" | \
            mail -s"Neues zu Erlebnis Erde" ich@meinprovider.de

    Hierfür gibt es ein Beispielskript (`/usr/local/bin/mtv_sendinfo`)
  - Das automatisches Aufzeichnen von Sendungen ("Abo") funktioniert mit
    `mtv_cli.py -b -V "Terra X"`. Die Optionen `-V` und `-S` nehmen nur
    Sendungen in die Downloadliste auf, die dort noch nicht vorhanden sind.
    (**Achtung: diese Funktionalität ist aktuell nicht stabil**)
  - Für den nochmaligen Download einer Sendung muss der entsprechende
    Eintrag in der Downloadliste erst mit
    `mtv_cli.py entferne-filmvormerkungen` gelöscht werden.
