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

import datetime

class FilmInfo(object):
  """Info über einen einzelnen Film"""

    # ------------------------------------------------------------------------
  
  def __init__(self,sender,thema,titel,datum,zeit,dauer,
               groesse,beschreibung,url,website,url_untertitel,url_rtmp,
               url_klein,url_rtmp_klein,url_hd,url_rtmp_hd,url_datuml,
               url_history,url_geo,neu,_id):
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
    self.url_datuml     = url_datuml
    self.url_history    = url_history
    self.url_geo        = url_geo
    self.neu            = neu
    self._id            = _id

  # ------------------------------------------------------------------------

  def to_date(self,datum):
    """Datumsstring in ein Date-Objekt umwandeln"""
    if '.' in datum:
      return datetime.datetime.strptime(datum,"%d.%m.%Y").date()
    else:
      # schon im ISO-Format
      return datetime.datetime.strptime(datum,"%Y-%m-%d").date()

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
      self.url_datuml,
      self.url_history,
      self.url_geo,
      self.neu,
      self._id
      )
