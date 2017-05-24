#!/usr/bin/python3
# -*- coding: utf-8 -*-
# ---------------------------------------------------------------------------
# Mediathekview auf der Kommandozeile (Webinterface)
#
# Einfaches Webinterface auf Basis von Bottle
#
# Author: Bernhard Bablok
# License: GPL3
#
# Website: https://github.com/bablokb/mtv_cli
#
# ---------------------------------------------------------------------------

# --- System-Imports   ------------------------------------------------------

import os
import bottle
from bottle import route

# --- Webroot dynamisch bestimmen   -----------------------------------------

def get_webroot(pgm):
  pgm_dir = os.path.dirname(os.path.realpath(pgm))
  return os.path.realpath(os.path.join(pgm_dir,"..","lib","mtv_cli","web"))

def get_webpath(path):
  return os.path.join(WEB_ROOT,path)

# --- Methoden für das Routing   --------------------------------------------

@route('/css/<filepath:path>')
def css_pages(filepath):
    print(filepath)
    return bottle.static_file(filepath, root=get_webpath('css'))
  
@route('/js/<filepath:path>')
def css_pages(filepath):
    return bottle.static_file(filepath, root=get_webpath('js'))
  
@route('/')
def main_page():
  return bottle.template(get_webpath("index.html"))

# --- Hauptprogramm   -------------------------------------------------------

if __name__ == '__main__':
  WEB_ROOT = get_webroot(__file__)
  bottle.run(host='localhost', port=2626, debug=True,reloader=True)
