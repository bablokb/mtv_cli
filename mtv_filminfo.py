#!/usr/bin/python3
# -*- coding: utf-8 -*-
# --------------------------------------------------------------------------
# Mediathekview auf der Kommandozeile
#
# Class FilmInfo: Einzelsatz Info
#
# Author: Bernhard Bablok
# License: GPL3
#
# Website: https://github.com/bablokb/mtv_cli
#
# --------------------------------------------------------------------------

import datetime, hashlib

from mtv_cfg import *

class FilmInfo(object):
  """Info über einen einzelnen Film"""

    # ------------------------------------------------------------------------
  
  def __init__(self,sender,thema,titel,datum,zeit,dauer,
               groesse,beschreibung,url,website,url_untertitel,url_rtmp,
               url_klein,url_rtmp_klein,url_hd,url_rtmp_hd,datumL,
               url_history,geo,neu,_id=None):
    """FilmInfo-Objekt erzeugen"""

    self.sender         = sender
    self.thema          = thema
    self.titel          = titel
    self.datum          = self.to_date(datum)
    self.zeit           = zeit
    self.dauer          = dauer
    self.groesse        = int(groesse)
    self.beschreibung   = beschreibung
    self.url            = url
    self.website        = website
    self.url_untertitel = url_untertitel
    self.url_rtmp       = url_rtmp
    self.url_klein      = url_klein
    self.url_rtmp_klein = url_rtmp_klein
    self.url_hd         = url_hd
    self.url_rtmp_hd    = url_rtmp_hd
    self.datumL         = datumL
    self.url_history    = url_history
    self.geo            = geo
    self.neu            = neu
    if not _id:
      self._id            = hashlib.md5((sender+thema+titel+datum+zeit+dauer+
                                      groesse+beschreibung+url+website+
                                      url_untertitel+url_rtmp+url_klein+
                                      url_rtmp_klein+url_hd+url_rtmp_hd+
                                      datumL+url_history+
                                      geo).encode('utf-8')).hexdigest()
    else:
      self._id = _id

  # ------------------------------------------------------------------------

  def to_date(self,datum):
    """Datumsstring in ein Date-Objekt umwandeln"""
    if isinstance(datum,datetime.date):
      return datum
    if '.' in datum:
      return datetime.datetime.strptime(datum,"%d.%m.%Y").date()
    else:
      # schon im ISO-Format
      return datetime.datetime.strptime(datum,"%Y-%m-%d").date()

  # ------------------------------------------------------------------------

  def dauer_as_minutes(self):
    """Dauer HH:MM:SS in Minuten (Integer) umwandeln"""
    if isinstance(self.dauer,int):
      return self.dauer
    else:
      parts = self.dauer.split(":")
      minutes = 60*int(parts[0])+int(parts[1])
      if int(parts[2]) > 30:
        # Aufrunden von Sekunden
        minutes += 1
      return minutes

  # ------------------------------------------------------------------------

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
      self._id
      )

  # ------------------------------------------------------------------------

  def asDict(self):
    """Objekt-Felder als Dict zurückgeben"""
    return {
      "Sender": self.sender,
      "Thema": self.thema,
      "Titel": self.titel,
      "Datum": self.datum,
      "Zeit":  self.zeit,
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
      "_id": self._id
      }

  # ------------------------------------------------------------------------

  def get_url(self):
    """Bevorzugte URL zurückgeben
       Ergebnis ist (Qualität,URL)"""

    size = ""
    if GROESSE_DOWNLOADS == "HD" and self.url_hd:
      url_suffix = self.url_hd
      size = "HD"

    if GROESSE_DOWNLOADS == "SD" or not self.url_hd:
      return "SD",self.url
    elif not size:
      url_suffix = self.url_klein
      size = "LOW"

    parts = url_suffix.split("|")
    offset = int(parts[0])
    return size,self.url[0:offset] + parts[1]
