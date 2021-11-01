from typing import Union, Generator
from pathlib import Path
from random import sample as rndSample
from sys import exit

from spotipy import Spotify
from fuzzywuzzy import fuzz
from requests.exceptions import ReadTimeout

from .util import (
        batch,
        getCredentials, 
        initializeSpotifyAPI, 
        loadJson, 
        saveJson
        )
from data.types.util import Credentials
from data.types.billboard import BillboardSong
from data.types.spotify import (
        SpotifyAlbum, 
        SpotifyArtist, 
        SpotifyFeatures,
        SpotifySongData, 
        SpotifySongInfo, 
        SpotifySongQueryResult
        )

# List of blacklisted string in the results
# a query can result in a different version of the song that's actually been fetched
# so this is a blocking measure to not include them
blackList = [
        'Version', 
        'Instrumental',
        'Emulation',
        'Remix'
        ]

whiteList = [
        "Taylor's Version", 
        'No New Friends', 
        'Karate Chop',
        'Get Sleazier',
        "Don't cry me Argentina",
        'Outta Control',
        'A Country Boy Can Survive',
        'Turn It Up /',
        "Love Theme From St.Elmo's Fire"
        ]

def checkIfBlackListed(name: str) -> bool:
    for blackListed in blackList:
        if blackListed.lower() in name.lower():
            for whiteListed in whiteList:
                if whiteListed.lower() in name.lower():
                    return False
            return True
    return False

def parseSongInfo(
        songRaw: dict, 
        addAlbum: bool = True
        ) -> SpotifySongInfo:
    songID: str = songRaw['id']
    songName: str = songRaw['name']
    artists: list[SpotifyArtist] = []
    for spotifyArtist in songRaw['artists']:
        artists.append({
            'name': spotifyArtist['name'], 
            'artistID': spotifyArtist['id']
            })

    if addAlbum:
        album: SpotifyAlbum = {
            'name': songRaw['album']['name'],
            'albumID': songRaw['album']['id'],
            'totalTracks': songRaw['album']['total_tracks'],
            'releaseDate': songRaw['album']['release_date']
            }

    info: SpotifySongInfo = {
            'name': songName,
            'songID': songID,
            'artists': artists,
            'album': album if addAlbum else None
                }

    return info


def songQuery(
        api: Spotify, 
        query: str, 
        limit: int = 10
        ) -> list[SpotifySongInfo]:
    infos: list[SpotifySongInfo] = []
    queried: bool = False
    queryNum: int = 1
    queryLimit: int = 10
    try:
        while not queried:
            if queryNum >= queryLimit:
                raise Exception
            try:
                queryNum +=1
                for result in api.search(query, limit)['tracks']['items']: 
                    infos.append(parseSongInfo(result))
                queried = True
            except ReadTimeout:
                print("Timed out trying again...")
    except Exception:
        print("Max query num over...")
        print("exiting...")
        exit()

    return infos

def songMatching(
        songToMatch: str, 
        artistToMatch: str,
        resultSong: str,
        resultArtists: list, 
        allowedRatio: int = 80
        ) -> bool:
    
    if checkIfBlackListed(resultSong):
        return False
    
    # Exact match search
    if allowedRatio == 100:
        if songToMatch.lower() == resultSong.lower():
            # If song name matches check if the artist is found in artists
            # and if it is, this will be enough to add the song
            if 95 <= fuzz.token_set_ratio(artistToMatch, ' '.join((artist['name'] for artist in resultArtists))):
                return True
        return False
    
    # Some tracks do not match exactly for example feature feat. etc
    # so they can be fetched by matching based on tokens after tokenization of the strings
    if allowedRatio <= fuzz.token_set_ratio(songToMatch, resultSong):
        if allowedRatio <= fuzz.token_set_ratio(artistToMatch ,' '.join((artist['name'] for artist in resultArtists))):
            return True
        return False
    
    return False

