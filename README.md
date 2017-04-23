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


Status
------

Aktuell funktioniert nur der Download der Filmliste und die Konvertierung
in eine SQLite3-Datenbank.


Installation
------------

Voraussetzungen:

  - Python3
  - python3-curses
  - pick

TODO: mehr Details zur Installation


Verwendung
----------

Über die Option `-h` gibt das Programm die verfügbaren Optionen aus. Fast
nichts davon ist aktuell implementiert:


    usage: mtv_cli.py [-A [Quelle]] [-V] [-S] [-D] [-Q] [-b] [-z dir] [-d Datei]
                      [-q] [-h]
                      [Suchausdruck]

    Mediathekview auf der Kommandozeile

    positional arguments:
      Suchausdruck          Sucheausdruck

    optional arguments:
      -A [Quelle], --akt [Quelle]
                            Filmliste aktualisieren (Quelle: auto|Url|Datei)
      -V, --vormerken       Filmauswahl im Vormerk-Modus
      -S, --sofort          Filmauswahl im Sofort-Modus
      -D, --download        Vorgemerkte Filme herunterladen
      -Q, --query           Filme suchen
      -b, --batch           Ausführung ohne User-Interface (zusammen mit -V und
                            -S)
      -z dir, --ziel dir    Zielverzeichnis
      -d Datei, --db Datei  Datenbankdatei
      -q, --quiet           Keine Meldungen ausgeben
      -h, --hilfe           Diese Hilfe ausgeben


Details
-------

Abschnitt noch ohne Inhalt.