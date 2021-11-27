# Mediathekview auf der Kommandozeile
#
# Methoden rund um den Download
#
# Author: Bernhard Bablok, Max Görner
# License: GPL3
#
# Website: https://github.com/bablokb/mtv_cli
#


from pathlib import Path

import requests
from loguru import logger
from pydantic import BaseModel

from mtv_cli.film import FILM_QUALITAET, FilmlistenEintrag


class FilmDownloadFehlerhaft(RuntimeError):
    pass


class LowMemoryFileSystemDownloader(BaseModel):
    root: Path
    quality: FILM_QUALITAET
    chunk_size: int = 1024 * 1024  # 1 MiB

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
        try:
            response.raise_for_status()
            with self.get_filename(film).open("wb") as fh:
                for chunk in response.iter_content(chunk_size=self.chunk_size):
                    fh.write(chunk)
        except requests.HTTPError as http_err:
            logger.error(f"Download des Films {film} ist fehlgeschlagen!")
            logger.exception(http_err)
            raise FilmDownloadFehlerhaft from http_err
