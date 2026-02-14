import subprocess
import requests
import time
import os
import json
from datetime import datetime
from pathlib import Path
import re
from dotenv import load_dotenv

# Load environment variables from .env file in the same directory as this script
load_dotenv(Path(__file__).parent / '.env')

# Base paths
base_path = r'C:\Users\docsu\Documents\Dhammarato\Dhammarato Diarized Transcript Files and Recordings'
github_posts_path = r'G:\Work-Home Sync\Dhammarato.com\dhammarato-site\src\content\blog'
video_urls_path = r'G:\Work-Home Sync\Dhammarato.com\Dhammarato Transcription Scripts\list_of_videos.txt'

def extract_date_from_title(title):
    date_pattern = r'(\d{2})[./-](\d{2})[./-](\d{2})'
    match = re.search(date_pattern, title)

    if match:
        month, day, year = match.groups()  # MM.DD.YY format
        try:
            return datetime.strptime(f"{year}-{month}-{day}", "%y-%m-%d")
        except ValueError:
            return None
    return None

def clean_title(title):
    # Remove special characters and replace with spaces
    cleaned = re.sub(r'[|#.]', ' ', title)
    # Replace multiple spaces with single space and strip
    cleaned = ' '.join(cleaned.split())
    return cleaned

def format_file_name(video_title, talk_date):
    sanitized = clean_title(video_title).lower()
    sanitized = ''.join(c if c.isalnum() or c.isspace() else '-' for c in sanitized)
    sanitized = '-'.join(filter(None, sanitized.split()))
    return f"{talk_date.strftime('%Y-%m-%d')}-{sanitized}.md"

def create_regular_front_matter(video_title, talk_date, upload_date, channel_name, video_id, assemblyai_transcript_id=None):
    front_matter = f"""---
created: {datetime.now().strftime('%Y-%m-%d')}
modified: {datetime.now().strftime('%Y-%m-%dT%H:%M:%S%z')}
dateofpublication: {upload_date.strftime('%Y-%m-%d')}
dateoftalk: {talk_date.strftime('%Y-%m-%d')}
author: {channel_name}
note_type: youtube transcript
tags: transcripts, youtube-videos
youtube: https://www.youtube.com/watch?v={video_id}"""
    if assemblyai_transcript_id:
        front_matter += f"\nassemblyai_transcript_id: {assemblyai_transcript_id}"
    front_matter += "\n---\n\n"
    return front_matter

def create_github_front_matter(video_title, talk_date, upload_date, channel_name, video_id, assemblyai_transcript_id=None, tags=None):
    cleaned_title = clean_title(video_title)
    if tags is None:
        tags = ["transcripts"]
    tags_str = ", ".join(tags)
    front_matter = f"""---
layout: post
title: "{cleaned_title}"
pubDate: {talk_date.strftime('%Y-%m-%d')}
author: Dhammarato
categories: [transcripts, Dhamma Talk]
tags: [{tags_str}]
image: "https://i.ytimg.com/vi/{video_id}/maxresdefault.jpg"
description: "Transcript of {talk_date.strftime('%B %d, %Y')} Dhamma Talk with Dhammarato and Friends"
featured: false
hidden: false
toc: true"""
    if assemblyai_transcript_id:
        front_matter += f"\nassemblyai_transcript_id: {assemblyai_transcript_id}"
    front_matter += f"""
---

## {cleaned_title}

### Video


<p><iframe style="width:100%;" height="315" src="https://www.youtube.com/embed/{video_id}?rel=0&amp;showinfo=0" frameborder="0" allowfullscreen></iframe></p>


### Transcript

"""
    return front_matter

