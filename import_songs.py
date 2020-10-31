import os

import google_auth_oauthlib.flow
import googleapiclient.discovery
import googleapiclient.errors

youtube_auth_scopes = ["https://www.googleapis.com/auth/youtube.readonly"]


def get_youtube_client():
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


def start_import():
    print("Starting song import...")
    youtube_client = get_youtube_client()
    print("Getting liked YouTube videos...")
    get_liked_videos(youtube_client)
    # print("Searching for liked songs and adding to Spotify playlist...")
    # TODO: Add spotify api calls
    # print("Import complete!")


def get_liked_videos(youtube_client):
    # TODO: This request returns 5 results per page, need to request more or loop through pages
    request = youtube_client.videos().list(
        part="snippet,contentDetails,statistics",
        myRating="like"
    )
    response = request.execute()
    print(response)
    return response


if __name__ == "__main__":
    start_import()
