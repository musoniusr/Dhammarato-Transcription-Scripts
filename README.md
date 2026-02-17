# Dhammarato Transcription Scripts

Automated pipeline that downloads Dhamma talk videos from YouTube, transcribes them
with AssemblyAI, generates AI summaries and tags with DeepSeek, and publishes
formatted blog posts to the Dhammarato website repository.

---

## 1. What this project does

1. Reads a list of YouTube video URLs from `list_of_videos.txt`
2. Downloads the audio from each video using `yt-dlp`
3. Transcribes the audio using AssemblyAI (with speaker diarization and Buddhist terminology prompting)
4. Generates a summary and topic tags using the DeepSeek AI API
5. Writes a formatted Markdown blog post into the website repository
6. Records each processed video in `processed_videos.csv` so no video is transcribed twice
7. Automatically syncs the manifest with collaborators via git pull/push

---

## 2. What you'll need

- **Python 3.10+** — [Download Python](https://www.python.org/downloads/)
- **git** — [Download git](https://git-scm.com/downloads)
- **yt-dlp** — Install via pip: `pip install yt-dlp`
- **ffmpeg** — Required by yt-dlp for audio conversion. [Download ffmpeg](https://ffmpeg.org/download.html) and add it to your PATH
- **AssemblyAI account** — [Sign up at assemblyai.com](https://www.assemblyai.com/) (free tier available)
- **DeepSeek account** — [Sign up at platform.deepseek.com](https://platform.deepseek.com/) (very low cost)
- A local clone of the **dhammarato-site** repository (for writing blog posts)

---

## 3. Step-by-step setup

### 3a. Clone this repository

```
git clone https://github.com/Dhammarato/Dhammarato-Transcription-Scripts.git
cd Dhammarato-Transcription-Scripts
```

### 3b. Install Python dependencies

```
pip install requests python-dotenv assemblyai
```

### 3c. Copy the example environment file

```
copy .env.example .env
```

On Mac/Linux:
```
cp .env.example .env
```

### 3d. Fill in your `.env` file

Open `.env` in any text editor (Notepad works fine) and fill in each variable:

| Variable | What to put |
|---|---|
| `ASSEMBLYAI_API_KEY` | Your AssemblyAI API key (from your account dashboard) |
| `DEEPSEEK_API_KEY` | Your DeepSeek API key (from your account dashboard) |
| `BASE_PATH` | Full path to the folder where audio and transcript files will be saved |
| `GITHUB_POSTS_PATH` | Full path to the `src/content/blog` folder inside your local clone of the site repo |
| `VIDEO_URLS_PATH` | Full path to the `list_of_videos.txt` file in this repository |

**Never share your `.env` file** — it contains your private API keys. It is already listed in `.gitignore` so git will not accidentally commit it.

---

## 4. How to find your folder paths (Windows)

1. Open **File Explorer** and navigate to the folder you want
2. Click on the **address bar** at the top of the window
3. The full path will be highlighted — press **Ctrl+C** to copy it
4. Paste it into your `.env` file after the `=` sign

Example:
```
BASE_PATH=C:\Users\yourname\Documents\Dhammarato\Dhammarato Diarized Transcript Files and Recordings
```

> Tip: You do not need to add quotes around paths with spaces — the script handles this automatically.

---

## 5. How to run the script

Open a terminal (Command Prompt or PowerShell) in the project folder and run:

```
python dhammarato_transcription_pipeline.py
```

The script will:
- Pull the latest `processed_videos.csv` from git
- Work through each URL in `list_of_videos.txt`
- Skip any video already in `processed_videos.csv`
- Print its progress as it goes
- Commit and push the updated `processed_videos.csv` when finished

A typical video takes 5–15 minutes to process (most of that is transcription time).

---

## 6. Collaborative workflow

The script handles synchronization automatically:

- **At startup**: it runs `git pull` to get the latest manifest so you don't duplicate work
- **At the end**: it runs `git commit` and `git push` to share your results

### If git pull reports a conflict

This can happen if two volunteers finish at the same time. To resolve:

1. Open a terminal in the project folder
2. Run: `git status` — this shows which files conflict
3. The only file that should ever conflict is `processed_videos.csv`
4. Run: `git checkout --theirs processed_videos.csv` — this keeps the remote version
5. Run: `git add processed_videos.csv && git rebase --continue`
6. Then re-run the script — it will safely re-add your newly processed videos

If you are unsure what to do, reach out on the project Discord or open a GitHub issue.

---

## 7. What the output files are

| File | Description |
|---|---|
| `processed_videos.csv` | Shared manifest tracking every video that has been processed. Committed to git so all collaborators share it. |
| `list_of_videos.txt` | The input list of YouTube URLs to process. Edit this to add new videos. |
| `failed_videos.txt` | Temporary list of videos that failed during the current run. Not committed to git. |
| `<date>-<title>.md` (in BASE_PATH) | Local transcript file with speaker diarization, saved in your audio/transcript folder. |
| `<date>-<title>.txt` (in BASE_PATH) | Plain text version of the transcript. |
| `<date>-<title>.md` (in GITHUB_POSTS_PATH) | Formatted blog post with front matter, AI summary, and tags, saved to the website repo. |

---

## Questions or problems?

Open an issue on GitHub or ask in the Dhamma Friends Discord:
[discord.com/invite/kmQUUJysZJ](https://discord.com/invite/kmQUUJysZJ)
