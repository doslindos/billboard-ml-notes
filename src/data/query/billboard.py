from pathlib import Path
from csv import reader as CSVReader
from io import TextIOWrapper
from zipfile import ZipFile

from data.types.util import Credentials
from data.types.billboard import BillboardSong
from .util import getCredentials, setKaggleCredentialsToEnv, downloadKaggleDataset

def getBillboardData(
        pathToData: str, 
        dataFilename: str = 'charts.csv'
        ) -> list[BillboardSong]:
    
    # Read the data file
    all_tracks: list[BillboardSong] = []
    with ZipFile(pathToData) as z:
        with z.open(dataFilename, 'r') as f:
            for i, row in enumerate(CSVReader(TextIOWrapper(f, 'utf-8'))):
                if i == 0:
                    column_names: list = row
                    continue
                    
                track: BillboardSong = { column_names[j]: value for j, value in enumerate(row)}
                all_tracks.append(track)

    return all_tracks

def downloadBillboardData(
        datasetName: str,
        downloadPath: str = "../data/datasets/billboard/",
        credentialsPath: str = "../config/env.ini",
        kaggleUsername: str = "", 
        kaggleKey: str = ""
        ) -> None:


    kaggleCredentials: Credentials
    if not kaggleUsername or not kaggleKey:
        # Set the kaggle username and password as env variables
        # the Kaggle API is searching the credentials from a .kaggle forlder
        # this is run in a container so to save from a hassle, the credentials are read from env.init and set as env variables when this will run.

        # Fetch the credentials
        kaggleCredentials = getCredentials('KAGGLE', credentialsPath)
    else:
        kaggleCredentials = {'user': kaggleUsername, 'key': kaggleKey}

    # Set the credentials to enc
    setKaggleCredentialsToEnv(kaggleCredentials)
    downloadKaggleDataset(kaggleCredentials, datasetName, downloadPath)
