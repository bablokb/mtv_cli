#!/usr/bin/python3
# -*- coding: utf-8 -*-
# --------------------------------------------------------------------------
# Mediathekview auf der Kommandozeile
#
# Methoden rund um den Downlaod
#
# Author: Bernhard Bablok
# License: GPL3
#
# Website: https://github.com/bablokb/mtv_cli
#
# --------------------------------------------------------------------------

# --- System-Imports   -----------------------------------------------------

import multiprocessing, os
import subprocess
import shlex
from subprocess import DEVNULL,STDOUT
from multiprocessing.pool import ThreadPool

# --- eigene Imports   ------------------------------------------------------

from mtv_const  import *
from mtv_filmdb import FilmDB as FilmDB
from mtv_msg    import Msg as Msg

# --- Download eines Films   -----------------------------------------------

def download_film(options,film):
  """Download eines einzelnen Films"""

  # Infos zusammensuchen
  _id = film._id
  size,url = film.get_url(options.config["QUALITAET"])
  film.thema = film.thema.replace('/','_')
  film.titel = film.titel.replace('/','_')
  ziel = options.config["ZIEL_DOWNLOADS"].format(ext=url.split(".")[-1],
                                                 **film.asDict())
  cmd = options.config["CMD_DOWNLOADS"].format(ziel=ziel,url=url)

  # Zielverzeichnis erstellen
  ziel_dir = os.path.dirname(ziel)
  if not os.path.exists(ziel_dir):
    os.mkdirs(ziel_dir)

  # Download ausführen
  options.filmDB.update_downloads(_id,'A')
  Msg.msg("INFO","Start Download (%s) %s" % (size,film.titel[0:50]))
  p = subprocess.Popen(shlex.split(cmd),stdout=DEVNULL, stderr=STDOUT)
  p.wait()
  rc = p.returncode
  Msg.msg("INFO",
      "Ende  Download (%s) %s (Return-Code: %d)" % (size,film.titel[0:50],rc))
  if rc==0:
    options.filmDB.update_downloads(_id,'K')
  else:
    options.filmDB.update_downloads(_id,'F')

  return rc

# --- Download aller Filme   -----------------------------------------------

def download_filme(options,status="'V','F','A'"):
  # Filme lesen
  filme = options.filmDB.read_downloads(ui=False,status=status)

  if not filme:
    Msg.msg("INFO","Keine vorgemerkten Filme vorhanden")
    return

  if NUM_DOWNLOADS == 1:
    # Spezialbehandlung (erleichtert Debugging)
    for film in filme:
      download_film(options,film)
  else:
    with ThreadPool(options.config["NUM_DOWNLOADS"]) as pool:
      results = []
      for film in filme:
        pool.apply_async(download_film,(options,film))
      pool.close()
      pool.join()

  options.filmDB.save_status('_download')
