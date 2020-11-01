# youtube-likes-spotify-import
Create a Spotify playlist that contains all songs in your YouTube liked videos
1. Clone this repository.
2. Install all dependencies by running the following command:
```python
pip install -r dependencies.txt
```
3. Create a file named "spotify_bearer_token.json" in the top-level directory of the repository with the following format:
```json
{
	"user_id": "YOUR_SPOTIFY_USER_ID",
	"access_token": "YOUR_SPOTIFY_BEARER_TOKEN"
}
```
4. Visit the [Spotify Developer Console](https://developer.spotify.com/console/post-playlists/) to retrieve an OAuth token. Enter the token in the "access_token" field and your Spotify username in the "user_id" field of your spotify_bearer_token.json file.
5. Visit the [Google Develope Console](https://console.developers.google.com/apis/credentials), enable OAuth for YouTube Data API, and use the +Create Credentials button to create an OAuth 2.0 Client ID. Select "Desktop App" for Application type when creating the credentials. Then select your new client id and use the Download JSON button to download the credentials in a json file, rename it to "youtube_client_secret.json", and move it to the top-level directory of this repository.
6. Run the program using the following command:
```python
python import_songs.py
```
7. You will be prompted with a Google account url to visit and grant the program access to your account. Login to your account that you want to import your YouTube likes from, copy the token shown, and paste it into the prompt. It will then start adding your liked songs to a new Spotify playlist.
