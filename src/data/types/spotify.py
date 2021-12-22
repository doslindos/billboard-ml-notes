from typing import TypedDict, Optional

from .billboard import BillboardSong

class SpotifyArtist(TypedDict):
    name: str
    artistID: str

class SpotifyAlbum(TypedDict):
    name: str
    albumID: str
    totalTracks: int
    releaseDate: str

class SpotifyFeatures(TypedDict):
    timeSignature: int
    durationMS: float
    key: int
    mode: int
    acousticness: float
    danceability: float
    energy: float
    instrumentalness: int
    liveness: float
    loudness: float
    speechiness: float
    valence: float
    tempo: float

class SpotifySongInfo(TypedDict):
    name: str
    songID: str
    artists: list[SpotifyArtist]
    album: SpotifyAlbum

class SpotifySongQueryResult(TypedDict):
    spotifyData: SpotifySongInfo 
    searchQuery: Optional[str] 
    minMatchingRatioUsed: Optional[int]
    originalData: Optional[BillboardSong]

class SpotifySongData(TypedDict):
    info: SpotifySongInfo
    features: SpotifyFeatures
    labels: Optional[dict]
