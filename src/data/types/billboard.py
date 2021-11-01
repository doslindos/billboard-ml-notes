from typing import TypedDict

class BillboardSong(TypedDict):
    rank: int
    song: str
    artist: str
    lastWeek: int
    peakRank: int
    weeksOnBoard: int
    date: str
