"""Manually authored local movies used by the opt-in development seed."""

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class DemoMovie:
    """One immutable movie definition owned by this application."""

    title: str
    release_year: int
    genres: tuple[str, ...]


DEMO_MOVIES: tuple[DemoMovie, ...] = (
    DemoMovie("Orbit of Glass", 1998, ("drama", "science fiction")),
    DemoMovie("The Quiet Signal", 2001, ("mystery", "science fiction")),
    DemoMovie("Winter at Meridian", 2003, ("drama", "mystery")),
    DemoMovie("Copper Sky", 2005, ("adventure", "science fiction")),
    DemoMovie("Last Train to Solace", 2006, ("drama", "thriller")),
    DemoMovie("Paper Constellations", 2008, ("drama", "romance")),
    DemoMovie("Lanterns Below", 2010, ("adventure", "fantasy")),
    DemoMovie("Echo Harbor", 2012, ("drama", "mystery")),
    DemoMovie(
        "The Clockmaker's Map",
        2014,
        ("adventure", "fantasy", "mystery"),
    ),
    DemoMovie("Static Summer", 2016, ("comedy", "drama")),
    DemoMovie("Red Horizon Station", 2018, ("science fiction", "thriller")),
    DemoMovie("A Garden in November", 2020, ("drama", "romance")),
)