def getSpotifyDataFromBillboardSongs(
        api: Spotify,
        billboardTracks: list[BillboardSong],
        savePath: str = "../datasets/spotify/spotifyData.json"
        ) -> list[SpotifySongInfo]:
    
    def fetchSongsByNameFromSpotify(
        tracks: Union[list, Generator],
        searchLimit: int = 1,
        matchingRatio: int = 80,
        useArtistInQuery: bool = True
        ) -> tuple[list, list[int], list[int]]:
    
        matches: list[SpotifySongQueryResult] = []
        unMatchedIndexes: list[int] = []
        # This is used to remove duplicates
        madeQueries: set[str] = set()
        duplicates: list[int] = []
        for i, track in enumerate(tracks):
            
            if i % 1000 == 0:
                print("Queried songs: ", i)
                print("Actual queries: ", len(madeQueries))
                
            billboardSongName: str = track['song']
            billboardArtistName: str = track['artist']
            
            query = billboardSongName
            if useArtistInQuery:
                query = query + ' ' + billboardArtistName
                
            if query not in madeQueries:
                madeQueries.add(query)
                unMatchedIndexes.append(i)
                for song in songQuery(api, query, searchLimit):
                    if songMatching(
                            billboardSongName, 
                            billboardArtistName, 
                            song['name'], 
                            song['artists'], 
                            matchingRatio
                            ):
                        matches.append({
                            'spotifyData': song, 
                            'searchQuery': query, 
                            'minMatchingRatioUsed': matchingRatio,
                            'originalData': track
                        })
                        unMatchedIndexes.pop()
                        break
            else:
                duplicates.append(i)
            
        return (matches, unMatchedIndexes, duplicates)
    
    if not Path(savePath).exists():
        print("Total number of songs to query: ", len(billboardTracks))
        # Call API to get the spotify info for tracks with a strict matching
        # Number of query results = 3 and only song name is used in query
        matched, notMatched, duplicates = fetchSongsByNameFromSpotify(billboardTracks, 3, 100, False)
        print("From %d exact matches: %d Duplicates: %d" % (len(billboardTracks), len(matched), len(duplicates)))
        # Try to get some matches where the matching isn't so strict
        # this is because the data does have some information with differing letters for example American vs European
        # + others that can be matched when the matching isn't so strict
        unexactMatches, noMatchThree, _ = fetchSongsByNameFromSpotify(
        (billboardTracks[i] for i in notMatched),
        3,
        90,
        True)
        print("From %d exact matches: %d" % (len(notMatched), len(unexactMatches)))
        print("Total matched %d / %d " % (len(matched + unexactMatches), len(billboardTracks)))
        saveJson(matched + unexactMatches, savePath)
    
    return loadJson(savePath)

def getSpotifyAudioFeatures(
        api: Spotify, 
        tracks: list[SpotifySongInfo]
        ) -> list[SpotifySongData]:

    allSpotifySongData: list[SpotifySongData] = []
    for trackBatch in batch(tracks, 50):
        trackIDGenerator: Generator = (track['spotifyData']['songID'] for track in trackBatch)
        for i, featuresResult in enumerate(api.audio_features(trackIDGenerator)):
            features: SpotifyFeatures = {}
            if featuresResult is not None:
                features = {
                    'timeSignature': featuresResult['time_signature'],
                    'durationMS': featuresResult['duration_ms'],
                    'key': featuresResult['key'],
                    'mode': featuresResult['mode'],
                    'acousticness': featuresResult['acousticness'],
                    'danceability': featuresResult['danceability'],
                    'energy': featuresResult['energy'],
                    'instrumentalness': featuresResult['instrumentalness'],
                    'liveness': featuresResult['liveness'],
                    'loudness': featuresResult['loudness'],
                    'speechiness': featuresResult['speechiness'],
                    'valence': featuresResult['valence'],
                    'tempo': featuresResult['tempo']
                }

            songData: SpotifySongData = {
                    'info': trackBatch[i],
                    'features': features
                    }

            allSpotifySongData.append(songData)

    return allSpotifySongData

def fetchAlbumTracks(
        api: Spotify, 
        trackInfo: list[SpotifySongInfo], 
        sampleSize: int = 5
        ) -> list[SpotifySongQueryResult]:
    # Loop album ids and fetch the track ids of tracks in every album
    queriedAlbumTracks: list[SpotifySongQueryResult] = []
    for i, track in enumerate(trackInfo):
        album: SpotifyAlbum = track['spotifyData']['album']
        albumTracks: list = api.album_tracks(album['albumID'])['items']
        if len(albumTracks) > 1:
            # Take a random sample of tracks
            trackSample: list = rndSample(albumTracks, sampleSize) if sampleSize > len(albumTracks) else rndSample(albumTracks, len(albumTracks))
            # Add ids of the random sample tracks to a list
            for albumTrack in trackSample:
                # Ignore duplicates (song based to fetch songs from album)
                # and blacklisted words in songs
                if  not checkIfBlackListed(albumTrack['name']) and albumTrack['id'] != track['spotifyData']['songID']:
                    data: SpotifySongQueryResult = {
                            'spotifyData': parseSongInfo(albumTrack, False)
                            }
                    data['spotifyData']['album'] = album
                    data['searchQuery'] = "Shares album with " + track['spotifyData']['name']
                    queriedAlbumTracks.append(data)

        if i % 100 == 0:
            print("Album ", i+1)

    return queriedAlbumTracks

def getSongsWithAlbums(
        api: Spotify,
        tracks: list[SpotifySongInfo], 
        randomSampleSize: int = 5
        ) -> list[SpotifySongData]:

    # Fetch the data for songs in a album
    songInfos: list[SpotifySongData] = fetchAlbumTracks(api, tracks, randomSampleSize)
    # Fetch feature data for tracks
    return getSpotifyAudioFeatures(api, songInfos)
