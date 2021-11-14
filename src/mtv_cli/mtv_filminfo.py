from __future__ import annotations

import datetime as dt
from dataclasses import asdict, dataclass
from typing import Literal, Optional, Union

# Mediathekview auf der Kommandozeile
#
# Class FilmInfo: Einzelsatz Info
#
# Author: Bernhard Bablok, Max Görner
# License: GPL3
#
# Website: https://github.com/bablokb/mtv_cli
#

FILM_QUALITAET = Union[Literal["HD"], Literal["SD"], Literal["LOW"]]


class FilmInfo:
    """Info über einen einzelnen Film"""

    def __init__(
        self,
        sender,
        thema,
        titel,
        datum,
        zeit,
        dauer,
        groesse,
        beschreibung,
        url,
        website,
        url_untertitel,
        url_rtmp,
        url_klein,
        url_rtmp_klein,
        url_hd,
        url_rtmp_hd,
        datumL,
        url_history,
        geo,
        neu,
    ):
        """FilmInfo-Objekt erzeugen"""

        self.sender = sender
        self.thema = thema
        self.titel = titel
        self.datum = self.to_date(datum)
        self.zeit = zeit
        self.dauer = dauer
        self.groesse = int(groesse) if groesse else 0
        self.beschreibung = beschreibung
        self.url = url
        self.website = website
        self.url_untertitel = url_untertitel
        self.url_rtmp = url_rtmp
        self.url_klein = url_klein
        self.url_rtmp_klein = url_rtmp_klein
        self.url_hd = url_hd
        self.url_rtmp_hd = url_rtmp_hd
        self.datumL = datumL
        self.url_history = url_history
        self.geo = geo
        self.neu = neu

    def to_date(self, datum):
        """Datumsstring in ein Date-Objekt umwandeln"""
        if isinstance(datum, dt.date):
            return datum
        if "." in datum:
            return dt.datetime.strptime(datum, "%d.%m.%Y").date()
        else:
            # schon im ISO-Format
            return dt.datetime.strptime(datum, "%Y-%m-%d").date()

    def dauer_as_minutes(self):
        """Dauer HH:MM:SS in Minuten (Integer) umwandeln"""
        if isinstance(self.dauer, int):
            return self.dauer
        elif self.dauer:
            parts = self.dauer.split(":")
            minutes = 60 * int(parts[0]) + int(parts[1])
            if int(parts[2]) > 30:
                # Aufrunden von Sekunden
                minutes += 1
            return minutes
        else:
            return 999

    def asTuple(self):
        """Objekt-Felder als Tuple zurückgeben"""
        return (
            self.sender,
            self.thema,
            self.titel,
            self.datum,
            self.zeit,
            self.dauer,
            self.groesse,
            self.beschreibung,
            self.url,
            self.website,
            self.url_untertitel,
            self.url_rtmp,
            self.url_klein,
            self.url_rtmp_klein,
            self.url_hd,
            self.url_rtmp_hd,
            self.datumL,
            self.url_history,
            self.geo,
            self.neu,
        )

    def asDict(self):
        """Objekt-Felder als Dict zurückgeben"""
        return {
            "Sender": self.sender,
            "Thema": self.thema,
            "Titel": self.titel,
            "Datum": self.datum,
            "Zeit": self.zeit,
            "Dauer": self.dauer,
            "Groesse": self.groesse,
            "Beschreibung": self.beschreibung,
            "Url": self.url,
            "Website": self.website,
            "Url_Untertitel": self.url_untertitel,
            "Url_RTMP": self.url_rtmp,
            "Url_klein": self.url_klein,
            "Url_RTMP_klein": self.url_rtmp_klein,
            "Url_HD": self.url_hd,
            "Url_RTMP_HD": self.url_rtmp_hd,
            "DatumL": self.datumL,
            "Url_History": self.url_history,
            "geo": self.geo,
            "neu": self.neu,
        }

    def get_url(self, qualitaet):
        """Bevorzugte URL zurückgeben
        Ergebnis ist (Qualität,URL)"""

        size = ""
        if qualitaet == "HD" and self.url_hd:
            url_suffix = self.url_hd
            size = "HD"

        if qualitaet == "SD" or not self.url_hd:
            return "SD", self.url
        elif not size:
            url_suffix = self.url_klein
            size = "LOW"

        parts = url_suffix.split("|")
        offset = int(parts[0])
        return size, self.url[0:offset] + parts[1]


