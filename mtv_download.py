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

import multiprocessing
import subprocess
import shlex
from subprocess import DEVNULL,STDOUT
from multiprocessing.pool import ThreadPool

# --- eigene Imports   ------------------------------------------------------

from mtv_const import *
from mtv_cfg import *
from mtv_filmdb import FilmDB as FilmDB

# --- Download eines Films   -----------------------------------------------

def download_film(filmdb,film):
  """Download eines einzelnen Films"""

  # Infos zusammensuchen
  _id = film._id
  size,url = film.get_url()
  film.thema = film.thema.replace('/','_')
  film.titel = film.titel.replace('/','_')
  ziel = ZIEL_DOWNLOADS.format(ext=url.split(".")[-1],**film.asDict())
  cmd = CMD_DOWNLOADS.format(ziel=ziel,url=url)

  # Download ausführen
  filmdb.update_downloads(_id,'A')
  msg("INFO","Start Download (%s) %s" % (size,film.titel[0:50]))
  p = subprocess.Popen(shlex.split(cmd),stdout=DEVNULL, stderr=STDOUT)
  p.wait()
  rc = p.returncode
  msg("INFO",
      "Ende  Download (%s) %s (Return-Code: %d)" % (size,film.titel[0:50],rc))
  if rc==0:
    filmdb.update_downloads(_id,'K')
  else:
    filmdb.update_downloads(_id,'F')

  return rc

# --- Download aller Filme   -----------------------------------------------

def download_filme(filmdb,status="'V','F','A'"):
  # Filme lesen
  filme = filmdb.read_downloads(ui=False,status=status)

  if NUM_DOWNLOADS == 1:
    # Spezialbehandlung (erleichtert Debugging)
    for film in filme:
      download_film(filmdb,film)
  else:
    with ThreadPool(NUM_DOWNLOADS) as pool:
      results = []
      for film in filme:
        pool.apply_async(download_film,(filmdb,film))
      pool.close()
      pool.join()
