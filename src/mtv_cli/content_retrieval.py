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
from multiprocessing.pool import ThreadPool
from pathlib import Path
from subprocess import DEVNULL, STDOUT

import requests
from film import FILM_QUALITAET, FilmlistenEintrag
from loguru import logger
from pydantic import BaseModel
from storage_backend import DownloadStatus, FilmDB


class LowMemoryFileSystemDownloader(BaseModel):
    root: Path
    quality: FILM_QUALITAET
    chunk_size: int = 128

    def get_filename(self, film: FilmlistenEintrag) -> Path:
        # Infos zusammensuchen
        size, url = film.get_url(self.quality)
        thema = film.thema.replace("/", "_")
        titel = film.titel.replace("/", "_")
        ext = url.split(".")[-1].lower()
        fname = self.root / f"{film.sender}_{film.datum}_{thema}_{titel}.{ext}"
        return fname

    def download_film(self, film: FilmlistenEintrag) -> None:
        """Download eines einzelnen Films"""
        real_quality, url = film.get_url(self.quality)
        if real_quality != self.quality:
            logger.warning(
                f"Angeforderte Qualität {self.quality} ist für Film {film} nicht"
                " vorhanden! Nutze stattdessen {real_quality}."
            )
        response = requests.get(url, stream=True)
        with self.get_filename(film).open("wb") as fh:
            for chunk in response.iter_content(chunk_size=self.chunk_size):
                fh.write(chunk)


def download_film(options, film: FilmlistenEintrag) -> int:
    """Download eines einzelnen Films"""

    filmDB: FilmDB = options.filmDB

    # Infos zusammensuchen
    size, url = film.get_url(options.config["QUALITAET"])
    sanitised_thema = film.thema.replace("/", "_")
    sanitised_titel = film.titel.replace("/", "_")
    ext = url.split(".")[-1].lower()
    film_kwargs = film.dict()
    film_kwargs.update(dict(titel=sanitised_titel, thema=sanitised_thema))
    sanitised_film = FilmlistenEintrag.parse_obj(film_kwargs)

    # Kommando bei Playlisten anpassen. Die Extension der gespeicherten Datei
    # wird auf mp4 geändert
    isM3U = ext.startswith("m3u")
    if isM3U:
        cmd = options.config["CMD_DOWNLOADS_M3U"]
        ext = "mp4"
    else:
        cmd = options.config["CMD_DOWNLOADS"]

    ziel = Path(
        options.config["ZIEL_DOWNLOADS"].format(ext=ext, **sanitised_film.dict())
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
