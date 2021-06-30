#!/usr/bin/python3
# -*- coding: utf-8 -*-
# --------------------------------------------------------------------------
# Mediathekview auf der Kommandozeile
#
# Definition der Klasse Msg
#
# Author: Bernhard Bablok
# License: GPL3
#
# Website: https://github.com/bablokb/mtv_cli
#
# --------------------------------------------------------------------------

import datetime
import sys

MSG_LEVELS = {"TRACE": 0, "DEBUG": 1, "INFO": 2, "WARN": 3, "ERROR": 4}


class Msg:
    """Simple Klasse für Meldungen"""

    def __init__(self, level="INFO"):
        self.level = level

    def msg(self, msg_level, text, nl=True):
        """Ausgabe einer Meldung"""
        if MSG_LEVELS[msg_level] >= MSG_LEVELS[self.level]:
            if nl:
                now = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                sys.stderr.write(
                    "[" + msg_level + "] " + "[" + now + "] " + text + "\n"
                )
            else:
                sys.stderr.write(text)
                sys.stderr.flush()
