# Imports
# ------|
# `Module` spotipy: interact with users spotify
# `Function` SpotifyOAuth: provide authorization to pull data
# `Function` pprint: pretty print nested dictionaries for readability (for debugging)
# `Module` pandas (pd): tidying and handling data in tabular form
# `Module` requests: fetching data for track audios (spotipy was buggy with rate limits)
# `Module` json: fetching data for track audios 
# `Module` time: use the sleep function to avoid rate limits
# ------|
import spotipy
from spotipy.oauth2 import SpotifyOAuth
# from pprint import pprint
import pandas as pd
import requests
import json
import time


# Just a few constants...
# ----------------------|
CLIENT_ID = "..."
CLIENT_SECRET = "..."
REDIRECT_URL = "http://localhost:9001/callback"
SCOPE = "user-library-read user-top-read playlist-modify-public"

# Set up authentication
# --------------------|
sp = spotipy.Spotify(auth_manager = SpotifyOAuth(
  client_id = CLIENT_ID,
  client_secret = CLIENT_SECRET,
  redirect_uri = REDIRECT_URL,
  scope = SCOPE 
))


# Pretty print call to view an example of data pull
# ------------------------------------------------|
# pprint(sp.current_user_top_tracks())

def main(): 
  
  # Load top artist data
  # -------------------|
  print("\nGetting and Filtering Top Artist Data...\n")

  # Get the filtered list of top artists 
  top_artists = filter_limited(sp, sp.current_user_top_artists())
  # Create the data frame
  top_artists_df = get_top_artist_df(top_artists)
  # Save the data in a .pkl file
  top_artists_df.to_pickle("./top_artists.pkl")

  print("Artist Data Saved!")
  
  # Load top track data
  # ------------------| 
  print("\nGetting and Filtering Top Track Data...\n")

  # Get the filtered list of top tracks
  top_tracks = filter_limited(sp, sp.current_user_top_tracks())
  # Create the track data frame
  top_tracks_df = get_top_tracks_df(top_tracks)
  # Add the audio features
  top_tracks_df = add_track_audio_df(top_tracks_df)

  # Cleanup
  # top_tracks_df = pd.read_pickle("./top_tracks.pkl")
  # top_tracks_df = top_tracks_df.drop(0, axis = 1).assign(**top_tracks_df[0].apply(pd.Series))

  # Save the data in a .pkl file
  top_tracks_df.to_pickle("./top_tracks.pkl")

  print("Track Data Saved!")
  
  # Load playlist data
  # -----------------|
  print("\nGetting Playlist Data...\n")

  # Create the playlists data frame
  playlists_df = get_playlists_df(sp, sp.current_user_playlists())
  # Add the audio features
  playlists_df = add_track_audio_df(sp, playlists_df)
  # Save the data in a .pkl file
  playlists_df.to_pickle("./playlists.pkl")

  print("Playlist Data Saved!")

  # Load spotify recommendations data
  # --------------------------------|
  print("\nGetting Sample Spotify Track Recommendations...\n")

  playlists_df = pd.read_pickle("./playlists.pkl")

  # Housekeeping...
  search_space = [
  "Shea Butter Shampoo", "The Iceman !", "Bus No. 5509", "West End Coffee",
  "The intermediary 🚧", "Don’t forget the bouquet!", "Scare Tactics",
  "Tautology", "Tour Dates", "Biting the Bottleneck", "Project ⊗"
  ]
  filtered_playlists = playlists_df[playlists_df["playlist_name"].isin(search_space)]
  filtered_playlists = filtered_playlists.drop_duplicates(subset = "id", keep = "last")["id"].tolist()
  
  # Generating the sample recommendations
  recs = get_recs(sp, filtered_playlists)
  # Turning recs into a tidy dataframe
  recs_df = get_top_tracks_df(recs)

  # recs_df.to_pickle("./tmp.pkl")
  # recs_df = pd.read_pickle("./tmp.pkl")

  # Adding audio features
  recs_df = add_track_audio_df(recs_df)
  # Writing out to a .pkl file
  recs_df.to_pickle("./recommendations.pkl")

  print("Spotify Track Recommendations Saved!")
  

