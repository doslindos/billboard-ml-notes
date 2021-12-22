from typing import TypedDict, Literal

class ModelFeatures(TypedDict):
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
    releaseYear: int

class SongFeaturesAndLabels(TypedDict):
    spotifyID: str
    features: ModelFeatures
    label: Literal[0, 1]
