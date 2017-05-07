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
from multiprocessing import Lock
from multiprocessing.pool import ThreadPool

# --- eigene Imports   ------------------------------------------------------

from mtv_const import *
from mtv_cfg import *
from mtv_filmdb import FilmDB as FilmDB

# --- Download eines Films   -----------------------------------------------

def download_film(film):
  """Download eines einzelnen Films"""

  # Infos zusammensuchen
  _id = film._id
  size,url = film.get_url()
  film.thema = film.thema.replace('/','_')
  film.titel = film.titel.replace('/','_')
  ziel = ZIEL_DOWNLOADS.format(ext=url.split(".")[-1],**film.asDict())
  cmd = CMD_DOWNLOADS.format(ziel=ziel,url=url)

  # Download ausführen
  msg("INFO","Start Download (%s) %s" % (size,film.titel[0:50]))
  p = subprocess.Popen(shlex.split(cmd),stdout=DEVNULL, stderr=STDOUT)
  p.wait()
  rc = p.returncode
  msg("INFO","Ende  Download (%s) %s (Return-Code: %d)" % (size,film.titel[0:50],rc))
  return rc

# --- Download aller Filme   -----------------------------------------------

def download_filme(filmdb,status="'V','F'"):
  # Filme lesen
  filme = filmdb.read_downloads(ui=False,status=status)

  with ThreadPool(NUM_DOWNLOADS) as pool:
    results = []
    for film in filme:
        pool.apply_async(download_film,(film,))
    pool.close()
    pool.join()
  
  #  for i in range(1,20):
  #      arguments += str(i) + "_image.jpg "
  #      results.append(pool.apply_async(call_proc, ("./combine" + arguments,)))

  # Close the pool and wait for each running task to complete
  #  pool.close()
  #  pool.join()
  #  for result in results:
  #      out, err = result.get()
  #      print("out: {} err: {}".format(out, err))

