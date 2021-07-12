# Erzeugen eines Debian Paketes für Debian und Ubuntu

## Debian Paket erzeugen
```
dpkg-buildpackage -us -uc -b
```

## Aufräumen nach dem Erzeugen des Pakets
```
dh clean
```

## Information

Das ist ein erster Versuch aus den vorhandenen Dateien ein 
brauchbares Debian Paket zu erzeugen. 

Da die aktuelle Implementierung nicht speziell für ein 
Debian Paket ausgelegt ist, mussten ein paar "Hacks" angewandt
werden. In der ersten Version sollte so wenig wie möglich an den
ursprünglichen Sourcen verändert werden.

## Achtung

Dies ist noch weit davon entfernt für ein echtes Debian Paket,
welches auch in den Debian/Ubuntu Repositories benutzt werden kann.

Es wurde geschrieben, um die Installation zu vereinfachen, nicht mehr 
und nicht weniger.