# Helper functions to preprocess the data
# --------------------------------------|
def filter_limited(sp, pull):
  """

  Filter data pull so that artists and tracks
  that are limited by region are removed

  :param sp: spotify.Spotify() instance
  :param pull: results from API pull request
  :return: a list containing the filtered pull data

  """
  
  # Initialize the raw results of the pull request
  raw = pull
  
  # Check if we have to switch intitial search space
  if "items" not in raw.keys():
    raw = raw["artists"]
  
  # Initialize the results list
  res = raw["items"]

  # Keep going until there is no more data
  while raw["next"]:
  
  # Go to the next page
    raw = sp.next(raw)

  # Check if we have to switch search spaces
  if "items" not in raw.keys():
    raw = raw["artists"]
  
  # Append data to res
  res.extend(raw["items"])

  return res


def get_top_artist_df(data):
  """

  Creates and returns a tidy pandas data frame of the top artists

  :param data: a list of filtered top artist data from API pull
  :return: a tidy pandas data frame containing top artist data

  """

  # Turn the list into a DataFrame
  top_artists_df = pd.DataFrame(data)

  # Tidy the df and extract important columns
  top_artists_df["followers"] = top_artists_df["followers"].apply(lambda x: x["total"])
  top_artists_df = top_artists_df[["id", "name", "followers", "type", "genres", "uri"]]

  return top_artists_df


def get_top_tracks_df(data):
  """

  Creates and returns a tidy pandas data frame of the top tracks

  :param data: a list of filtered top track data from API pull
  :return: a tidy pandas data frame containing top artist data

  """

  # Turn the list into a DataFrame
  top_tracks_df = pd.DataFrame(data)

  # Spread track values if not yet spread to columns
  if "track" in top_tracks_df.columns.tolist():
    top_tracks_df = top_tracks_df.drop("track", axis = 1).assign(**top_tracks_df["track"].apply(pd.Series))

  # Tidy the df and extract important columns

  # Album Properties
  top_tracks_df["album_id"] = top_tracks_df["album"].apply(lambda x: x["id"])
  top_tracks_df["album_name"] = top_tracks_df["album"].apply(lambda x: x["name"])
  top_tracks_df["album_release_date"] = top_tracks_df["album"].apply(lambda x: x["release_date"])
  top_tracks_df["album_tracks"] = top_tracks_df["album"].apply(lambda x: x["total_tracks"])
  top_tracks_df["album_type"] = top_tracks_df["album"].apply(lambda x: x["type"])

  # Album Artist Properties
  top_tracks_df["album_artist_id"] = top_tracks_df["album"].apply(lambda x: x["artists"][0]["id"])
  top_tracks_df["album_artist_name"] = top_tracks_df["album"].apply(lambda x: x["artists"][0]["name"])

  # Artist Properties
  top_tracks_df["artist_id"] = top_tracks_df["artists"].apply(lambda x: x[0]["id"])
  top_tracks_df["artist_name"] = top_tracks_df["artists"].apply(lambda x: x[0]["name"])

  # Extract important columns
  cols = [
  "id", "name", "popularity", "type", "is_local", "explicit", "duration_ms", "disc_number",
  "track_number", "artist_id", "artist_name", "album_artist_id", "album_artist_name",
  "album_id", "album_name", "album_release_date", "album_tracks", "album_type"
  ]

  # Saved tracks have the additional column "added_at"
  if "added_at" in top_tracks_df.columns.to_list():
    cols.append("added_at")

  top_tracks_df = top_tracks_df[cols]

  return top_tracks_df


def add_track_audio_df(df: pd.DataFrame):
  """

  Add the audio features that spotify shows to
  an already created dataframe containing track information

  :param df: pandas dataframe containing top track data
  :return: pandas dataframe with track audio data added 

  """
  
  # Genres
  # df["genres"] = df["artist_id"].apply(lambda x: sp.artist(x)["genres"])
  # df["album_genres"] = df["album_artist_id"].apply(lambda x: sp.artist(x)["genres"])

  def helper(id):
    url = "https://accounts.spotify.com/api/token"
    headers = {
      "Content-Type": "application/x-www-form-urlencoded",
    }
    data = {
      "grant_type": "client_credentials",
      "client_id": CLIENT_ID,
      "client_secret": CLIENT_SECRET,
    }
    response = requests.post(url, headers=headers, data=data)
    if response.status_code == 200:
      # Extract the access token from the response
      access_token = response.json()["access_token"]

      # Use the access token to make the API request
      headers = {
        "Authorization": f"Bearer {access_token}",
      }

      response = requests.get(f"https://api.spotify.com/v1/audio-features/{id}", headers=headers)
      print(response, end = "\n\n")

      if response.status_code == 200:
        return dict(response.json())
        # print("Successfully fetched the data with the provided parameters:")
        # print(json.dumps(response.json(), sort_keys=True, indent=4))
      else:
        print(f"There's a {response.status_code} error with your request")
    else:
      print("Failed to obtain the access token")
  
  # Audio features
  ids = []
  df["id"].apply(lambda x: ids.append(x))
  df["audio_features"] = pd.DataFrame(ids)
  
  for i in range(len(df)):
    df.at[i, "audio_features"] = helper(df.at[i, "audio_features"])
    # time.sleep(1)

  # df["audio_features"] = df["id"].apply(lambda x: sp.audio_features(x))
  # df = df.drop("audio_features", axis = 1).assign(**df["audio_features"].apply(pd.Series))

  return df