def process_video(video_url):
    # Get video metadata first so we can check if audio already exists
    video_info = json.loads(subprocess.check_output(['yt-dlp', '--remote-components', 'ejs:github', '--dump-json', video_url]))
    video_title = video_info['title']
    upload_date = datetime.strptime(video_info['upload_date'], '%Y%m%d')
    talk_date = extract_date_from_title(video_title) or upload_date
    channel_name = video_info['channel']
    base_name = format_file_name(video_title, talk_date).replace('.md', '')

    # Check if audio already exists (from a previous interrupted run)
    # Search for any mp3 containing the video ID to handle special characters in titles
    existing_mp3s = [f for f in os.listdir(base_path) if f.endswith('.mp3') and video_title[:20] in f]
    if existing_mp3s:
        audio_file_path = os.path.join(base_path, existing_mp3s[0])
        print(f"Audio already exists, skipping download: {audio_file_path}")
    else:
        # Download the audio file
        subprocess.run(['yt-dlp', '--remote-components', 'ejs:github', '-x', '--audio-format', 'mp3', '--output', os.path.join(base_path, '%(title)s.%(ext)s'), video_url])
        # Get the most recently created .mp3 file
        audio_file_path = max(
            (os.path.join(base_path, f) for f in os.listdir(base_path) if f.endswith('.mp3')),
            key=os.path.getctime
        )

    # Path where the transcript files will be saved
    txt_transcript_file_path = os.path.join(base_path, f'{base_name}.txt')
    md_transcript_file_path = os.path.join(base_path, f'{base_name}.md')

    # Upload audio to AssemblyAI
    api_key = os.getenv("ASSEMBLYAI_API_KEY")
    base_api_url = "https://api.assemblyai.com"
    headers = {"authorization": api_key}

    print("Uploading audio to AssemblyAI...")
    with open(audio_file_path, "rb") as f:
        upload_response = requests.post(base_api_url + "/v2/upload", headers=headers, data=f)
    audio_url = upload_response.json()["upload_url"]

    # Request transcription with universal-3-pro and prompt
    transcript_request = {
        "audio_url": audio_url,
        "speech_models": ["universal-3-pro"],
        "speaker_labels": True,
        "prompt": "Mandatory: Transcribe this audio with attention to proper nouns and Buddhist terminology. Required: Use standard spelling and contextually correct spelling of all names and Buddhist terms including Anagami, Anapanasati, Anicca, Arahant, Arhat, Arya, Bhavana, Bhikkhuni, Bhikku, Bhante, Bodhisattva, Citta, Dhamma, Dharma, Dukkha, Hinayana, Jhana, Kamma, Karuna, Mahayana, Mandala, Mantra, Mara, Marga, Metta, Mudita, Mudra, Nibbana, Nirodha, Nivarana, Panna, Paramita, Parinibbana, Paticcasamuppada, Pañña, Piti, Prajna, Puja, Saddha, Sakadagami, Samadhi, Samatha, Samma Sanghappa, Samsara, Samskara, Sangha, Sankhara, Sati, Sila, Srotapanna, Sukkha, Sunyata, Tanha, Tathagata, Upadana, Upaya, Upekkha, Vajrayana, Vedana, Vinaya, Vipassana, Viriya and speaker names.  The main speaker is Dhammarato. Context: Buddhist teaching discussion with multiple participants.",
    }

    print("Starting transcription...")
    response = requests.post(base_api_url + "/v2/transcript", json=transcript_request, headers=headers)
    transcript_id = response.json()["id"]
    polling_endpoint = base_api_url + "/v2/transcript/" + transcript_id

    # Poll for completion
    while True:
        result = requests.get(polling_endpoint, headers=headers).json()
        if result["status"] == "completed":
            print("Transcription completed.")
            break
        elif result["status"] == "error":
            print(f"Transcription failed: {result['error']}")
            return None
        else:
            print(f"Transcription status: {result['status']}...")
            time.sleep(5)

    # Get utterances for speaker diarization
    utterances = result.get("utterances", [])

    # Write the transcript to the .txt file
    with open(txt_transcript_file_path, 'w', encoding='utf-8') as f:
        f.write(create_regular_front_matter(video_title, talk_date, upload_date, channel_name, video_info['id'], transcript_id))
        for utterance in utterances:
            f.write(f"Speaker {utterance['speaker']}: {utterance['text']}\n\n")

    # Write the transcript to the .md file
    with open(md_transcript_file_path, 'w', encoding='utf-8') as f:
        f.write(create_regular_front_matter(video_title, talk_date, upload_date, channel_name, video_info['id'], transcript_id))
        for utterance in utterances:
            f.write(f"**Speaker {utterance['speaker']}:** {utterance['text']}\n\n")

    return {
        'title': video_title,
        'talk_date': talk_date,
        'upload_date': upload_date,
        'channel_name': channel_name,
        'video_id': video_info['id'],
        'transcript_id': transcript_id,
        'transcript_path': md_transcript_file_path,
        'base_name': base_name
    }

