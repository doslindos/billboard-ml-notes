from configparser import ConfigParser
from pathlib import Path
from os import environ
from typing import Union, Generator
from json import dump as jsondump, load as jsonload

from spotipy import Spotify
from spotipy.oauth2 import SpotifyClientCredentials

from data.types.util import Credentials

def createPath(pathStr: str, p: int = 3) -> Path:
    path = Path(pathStr)
    for i, parent in enumerate(path.parents):
        if i > p:
            break
        if not parent.exists():
            parent.mkdir()

    return path

def saveJson(saveObject: Union[list, dict], savePath: str) -> None:
    path = createPath(savePath)
    with path.open('w', encoding='utf8') as f:
        jsondump(saveObject, f, ensure_ascii=False)

def loadJson(savePath: str) -> Union[list, dict]:
    return jsonload(Path(savePath).open("r", encoding="utf-8"))

def getCredentials(
        credentialName: str,
        credentialsPath: str,
        ) -> Credentials:
    # Initialize the parser
    parser = ConfigParser()
    # Check that env variable file exists
    if Path(credentialsPath).exists():
        # Read the env file
        parser.read(credentialsPath)
        # Search for specidic credentials
        if credentialName in parser.sections():
            return parser[credentialName]
    
    print("Could not find the kaggle configurations from ", credentialsPath)
    return None

def setKaggleCredentialsToEnv(kaggleCredentials: Credentials) -> None:
    # Set the env variables
    environ['KAGGLE_USERNAME'] = kaggleCredentials['userId']
    environ['KAGGLE_KEY'] = kaggleCredentials['userKey']

def downloadKaggleDataset(
        kaggleCredentials: Credentials, 
        datasetName: str,
        downloadPath: str
        ) -> None:

    from kaggle.api.kaggle_api_extended import KaggleApi
    # Them initialize the kaggle api
    api = KaggleApi()
    # Authenticate
    api.authenticate()

    # Create parent folders if not existing
    path = Path(downloadPath)

    # Download dataset
    api.dataset_download_files(datasetName, downloadPath)

def initializeSpotifyAPI(
        credentialsPath: str = "../config/env.ini",
        spotifyUsername: str = "", 
        spotifyKey: str = ""
        ) -> Spotify:
    
    # Initialize the spotify web API python module
    spotifyCredentials: Credentials
    if not spotifyUsername or not spotifyKey:
        spotifyCredentials = getCredentials('SPOTIFY', credentialsPath)
    else:
        spotifyCredentials = {'userId': spotifyUsername, 'userKey': spotifyKey}

    # Details about the spotify web api usage via spotipy in:
    # https://spotipy.readthedocs.io/en/2.19.0/#
    cc = SpotifyClientCredentials(**{
        'client_id': spotifyCredentials['userId'],
        'client_secret': spotifyCredentials['userKey']
        })
    return Spotify(client_credentials_manager=cc)

def batch(listToBatch: list, batchSize: int) -> Generator:
    for i in range(0, len(listToBatch), batchSize):
        yield listToBatch[i:i+batchSize]
