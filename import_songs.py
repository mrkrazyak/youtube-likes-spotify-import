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
        # self.youtube_client = self.get_youtube_client()
        with open("spotify_bearer_token.json") as f:
            data = json.load(f)
            self.spotify_bearer_token = data["access_token"]
            self.spotify_user_id = data["user_id"]

    def get_youtube_client(self):
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
        # TODO: This request returns 5 results per page, need to request more or loop through pages
        request = self.youtube_client.videos().list(
            part="snippet,contentDetails,statistics",
            myRating="like"
        )
        response = request.execute()
        print(response)
        return response

    def find_playlist(self, name):
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
            print(response_json)
            playlists = response_json["items"]
            for playlist in playlists:
                if playlist["name"].lower() == name.lower():
                    return playlist["id"]
            has_next = response_json["next"] is not None
            offset += 50
        return None

    def create_playlist(self, name, description):
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

    def start_import(self):
        print("Starting song import...")
        print("Getting liked YouTube videos...")
        # self.get_liked_videos()
        print("Searching for liked songs and adding to Spotify playlist...")
        playlist_id = self.find_playlist(playlist_name)
        if playlist_id is None:
            playlist_id = self.create_playlist(playlist_name, playlist_description)
        print("Import complete!")


if __name__ == "__main__":
    si = SongImport()
    si.start_import()
