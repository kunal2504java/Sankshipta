import os
import whisper
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
import yt_dlp
from pytube import YouTube

# OAuth2 Scopes (Required for captions)
SCOPES = ['https://www.googleapis.com/auth/youtube.force-ssl']

def authenticate():
    """Authenticate and return credentials."""
    flow = InstalledAppFlow.from_client_secrets_file(
        'credentials.json',
        SCOPES
    )
    return flow.run_local_server(port=0)

def download_caption(video_id):
    """Download captions using YouTube Data API."""
    try:
        credentials = authenticate()
        youtube = build('youtube', 'v3', credentials=credentials)
        
        # Fetch list of captions
        captions = youtube.captions().list(part='snippet', videoId=video_id).execute()
        if not captions.get('items'):
            print("No captions available via API.")
            return None
        
        caption_id = captions['items'][0]['id']
        
        # Download caption as plain text (SRT format)
        request = youtube.captions().download(id=caption_id, tfmt='srt')
        response = request.execute()  # This returns raw text, not JSON
        
        if response is None or response.strip() == "":
            print("Empty transcript from API.")
            return None
        
        print("Transcript from API:")
        print(response)
        return response
    except Exception as e:
        print(f"Error fetching transcript from API: {e}")
        return None

def download_subtitles(video_url):
    """Download auto-generated subtitles using yt-dlp."""
    ydl_opts = {
        'writesubtitles': True,
        'writeautomaticsub': True,
        'skip_download': True,
        'subtitlesformat': 'srt/vtt',  # Accept both srt and vtt
        'outtmpl': '%(id)s.%(ext)s',
    }

    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(video_url, download=False)
            if info and 'automatic_captions' in info and info['automatic_captions']:
                ydl.download([video_url])
                filename = f"{info['id']}.en.vtt"  # Get the downloaded filename
                print(f"Subtitles downloaded using yt-dlp to: {filename}")
                return filename  # Return the filename
            else:
                print("Auto-generated subtitles not available via yt-dlp.")
                return None
    except Exception as e:
        print(f"yt-dlp error: {e}")
        return None

def transcribe_audio(video_url):
    """Transcribe audio from the video using Whisper AI."""
    try:
        # Download video audio
        yt = YouTube(video_url)
        audio_stream = yt.streams.filter(only_audio=True).first()

        if not audio_stream:
            print("No audio stream found for video.")
            return

        audio_file = audio_stream.download(filename="temp_audio.mp4")

        # Load Whisper model and transcribe audio
        model = whisper.load_model("base")
        result = model.transcribe(audio_file)
        
        print("Transcription from Whisper:")
        print(result["text"])
    except Exception as e:
        print(f"Error during transcription with Whisper: {e}")

def vtt_to_text(vtt_filepath):
    """Convert VTT file to plain text."""
    try:
        with open(vtt_filepath, 'r', encoding='utf-8') as vtt_file:
            lines = vtt_file.readlines()
        
        text_lines = [line.strip() for line in lines if line.strip() and not line.startswith(('NOTE', 'WEBVTT')) and not '-->' in line]
        
        full_text = ' '.join(text_lines)
        return full_text
    except Exception as e:
        print(f"Error converting VTT to text: {e}")
        return None

def clean_transcription(raw_text):
    """Clean the raw transcription text."""
    cleaned_lines = []
    
    # Split the raw text into lines
    lines = raw_text.splitlines()
    
    for line in lines:
        # Remove <c> tags and timestamps
        cleaned_line = line.replace('<c>', '').replace('</c>', '')
        
        # Remove timestamps (anything that looks like <00:00:00>)
        cleaned_line = ''.join(filter(lambda x: not x.isdigit() and x not in ['<', '>'], cleaned_line))
        
        cleaned_lines.append(cleaned_line.strip())
    
    # Join cleaned lines into a single string
    return ' '.join(filter(None, cleaned_lines))

if __name__ == "__main__":
    video_id = "4s1Tcvm00pA"  # Replace with a valid video ID or URL
    video_url = f"https://www.youtube.com/watch?v={video_id}"

    # Attempt to download captions from the YouTube API
    transcript = download_caption(video_id)

    if transcript is None:
        # If no transcript is found, attempt to download subtitles with yt-dlp
        vtt_file = download_subtitles(video_url)
        
        if vtt_file:
            # Convert vtt to text if yt-dlp was successful
            raw_text = vtt_to_text(vtt_file)
            if raw_text:
                cleaned_text = clean_transcription(raw_text)
                print("Extracted and cleaned text from VTT:")
                print(cleaned_text)
            else:
                print("Failed to extract text from VTT file.")
        else:
            # If subtitles are not available, transcribe the audio directly
            transcribe_audio(video_url)
