# Spotify_Song_Recommender

Uses ML to generate a playlist containing recommended songs on Spotify. The user will need to make a Spotify for Developers account for the script to authorize the creation of the playlist and pull their data.

Although this is a finished product, I plan to refine this project using different ML methods to generate recommendations, preprocess the data differently, and work around rate-limiting issues that may arise with larger data pulls.

The current approach is to create a rating system using the audio features of my top tracks and artists in order to score tracks that I have saved in playlists. This forms a supervised regression problem that I can then use to make predictions about what songs (out of the thousands that Spotify "recommends") I determine are the best suited for me.

I thought that this approach worked pretty well since the playlist it generated had a lot of songs I did end up liking. However, the rating system could be improved by using a different metric than I did (averages of my top tracks' audio features and a constant added if the artist is part of my top artists).

My plans to continue to refine this project in the future include: testing out more regression models, using a different system to rate my training data, and pulling more useable data from Spotify itself.