def generate_ai_summary(transcript_text):
    api_key = os.getenv("DEEPSEEK_API_KEY")
    if not api_key:
        print("Warning: DEEPSEEK_API_KEY not set, skipping AI summary.")
        return "\n### Summary\n\n*AI summary not available — DEEPSEEK_API_KEY not configured.*\n\n### Metaphors and Stories\n\n*AI summary not available — DEEPSEEK_API_KEY not configured.*\n"

    api_url = "https://api.deepseek.com/v1/chat/completions"
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
    }

    # Request 1: Summary
    print("Generating AI summary...")
    summary_response = requests.post(api_url, headers=headers, json={
        "model": "deepseek-chat",
        "messages": [
            {"role": "user", "content": f"Can you give me a summary of this Dhamma talk with Dhammarato and Sangha friends?\n\n{transcript_text}"}
        ],
    })
    summary_text = summary_response.json()["choices"][0]["message"]["content"]

    # Request 2: Metaphors and Stories
    print("Generating metaphors and stories...")
    metaphors_response = requests.post(api_url, headers=headers, json={
        "model": "deepseek-chat",
        "messages": [
            {"role": "user", "content": f"What metaphors and stories are used in this talk?\n\n{transcript_text}"}
        ],
    })
    metaphors_text = metaphors_response.json()["choices"][0]["message"]["content"]

    return f"\n### Summary\n\n{summary_text}\n\n### Metaphors and Stories\n\n{metaphors_text}\n"


def generate_ai_tags(transcript_text):
    api_key = os.getenv("DEEPSEEK_API_KEY")
    if not api_key:
        print("Warning: DEEPSEEK_API_KEY not set, skipping AI tags.")
        return ["transcripts"]

    api_url = "https://api.deepseek.com/v1/chat/completions"
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
    }

    print("Generating AI tags...")
    response = requests.post(api_url, headers=headers, json={
        "model": "deepseek-chat",
        "messages": [
            {"role": "user", "content": (
                "Analyze this Dhamma talk transcript and return a comma-separated list of relevant tags. "
                "Always include 'transcripts' as the first tag. "
                "Add tags for key Buddhist concepts discussed (e.g., metta, karuna, sila, jhana, anapanasati, sati, dukkha, sukkha, nibbana, sankhara, vedana, vipassana, samadhi). "
                "Add tags for talk types (e.g., sangha-us, sangha-uk, one-on-one). "
                "Add tags for major themes (e.g., nurturing, compassion, mindfulness, meditation, brahma-viharas, noble-eightfold-path). "
                "Use lowercase, hyphenated tags only. Return ONLY the comma-separated list, nothing else.\n\n"
                f"{transcript_text}"
            )}
        ],
    })
    tags_text = response.json()["choices"][0]["message"]["content"].strip()
    tags = [tag.strip() for tag in tags_text.split(",") if tag.strip()]
    # Ensure 'transcripts' is always first
    if "transcripts" not in tags:
        tags.insert(0, "transcripts")
    return tags


