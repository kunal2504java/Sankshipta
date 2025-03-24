from googleapiclient.discovery import build
import requests
#this fetches the transcripts from the youtube video 
# Set up YouTube API
API_KEY = 'YOUR GOOGLE API KEY'
youtube = build('youtube', 'v3', developerKey=API_KEY)

def get_video_transcript(video_id):
    try:
        # Fetch video details
        response = youtube.captions().list(part='snippet', videoId=video_id).execute()
        caption_id = response['items'][0]['id']

        # Fetch caption data
        caption_response = youtube.captions().download(id=caption_id).execute()
        transcript = caption_response.decode('utf-8')
        return transcript
    except Exception as e:
        print(f"Error fetching transcript: {e}")
        return None

# Example Usage
video_id = "PUvrAJHr6nM"
transcript = get_video_transcript(video_id)
if transcript:
    print("Transcript fetched successfully!")
    print(transcript)
else:
    print("Transcript not available.")
