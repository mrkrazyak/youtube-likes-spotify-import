import os

import google_auth_oauthlib.flow
import googleapiclient.discovery
import googleapiclient.errors
import requests
import json

youtube_auth_scopes = ["https://www.googleapis.com/auth/youtube.readonly"]
playlist_name = "YouTube Likes"
playlist_description = "A playlist containing all liked songs on YouTube"


class SongImport:
    def __init__(self):
        self.youtube_client = self.get_youtube_client()
        self.song_info = {}
        with open("spotify_bearer_token.json") as f:
            data = json.load(f)
            self.spotify_bearer_token = data["access_token"]
            self.spotify_user_id = data["user_id"]

    def get_youtube_client(self):
        """Initialize a YouTube client that uses credentials stored in the youtube_client_secret.json file"""
        # Disable OAuthlib's HTTPS verification when running locally.
        # *DO NOT* leave this option enabled in production.
        os.environ["OAUTHLIB_INSECURE_TRANSPORT"] = "1"

        api_service_name = "youtube"
        api_version = "v3"
        client_secrets_file = "youtube_client_secret.json"

        # Get credentials and create an API client
        flow = google_auth_oauthlib.flow.InstalledAppFlow.from_client_secrets_file(
            client_secrets_file, youtube_auth_scopes)
        credentials = flow.run_console()
        youtube = googleapiclient.discovery.build(
            api_service_name, api_version, credentials=credentials)

        return youtube

    def get_liked_videos(self):
        """Gets all liked YouTube videos and saves artist and track info for any songs"""
        max_results = 50
        request = self.youtube_client.videos().list(
            part="snippet,contentDetails,statistics",
            maxResults=max_results,
            myRating="like"
        )
        response = request.execute()
        self.store_video_tracks_and_artists(response)
        num_pages_processed = 1
        print(str(max_results) + " YouTube likes processed")
        next_page_token = response["nextPageToken"]
        while next_page_token is not None:
            request = self.youtube_client.videos().list(
                part="snippet,contentDetails,statistics",
                maxResults=max_results,
                myRating="like",
                pageToken=next_page_token
            )
            response = request.execute()
            self.store_video_tracks_and_artists(response)
            num_pages_processed += 1
            videos_processed = num_pages_processed * max_results
            print(str(videos_processed) + " YouTube likes processed")
            if "nextPageToken" in response:
                next_page_token = response["nextPageToken"]
            else:
                break

    def find_playlist(self, name):
        """Searches all user playlists for one matching the name passed in, returns the playlist id if it is found"""
        max_limit = 50
        offset = 0
        has_next = True
        while has_next:
            query = "https://api.spotify.com/v1/users/{}/playlists?limit={}&offset={}".format(
                self.spotify_user_id, max_limit, offset)
            response = requests.get(
                query,
                headers={
                    "Content-Type": "application/json",
                    "Authorization": "Bearer {}".format(self.spotify_bearer_token)
                }
            )
            response_json = response.json()
            playlists = response_json["items"]
            for playlist in playlists:
                if playlist["name"].lower() == name.lower():
                    return playlist["id"]
            has_next = "next" in response_json and response_json["next"] is not None
            offset += 50
        return None

    def prepare_song_details_for_query(self, track, artist):
        """Formats the track and artist strings to be used in the Spotify search query"""
        track = track.replace(" ", "%20").replace("#", "")
        artist = artist.replace(" ", "%20").replace("#", "")
        return track, artist

    def find_song_uri(self, track, artist):
        """Searches for a song on Spotify matching the track and artist provided and returns the track uri"""
        track, artist = self.prepare_song_details_for_query(track, artist)
        query = "https://api.spotify.com/v1/search?query=track%3A{}+artist%3A{}&type=track&offset={}&limit={}".format(
            track, artist, 0, 1)
        response = requests.get(
            query,
            headers={
                "Content-Type": "application/json",
                "Authorization": "Bearer {}".format(self.spotify_bearer_token)
            }
        )
        response_json = response.json()
        if response_json["tracks"]["items"]:
            return response_json["tracks"]["items"][0]["uri"]
        else:
            return None

    def create_playlist(self, name, description):
        """Creates a Spotify playlist with the name and description passed in"""
        request_body = json.dumps({
            "name": name,
            "description": description,
            "public": True
        })
        query = "https://api.spotify.com/v1/users/{}/playlists".format(
            self.spotify_user_id)
        response = requests.post(
            query,
            data=request_body,
            headers={
                "Content-Type": "application/json",
                "Authorization": "Bearer {}".format(self.spotify_bearer_token)
            }
        )
        print("Created new playlist called: " + name)
        response_json = response.json()
        return response_json["id"]

    def store_video_tracks_and_artists(self, videos):
        """Parses a JSON response containing YouTube likes and stores info for any songs in song_info"""
        for video in videos["items"]:
            title = video["snippet"]["title"]
            if "-" in title:
                items = title.split("-")
                if len(items) == 2:
                    artist = items[0].strip()
                    track = items[1].strip()
                    if "(" in track:
                        track = track.split("(", 1)[0].strip()
                    uri = self.find_song_uri(track, artist)
                    if uri is not None:
                        self.song_info[title] = {
                            "artist": artist,
                            "track": track,
                            "spotify_uri": uri
                        }

    def get_playlist_track_uris(self, playlist_id):
        """Returns a list of all track uris in the playlist_id passed in"""
        query = "https://api.spotify.com/v1/playlists/{}/tracks".format(
            playlist_id)
        response = requests.get(
            query,
            headers={
                "Content-Type": "application/json",
                "Authorization": "Bearer {}".format(self.spotify_bearer_token)
            }
        )
        response_json = response.json()
        uris = []
        for item in response_json["items"]:
            uri = item["track"]["uri"]
            uris.append(uri)
        return uris

    def determine_track_uris_to_add(self, playlist_track_uris):
        """Returns a list of track uris found in liked videos that are not in the list of track uris passed in"""
        track_uris_to_add = []
        for key, value in self.song_info.items():
            if value["spotify_uri"] not in playlist_track_uris:
                track_uris_to_add.append(value["spotify_uri"])
        return track_uris_to_add

    def add_tracks_to_playlist(self, playlist_id, track_uris):
        """Add the list of track uris to the playlist_id passed in"""
        # TODO: Send multiple requests if number of tracks to add is over 100, endpoint accepts up to 100 track uris
        query = "https://api.spotify.com/v1/playlists/{}/tracks".format(
            playlist_id)
        request_data = json.dumps(track_uris)
        response = requests.post(
            query,
            data=request_data,
            headers={
                "Content-Type": "application/json",
                "Authorization": "Bearer {}".format(self.spotify_bearer_token)
            }
        )
        response_json = response.json()
        return response_json["snapshot_id"]

    def start_import(self):
        """Main method that finds all liked songs on YouTube and adds them to a Spotify playlist"""
        print("Starting song import...")
        print("Searching Spotify for liked YouTube videos...")
        self.get_liked_videos()
        if len(self.song_info.items()) == 0:
            print("No songs found in liked videos!")
            return
        playlist_id = self.find_playlist(playlist_name)
        if playlist_id is None:
            playlist_id = self.create_playlist(playlist_name, playlist_description)
            playlist_track_uris = []
        else:
            playlist_track_uris = self.get_playlist_track_uris(playlist_id)
            print("Found Spotify playlist titled " + playlist_name)
        uris_to_add = self.determine_track_uris_to_add(playlist_track_uris)
        if uris_to_add:
            print("Adding " + str(len(uris_to_add)) + " songs to playlist")
            playlist_snapshot_id = self.add_tracks_to_playlist(playlist_id, uris_to_add)
            print("Current playlist snapshot id: " + playlist_snapshot_id)
        else:
            print("No new songs from YouTube likes to add to playlist")
        print("Import complete!")


if __name__ == "__main__":
    si = SongImport()
    si.start_import()
