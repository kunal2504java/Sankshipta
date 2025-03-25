import os
import openai
from dotenv import load_dotenv
import tiktoken  # For token counting
from youtube_transcript_api import YouTubeTranscriptApi
import yt_dlp

# Load environment variables
load_dotenv()
openai.api_key = os.getenv("OPENAI_API_KEY")

# Initialize tokenizer for GPT-3.5
tokenizer = tiktoken.encoding_for_model("gpt-3.5-turbo")

def chunk_text(text, max_tokens=3000):
    """Split text into chunks that fit within GPT-3.5's token limit"""
    tokens = tokenizer.encode(text)
    chunks = []
    
    for i in range(0, len(tokens), max_tokens):
        chunk = tokenizer.decode(tokens[i:i+max_tokens])
        chunks.append(chunk)
    
    return chunks

def summarize_transcript(transcript):
    """
    Summarize the transcript text using OpenAI's GPT-3.5-turbo model
    with chunking for long documents
    """
    try:
        if not transcript:
            raise ValueError("Empty transcript provided")
            
        # Split transcript into manageable chunks
        chunks = chunk_text(transcript)
        
        summaries = []
        for chunk in chunks:
            response = openai.ChatCompletion.create(
                model="gpt-3.5-turbo",
                messages=[
                    {"role": "system", "content": """You are a expert summarizer. Create:
                    1. A 3-5 sentence overview
                    2. Bullet points of key topics
                    3. Important quotes/statistics"""},
                    {"role": "user", "content": f"Summarize this content:\n{chunk}"}
                ],
                temperature=0.3,  # More factual output
                max_tokens=500,
                top_p=0.9
            )
            summaries.append(response.choices[0].message.content.strip())
            
        # Combine chunk summaries
        final_summary = "\n\n".join(summaries)
        
        # Optionally summarize the combined summaries
        if len(summaries) > 1:
            response = openai.ChatCompletion.create(
                model="gpt-3.5-turbo",
                messages=[
                    {"role": "system", "content": "You are a expert editor. Create a cohesive summary from these section summaries:"},
                    {"role": "user", "content": final_summary}
                ],
                temperature=0.3,
                max_tokens=700
            )
            final_summary = response.choices[0].message.content.strip()
            
        return final_summary
        
    except Exception as e:
        print(f"Error generating summary: {str(e)}")
        return None

def save_summary(summary, filename="summary.txt"):
    """Save summary to file with metadata"""
    with open(filename, "w", encoding="utf-8") as f:
        f.write(f"Video Summary ({os.getenv('VIDEO_ID')})\n")
        f.write("="*50 + "\n")
        f.write(summary)
    print(f"Summary saved to {filename}")

# Existing video processing functions (download_caption, download_subtitles, etc.)

if __name__ == "__main__":
    video_id = "4s1Tcvm00pA"
    
    # Get transcript using your existing functions
    transcript = "..."  # Your transcript retrieval logic
    
    if transcript:
        # Generate and save summary
        summary = summarize_transcript(transcript)
        if summary:
            print("\n=== Final Summary ===")
            print(summary)
            save_summary(summary)
            
            # Optional: Add quiz generation
            # quiz = generate_quiz(summary)
            # save_quiz(quiz)
