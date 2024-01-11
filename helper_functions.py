import pandas as pd
import time
import os


def offset_api_limit(sp, sp_call):
    """
    Get all (non-limited) artists/tracks from a Spotify API call.
    :param sp: Spotify OAuth
    :param sp_call: API function all
    :return: list of artists/tracks
    """
    results = sp_call
    if 'items' not in results.keys():
        results = results['artists']
    data = results['items']
    while results['next']:
        results = sp.next(results)
        if 'items' not in results.keys():
            results = results['artists']
        data.extend(results['items'])
    return data


def get_artists_df(artists):
    """
    Transform and tidy Spotify artist data
    :param artists: list of Spotify artist data
    :return: formatted pandas dataframe
    """
    artists_df = pd.DataFrame(artists)
    artists_df['followers'] = artists_df['followers'].apply(lambda x: x['total'])
    return artists_df[['id', 'uri', 'type', 'name', 'genres', 'followers']]


def get_tracks_df(tracks):
    """
    Transform and tidy Spotify track data
    :param tracks: list of Spotify track data
    :return: formatted pandas dataframe
    """
    tracks_df = pd.DataFrame(tracks)
    # Spread track values if not yet spread to columns
    if 'track' in tracks_df.columns.tolist():
        tracks_df = tracks_df.drop('track', 1).assign(**tracks_df['track'].apply(pd.Series))
    # Album
    tracks_df['album_id'] = tracks_df['album'].apply(lambda x: x['id'])
    tracks_df['album_name'] = tracks_df['album'].apply(lambda x: x['name'])
    tracks_df['album_release_date'] = tracks_df['album'].apply(lambda x: x['release_date'])
    tracks_df['album_tracks'] = tracks_df['album'].apply(lambda x: x['total_tracks'])
    tracks_df['album_type'] = tracks_df['album'].apply(lambda x: x['type'])
    # Album Artist
    tracks_df['album_artist_id'] = tracks_df['album'].apply(lambda x: x['artists'][0]['id'])
    tracks_df['album_artist_name'] = tracks_df['album'].apply(lambda x: x['artists'][0]['name'])
    # Artist
    tracks_df['artist_id'] = tracks_df['artists'].apply(lambda x: x[0]['id'])
    tracks_df['artist_name'] = tracks_df['artists'].apply(lambda x: x[0]['name'])
    select_columns = ['id', 'name', 'popularity', 'type', 'is_local', 'explicit', 'duration_ms', 'disc_number',
                      'track_number',
                      'artist_id', 'artist_name', 'album_artist_id', 'album_artist_name',
                      'album_id', 'album_name', 'album_release_date', 'album_tracks', 'album_type']
    # saved_tracks has ['added_at', 'tracks']
    if 'added_at' in tracks_df.columns.tolist():
        select_columns.append('added_at')
    return tracks_df[select_columns]


def get_track_audio_df(sp, df):
    """
    Include Spotify audio features and analysis in track data.
    :param sp: Spotify OAuth
    :param df: pandas dataframe of Spotify track data
    :return: formatted pandas dataframe
    """

    '''
    df = df.copy()
    df['genres'] = df['artist_id'].apply(lambda x: sp.artist(x)['genres'])
    df['album_genres'] = df['album_artist_id'].apply(lambda x: sp.artist(x)['genres'])
    df['audio_features'] = df['id'].apply(lambda x: sp.audio_features(x))
    df['audio_features'] = df['audio_features'].apply(pd.Series)
    df = df.assign(**df['audio_features'].apply(pd.Series))
    # Don't need sp.audio_analysis(track_id) audio analysis for this project
    return df
    '''

    df = df.copy()

    df['genres'] = df['artist_id'].apply(lambda x: sp.artist(x)['genres'])
    df['album_genres'] = df['album_artist_id'].apply(lambda x: sp.artist(x)['genres'])

    df['audio_features'] = df['id'].apply(lambda x: sp.audio_features(x)[0] if sp.audio_features(x) else {})
    
    # Creating a DataFrame from audio_features
    audio_features_df = df['audio_features'].apply(pd.Series)
    audio_features_df.drop('id', axis=1, inplace=True)
    audio_features_df.drop('type', axis=1, inplace=True)
    audio_features_df.drop('duration_ms', axis=1, inplace=True)

    # Debugging: Print column names to check for duplicates
    # print("Columns in main df:", df.columns)
    # print("Columns in audio_features_df:", audio_features_df.columns)

    # Drop the original audio_features column from df
    df.drop('audio_features', axis=1, inplace=True)

    # Merge the new columns back to the main dataframe
    df = pd.concat([df, audio_features_df], axis=1)

    # print("Columns in merged df:", df.columns)

    return df