def get_playlists_df(sp, pull):
  """

  Creates and returns a tidy pandas dataframe containing
  tracks that are in user"s playlists

  :param sp: spotipy.Spotify() instance
  :param pull: sp.current_user_playlists() call
  :return: pandas dataframe containing playlist audio data

  """
  
  # Save the pull data
  playlists = pull

  # Initialize lists to be populated with playlist data
  items, data = playlists["items"], []
  ids, names, num_tracks = [], [], []

  # For each playlist, append track information
  # to corresponding list
  for pl in items:

    for _ in range(pl["tracks"]["total"]):
    
      ids.append(pl["id"])
      names.append(pl["name"])
      num_tracks.append(pl["tracks"]["total"])

    # Store the saved tracks
    saved = sp.playlist(pl["id"], fields = "tracks, next")

    # While there are more tracks saved in pl,
    # keep adding to data list
    res = saved["tracks"]
    data.extend(res["items"])
    while res["next"]:
      res = sp.next(res)
      data.extend(res["items"])
  
  # Initialize the dataframe to be returned
  playlist_df = pd.DataFrame(data)
  
  # Add the labels saved above
  playlist_df["playlist_id"] = ids
  playlist_df["playlist_name"] = names
  playlist_df["playlist_tracks"] = num_tracks

  # Remove local tracks b/c there is no audio data
  playlist_df = playlist_df[playlist_df["is_local"] == False]
  playlist_df = playlist_df.drop("track", axis = 1).assign(**playlist_df["track"].apply(pd.Series))

  # Album information
  playlist_df["album_id"] = playlist_df["album"].apply(lambda x: x["id"])
  playlist_df["album_name"] = playlist_df["album"].apply(lambda x: x["name"])
  playlist_df["album_release_date"] = playlist_df["album"].apply(lambda x: x["release_date"])
  playlist_df["album_tracks"] = playlist_df["album"].apply(lambda x: x["total_tracks"])
  playlist_df["album_type"] = playlist_df["album"].apply(lambda x: x["type"])

  # Album Arist information
  playlist_df["album_artist_id"] = playlist_df["album"].apply(lambda x: x["artists"][0]["id"])
  playlist_df["album_artist_name"] = playlist_df["album"].apply(lambda x: x["artists"][0]["name"])

  # Artist information
  playlist_df["artist_id"] = playlist_df["artists"].apply(lambda x: x[0]["id"])
  playlist_df["artist_name"] = playlist_df["artists"].apply(lambda x: x[0]["name"])

  # Extract important columns
  cols = [
  "id", "name", "popularity", "type", "is_local", "explicit", "duration_ms", "disc_number",
  "track_number", "artist_id", "artist_name", "album_artist_id", "album_artist_name",
  "album_id", "album_name", "album_release_date", "album_tracks", "album_type", "playlist_id",
  "playlist_name", "playlist_tracks", "added_at", "added_by"
  ]

  playlist_df = playlist_df[cols]

  return playlist_df


def get_recs(sp, search_space):
  """

  Generates track recommendations based off of search_space

  :param sp: spotipy.Spotify() instance
  :param search_space: filtered playlist tracks
  :return: list of spotify track recommendation ids

  """

  # Initialize a result list
  res = []

  # Generate recommendations for each track
  for t in search_space:

    recs = sp.recommendations(seed_tracks = [t])
    res.extend(recs["tracks"])

  return res


main()