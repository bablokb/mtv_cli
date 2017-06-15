Mediathekview auf der Kommandozeile
===================================

Mediathekview ist eine sehr gute Anwendung, ist aber nicht auf der
Kommandozeile verwendbar.

Das Kommando `mtv_cli.py` läuft dagegen auch ohne grafische Oberfläche,
etwa wenn man sich per SSH auf einen Pi mit Kodi-Distribution einlogged.

Die Kommandozeilenversion von Mediathekview wird nie den Funktionsumfang
des Originals erhalten. Es geht um eine einfache, schlanke Lösung die
sich eher an Experten, denn an absolute Laien richtet.

Die Anwendung verwendet die Mediathekview-Filmliste, allerdings konvertiert
in ein richtiges Datenbankformat.


Status/Neuigkeiten
------------------

### Version 2 ###

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
  - pick

Das Skript `tools/install-mtv_cli` (per sudo aufrufen) installiert das
Programm und alle Voraussetzungen automatisch.

**Nach der Installation sollte auf alle Fälle die Variable `ZIEL_DOWNLOADS`
in der Konfiguration angepasst werden!** Details zur Konfiguration sind
weiter unten beschrieben.


Verwendung
----------

Über die Option `-h` gibt das Programm die verfügbaren Optionen aus:


    usage: mtv_cli.py [-A [Quelle]] [-V] [-S] [-D] [-Q] [-b] [-z dir] [-d Datei]
                      [-q] [-h]
                      [Suchausdruck]

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

In der Datei `/et/mtv_cli.conf` gibt es eine Reihe von Konfigurationsvariablen:

  - `DATE_CUTOFF`: Filme die älter sind, landen bei der Aktualisierung nicht
     in der Datenbank
  - `DAUER_CUTOFF`: Filme die kürzer sind, landen bei der Aktualisierung nicht
     in der Datenbank
  - `MSG_LEVEL`: Steuert die Ausgaben des Programms. Gültige Werte:
     `TRACE`, `DEBUG`, `INFO`, `WARN`, `ERROR`
  - `NUM_DOWNLOADS`: Anzahl paralleler Downloads
  - `ZIEL_DOWNLOADS`: Maske für Dateinamen
  - `CMD_DOWNLOADS`: Download-Kommando
  - `QUALITAET`: Download-Qualität ("LOW", "SD", "HD")

**Nach der Installation sollte auf alle Fälle die Variable `ZIEL_DOWNLOADS`
angepasst werden!**

Anwendungsfälle
---------------

Die typischen Anwendungsszenarien von `mtv_cli` sehen so aus:

  - Automatische Aktualisierung der Filmliste (`mtv_cli.py -A`) mit einem
    Cronjob.
  - Einplanung des Downloads (`mtv_cli.py -D`) ebenfalls per Cronjob.
  - Automatisierte Suche mit Versand des Ergebnisses per Mail, z.B.

        mtv_cli.py -Q thema:"erlebnis erde" | \
            mail -s"Neues zu Erlebnis Erde" ich@meinprovider.de

  - Das automatisches Aufzeichnen von Sendungen ("Abo") funktioniert mit
    `mtv_cli.py -b -V "Terra X"`. Die Optionen `-V` und `-S` nehmen nur
    Sendungen in die Downloadliste auf, die dort noch nicht vorhanden sind.
  - Für den nochmaligen Download einer Sendung muss der entsprechende
    Eintrag in der Downloadliste erst mit `mtv_cli.py -E` gelöscht werden.