def get_all_playlist_tracks_df(sp, sp_call):
    """
    Get all (non-limited) tracks from a Spotify playlist API call
    :param sp:
    :param sp_call:
    :param sp: Spotify OAuth
    :param sp_call: API function all
    :return: list of tracks
    """
    playlists = sp_call
    playlist_data, data = playlists['items'], []
    playlist_ids, playlist_names, playlist_tracks = [], [], []
    # Uncomment this to pull every single saved playlist (commented out here to no blow up data size)
    # while playlists['next']:
    #     playlist_results = sp.next(playlists)
    #     playlist_data.extend(playlist_results['items'])
    for playlist in playlist_data:
        for i in range(playlist['tracks']['total']):
            playlist_ids.append(playlist['id'])
            playlist_names.append(playlist['name'])
            playlist_tracks.append(playlist['tracks']['total'])
        saved_tracks = sp.playlist(playlist['id'], fields="tracks, next")
        results = saved_tracks['tracks']
        data.extend(results['items'])
        while results['next']:
            results = sp.next(results)
            data.extend(results['items'])

    tracks_df = pd.DataFrame(data)
    # Playlists
    tracks_df['playlist_id'] = playlist_ids
    tracks_df['playlist_name'] = playlist_names
    tracks_df['playlist_tracks'] = playlist_tracks
    # Dataframe manipulation
    tracks_df = tracks_df[tracks_df['is_local'] == False]  # remove local tracks (no audio data)
    tracks_df = tracks_df.assign(**tracks_df['track'].apply(pd.Series))
    #tracks_df = tracks_df.drop('track', 1).assign(**tracks_df['track'].apply(pd.Series))
    # Album
    tracks_df['album_id'] = tracks_df['album'].apply(lambda x: x['id'])
    tracks_df['album_name'] = tracks_df['album'].apply(lambda x: x['name'])
    tracks_df['album_release_date'] = tracks_df['album'].apply(lambda x: x['release_date'])
    tracks_df['album_tracks'] = tracks_df['album'].apply(lambda x: x['total_tracks'])
    tracks_df['album_type'] = tracks_df['album'].apply(lambda x: x['type'])
    # Album Artist
    tracks_df['album_artist_id'] = tracks_df['album'].apply(lambda x: x['artists'][0]['id'])
    tracks_df['album_artist_name'] = tracks_df['album'].apply(lambda x: x['artists'][0]['name'])
    # Artist
    tracks_df['artist_id'] = tracks_df['artists'].apply(lambda x: x[0]['id'])
    tracks_df['artist_name'] = tracks_df['artists'].apply(lambda x: x[0]['name'])
    # playlist_tracks has ['added_at', 'added_by', 'is_local', 'primary_color', 'track', 'video_thumbnail']
    select_columns = ['id', 'name', 'popularity', 'type', 'is_local', 'explicit', 'duration_ms', 'disc_number',
                      'track_number',
                      'artist_id', 'artist_name', 'album_artist_id', 'album_artist_name',
                      'album_id', 'album_name', 'album_release_date', 'album_tracks', 'album_type',
                      'playlist_id', 'playlist_name', 'playlist_tracks',
                      'added_at', 'added_by']
    return tracks_df[select_columns]


def get_recs(sp, tracks, n=1):
    """
    Get recommendations from a list of Spotify track ids.
    :param sp: Spotify OAuth
    :param tracks: list of Spotify track ids
    :param n: batch number
    :return: list of tracks
    """
    data = []
    m = len(tracks)
    start = (n-1)*100
    end = min(n*100, m)
    filtered_tracks = tracks[start:end]
    for i, x in enumerate(filtered_tracks):

        results = sp.recommendations(seed_tracks=[x])  # default api limit of 20 is enough
        data.extend(results['tracks'])
        print(f'{i + (n-1)*100}/{m - 1} tracks processed')
        time.sleep(3.5)

        # Write out after every 100 tracks
        if (i + 1) % 100 == 0:
            df = get_tracks_df(data)
            df.to_pickle(f"./data/tmp_{n}.pkl")
            print(f'Intermediary save {n} done!')
            return data
    
    # Last batch
    df = get_tracks_df(data)
    df.to_pickle(f"./data/tmp_{n}.pkl")
    print(f'Intermediary save {n} done!')
        
    return data

def merge_temp_files(n):
    """
    Merge all temporary files into one dataframe.
    :param n: number of temporary files
    :return: merged dataframe
    """
    dfs = []
    for i in range(1, n + 1):
        temp_df = pd.read_pickle(f'./data/tmp_recs_audio_{{{i}}}.pkl')
        dfs.append(temp_df)
        # os.remove(f'./data/tmp_recs_audio_{i}.pkl') # Uncomment to remove temporary files
    df = pd.concat(dfs)

    return df