import datetime as dt
from dataclasses import dataclass
from typing import Optional, Protocol

from pydantic import BaseModel, Field

from mtv_cli.film import FilmlistenEintrag

MINUTES_T = int
DAYS_T = int


class FilmMissesDateError(ValueError):
    "Raised if a film with missing date is encountered unexpectedly."
    pass


class FilmFilter(Protocol):
    def is_permitted(self, film: FilmlistenEintrag) -> bool:
        pass


@dataclass(frozen=True)
class CompositeFilter:
    filters: list[FilmFilter]

    def is_permitted(self, film) -> bool:
        for f in self.filters:
            if not f.is_permitted(film):
                return False
        return True


class AgeFilter(BaseModel):
    # Filme können negatives Alter haben, wenn sie vor der Ausstrahlung
    # veröffentlicht wurden.
    min_age: Optional[DAYS_T] = None
    max_age: Optional[DAYS_T] = None
    today: dt.date = Field(default_factory=dt.date.today)

    def is_permitted(self, film: FilmlistenEintrag) -> bool:
        if film.datum is None:
            # Film kann nicht verworfen werden, da Informationen fehlen.
            return True
        if self.min_age is None:
            return False
        age = (self.today - film.datum).days
        min_age = age if self.min_age is None else self.min_age
        max_age = age if self.max_age is None else self.max_age
        return min_age <= age <= max_age


class DurationFilter(BaseModel):
    min_duration: MINUTES_T = 0
    max_duration: Optional[MINUTES_T] = None

    def is_permitted(self, film: FilmlistenEintrag) -> bool:
        duration = film.dauer_as_minutes()
        max_duration = duration if self.max_duration is None else self.max_duration
        return self.min_duration <= duration <= max_duration


class HasDateFilter(BaseModel):
    def is_permitted(self, film: FilmlistenEintrag) -> bool:
        return film.datum is not None


def AgeDurationFilter(
    *,
    min_age: Optional[DAYS_T] = None,
    max_age: Optional[DAYS_T] = None,
    today: Optional[dt.date] = None,
    min_duration: MINUTES_T = 0,
    max_duration: Optional[MINUTES_T] = None,
) -> CompositeFilter:
    age_filter_kwargs = dict(min_age=min_age, max_age=max_age)
    if today is not None:
        age_filter_kwargs["today"] = today  # type: ignore[assignment]
    age_filter = AgeFilter.parse_obj(age_filter_kwargs)
    duration_filter = DurationFilter(
        min_duration=min_duration, max_duration=max_duration
    )
    has_date_filter = HasDateFilter()
    return CompositeFilter(filters=[has_date_filter, age_filter, duration_filter])