def create_github_markdown(video_url, assemblyai_transcript_id=None):
    video_info = json.loads(subprocess.check_output(['yt-dlp', '--remote-components', 'ejs:github', '--dump-json', video_url]))
    video_title = video_info['title']
    upload_date = datetime.strptime(video_info['upload_date'], '%Y%m%d')
    talk_date = extract_date_from_title(video_title) or upload_date
    channel_name = video_info['channel']
    video_id = video_info['id']

    file_name = format_file_name(video_title, talk_date)
    base_name = file_name.replace('.md', '')

    source_md_path = os.path.join(base_path, f'{base_name}.md')
    with open(source_md_path, 'r', encoding='utf-8') as f:
        transcript_content = f.read().split('---\n', 2)[-1]

    # Build raw transcript text for AI summary
    raw_lines = [line.strip() for line in transcript_content.strip().split('\n') if line.strip()]
    raw_transcript_text = '\n'.join(raw_lines)

    ai_summary = generate_ai_summary(raw_transcript_text)
    ai_tags = generate_ai_tags(raw_transcript_text)

    sangha_info = """
### Connect with Dhammarato and Sangha Friends

☸️ **Dhamma Friends Discord** — [Join our Discord](https://discord.com/invite/kmQUUJysZJ)
Join our Sangha on Discord and please send a friend request to Dhammarato

🌐 **Open Sangha Foundation** — [opensanghafoundation.org](https://opensanghafoundation.org/)
Connect with friends, teachers, and explore places to visit and stay

▶️ **Youtube** — [Dhammarato Dhamma - YouTube](https://www.youtube.com/@DhammaratoDhamma)
Videos of Sanghas and One-on-One Calls

🎧 **Podcast** — [Podbean](https://dhammaratodhamma.podbean.com/)
Find our content on Spotify, Apple Podcasts, and more by visiting Podbean

📧 **E-mail Dhammarato** — dhammarato16@gmail.com
Please put name, age, location and practice info when sending an e-mail
"""

    github_markdown_path = os.path.join(github_posts_path, file_name)
    with open(github_markdown_path, 'w', encoding='utf-8') as f:
        f.write(create_github_front_matter(video_title, talk_date, upload_date, channel_name, video_id, assemblyai_transcript_id, ai_tags))
        f.write(transcript_content)
        f.write(ai_summary)
        f.write(sangha_info)

# Process each YouTube video
with open(video_urls_path, 'r') as file:
    lines = file.read().splitlines()

for line in lines:
    line = line.strip()
    if not line:
        continue
    # Extract YouTube URL from pipe-delimited format or use as-is
    if '|' in line:
        # Format: NA | Title | Info | Date | URL
        parts = [p.strip() for p in line.split('|')]
        video_url = next((p for p in parts if 'youtube.com' in p or 'youtu.be' in p), None)
        if not video_url:
            print(f"No YouTube URL found in line: {line}")
            continue
    else:
        video_url = line

    # Extract video ID for deduplication check
    video_id_match = re.search(r'[?&]v=([a-zA-Z0-9_-]{11})', video_url)
    if video_id_match:
        video_id = video_id_match.group(1)
        print(f"Checking for duplicates: {video_id}...")
        # Check if a blog post already contains this video ID (embedded in iframe or front matter)
        existing = [f for f in os.listdir(github_posts_path) if f.endswith('.md')]
        already_exists = False
        for fname in existing:
            fpath = os.path.join(github_posts_path, fname)
            with open(fpath, 'r', encoding='utf-8') as check_f:
                if video_id in check_f.read():
                    print(f"  -> SKIP (already exists): {fname}")
                    already_exists = True
                    break
        if already_exists:
            continue

    print(f"Processing video: {video_url}")
    video_info = process_video(video_url)
    if video_info:
        create_github_markdown(video_url, video_info.get('transcript_id'))
        print(f"Completed processing video: {video_info['title']}")
    else:
        print(f"Failed to process video: {video_url}")