@dataclass(frozen=True)
class FilmlistenEintrag:
    # TODO: Datum+Zeit zu Sendezeit zusammenfassen; DatumL ganz durch Sendezeit ersetzen
    sender: str
    thema: str
    titel: str
    datum: Optional[dt.date]
    zeit: Optional[dt.time]
    dauer: Optional[dt.timedelta]
    groesse: int
    beschreibung: str
    url: str
    website: str
    url_untertitel: str
    url_rtmp: str
    url_klein: str
    url_rtmp_klein: str
    url_hd: str
    url_rtmp_hd: str
    datuml: Optional[int]
    url_history: str
    geo: str
    neu: bool

    def __post_init__(self) -> None:
        assert isinstance(self.sender, str)
        assert isinstance(self.thema, str)
        assert isinstance(self.titel, str)
        assert self.datum is None or isinstance(self.datum, dt.date)
        assert self.zeit is None or isinstance(self.zeit, dt.time)
        assert self.dauer is None or isinstance(self.dauer, dt.timedelta)
        assert isinstance(self.groesse, int)
        assert isinstance(self.beschreibung, str)
        assert isinstance(self.url, str)
        assert isinstance(self.website, str)
        assert isinstance(self.url_untertitel, str)
        assert isinstance(self.url_rtmp, str)
        assert isinstance(self.url_klein, str)
        assert isinstance(self.url_rtmp_klein, str)
        assert isinstance(self.url_hd, str)
        assert isinstance(self.url_rtmp_hd, str)
        assert self.datuml is None or isinstance(self.datuml, int)
        assert isinstance(self.url_history, str)
        assert isinstance(self.geo, str)
        assert isinstance(self.neu, bool)

    @classmethod
    def from_item_list(cls, raw_entry: list[str]) -> FilmlistenEintrag:
        datum = (
            None
            if raw_entry[3] == ""
            else dt.datetime.strptime(raw_entry[3], "%d.%m.%Y").date()
        )
        zeit = (
            None
            if raw_entry[4] == ""
            else dt.datetime.strptime(raw_entry[4], "%H:%M:%S").time()
        )
        dauer_raw = (
            None
            if raw_entry[5] == ""
            else dt.datetime.strptime(raw_entry[5], "%H:%M:%S")
        )
        dauer = None if dauer_raw is None else dauer_raw - dt.datetime(1900, 1, 1)
        return FilmlistenEintrag(
            sender=raw_entry[0],
            thema=raw_entry[1],
            titel=raw_entry[2],
            datum=datum,
            zeit=zeit,
            dauer=dauer,
            groesse=int(raw_entry[6]) if raw_entry[6] else 0,
            beschreibung=raw_entry[7],
            url=raw_entry[8],
            website=raw_entry[9],
            url_untertitel=raw_entry[10],
            url_rtmp=raw_entry[11],
            url_klein=raw_entry[12],
            url_rtmp_klein=raw_entry[13],
            url_hd=raw_entry[14],
            url_rtmp_hd=raw_entry[15],
            datuml=None if raw_entry[16] == "" else int(raw_entry[16]),
            url_history=raw_entry[17],
            geo=raw_entry[18],
            neu=raw_entry[19] == "true",
        )

    def update(self, entry: Optional[FilmlistenEintrag]) -> FilmlistenEintrag:
        """
        Übernimm die Felder Sender und Thema, falls nötig

        Falls eines der genannten Felder leer ist, wird es von `eintrag`
        übernommen.
        """
        if entry is None:
            return self
        new = asdict(self)
        for attr in "sender", "thema":
            if not new[attr]:
                new[attr] = asdict(entry)[attr]
        return type(self)(**new)

    def dauer_as_minutes(self) -> int:
        if self.dauer is None:
            # Die Dauer des Eintrages ist unbekannt. Es wird daher ein
            # Maximalwert zurückgegeben, damit der Film nicht als zu kurz
            # aussortiert wird.
            minutes_in_day = 24 * 60 * 60
            return minutes_in_day
        return self.dauer.seconds // 60

    def get_url(self, qualitaet: FILM_QUALITAET) -> tuple[FILM_QUALITAET, str]:
        """Bevorzugte URL zurückgeben

        Ergebnis ist (Qualität,URL)
        """
        if qualitaet == "SD" or not self.url_hd:
            return "SD", self.url

        size: FILM_QUALITAET
        if qualitaet == "HD" and self.url_hd:
            url_suffix = self.url_hd
            size = "HD"
        else:
            url_suffix = self.url_klein
            size = "LOW"

        parts = url_suffix.split("|")
        offset = int(parts[0])
        return size, self.url[0:offset] + parts[1]
