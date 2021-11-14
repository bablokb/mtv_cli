# Mediathekview auf der Kommandozeile
#
# Methoden rund um den Download
#
# Author: Bernhard Bablok, Max Görner
# License: GPL3
#
# Website: https://github.com/bablokb/mtv_cli
#


import shlex
import subprocess
from dataclasses import asdict, replace
from multiprocessing.pool import ThreadPool
from pathlib import Path
from subprocess import DEVNULL, STDOUT

from loguru import logger
from mtv_filmdb import DownloadStatus, FilmDB
from mtv_filminfo import FilmlistenEintrag


def download_film(options, film: FilmlistenEintrag) -> int:
    """Download eines einzelnen Films"""

    filmDB: FilmDB = options.filmDB

    # Infos zusammensuchen
    size, url = film.get_url(options.config["QUALITAET"])
    sanitised_film = replace(
        film, thema=film.thema.replace("/", "_"), titel=film.titel.replace("/", "_")
    )
    ext = url.split(".")[-1].lower()

    # Kommando bei Playlisten anpassen. Die Extension der gespeicherten Datei
    # wird auf mp4 geändert
    isM3U = ext.startswith("m3u")
    if isM3U:
        cmd = options.config["CMD_DOWNLOADS_M3U"]
        ext = "mp4"
    else:
        cmd = options.config["CMD_DOWNLOADS"]

    ziel = Path(
        options.config["ZIEL_DOWNLOADS"].format(ext=ext, **asdict(sanitised_film))
    )
    ziel.parent.mkdir(parents=True, exist_ok=True)
    cmd = cmd.format(ziel=ziel, url=url)

    # Download ausführen
    filmDB.update_downloads(film, "A")
    logger.info("Start Download (%s) %s" % (size, film.titel[0:50]))
    if isM3U:
        logger.debug("Kommando: %s" % cmd)
        p = subprocess.Popen(cmd, shell=True, stdout=DEVNULL, stderr=STDOUT)
    else:
        logger.debug("Kommando: %r" % shlex.split(cmd))
        p = subprocess.Popen(shlex.split(cmd), stdout=DEVNULL, stderr=STDOUT)
    p.wait()
    rc = p.returncode
    logger.info(
        "Ende  Download (%s) %s (Return-Code: %d)" % (size, film.titel[0:50], rc),
    )
    if rc == 0:
        filmDB.update_downloads(film, "K")
        filmDB.save_recs(film, ziel)
    else:
        filmDB.update_downloads(film, "F")

    return rc


def download_filme(options, status: list[DownloadStatus] = ["V", "F", "A"]):
    # Filme lesen
    filmDB: FilmDB = options.filmDB
    filme = filmDB.read_downloads(status=status)

    if not filme:
        logger.info("Keine vorgemerkten Filme vorhanden")
        return

    if options.config["NUM_DOWNLOADS"] == 1:
        # Spezialbehandlung (erleichtert Debugging)
        for film in filme:
            download_film(options, film)
    else:
        with ThreadPool(options.config["NUM_DOWNLOADS"]) as pool:
            for film in filme:
                pool.apply_async(download_film, (options, film))
            pool.close()
            pool.join()

    filmDB.save_status("_download")
