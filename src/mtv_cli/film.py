# Mediathekview auf der Kommandozeile
#
# Author: Bernhard Bablok, Max Görner
# License: GPL3
#
# Website: https://github.com/bablokb/mtv_cli
#

from __future__ import annotations

import datetime as dt
from typing import Literal, Optional, Union

from pydantic import BaseModel

FILM_QUALITAET = Union[Literal["HD"], Literal["SD"], Literal["LOW"]]


class FilmlistenEintrag(BaseModel):
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

    class Config:
        allow_mutation = False

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
        new = self.dict()
        for attr in "sender", "thema":
            if not new[attr]:
                new[attr] = entry.dict()[attr]
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
