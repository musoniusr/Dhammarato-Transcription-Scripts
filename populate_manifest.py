"""
One-time script to populate processed_videos.csv from existing blog posts
AND local transcript files.

Scans:
1. Blog posts in the site's blog directory
2. Local transcript .md files in the transcript recordings directory

Extracts:
- video_id: from image: ytimg URL, iframe embed, or youtube: frontmatter field
- title: from frontmatter
- filename: the .md filename
- pub_date: from frontmatter (pubDate or dateoftalk)
- assemblyai_transcript_id: from frontmatter (if present)
"""

import csv
import os
import re

BLOG_DIR = r'G:\Work-Home Sync\Dhammarato.com\dhammarato-site\src\content\blog'
LOCAL_TRANSCRIPT_DIR = r'C:\Users\docsu\Documents\Dhammarato\Dhammarato Diarized Transcript Files and Recordings'
CSV_PATH = os.path.join(os.path.dirname(__file__), 'processed_videos.csv')

# Patterns to extract video ID
IMAGE_PATTERN = re.compile(r'image:\s*"https://i\.ytimg\.com/vi/([a-zA-Z0-9_-]{11})/')
EMBED_PATTERN = re.compile(r'youtube\.com/embed/([a-zA-Z0-9_-]{11})')
YOUTUBE_URL_PATTERN = re.compile(r'^youtube:\s*https://www\.youtube\.com/watch\?v=([a-zA-Z0-9_-]{11})', re.MULTILINE)

# Frontmatter field patterns
TITLE_PATTERN = re.compile(r'^title:\s*["\']?(.*?)["\']?\s*$', re.MULTILINE)
PUBDATE_PATTERN = re.compile(r'^pubDate:\s*(\S+)', re.MULTILINE)
DATEOFTALK_PATTERN = re.compile(r'^dateoftalk:\s*(\S+)', re.MULTILINE)
TRANSCRIPT_ID_PATTERN = re.compile(r'^assemblyai_transcript_id:\s*(\S+)', re.MULTILINE)


def extract_video_id(content):
    """Extract video ID from file content, trying multiple patterns."""
    for pattern in [IMAGE_PATTERN, EMBED_PATTERN, YOUTUBE_URL_PATTERN]:
        m = pattern.search(content)
        if m:
            return m.group(1)
    return None


def extract_from_blog_post(filepath):
    """Extract video metadata from a blog post file."""
    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()

    video_id = extract_video_id(content)
    if not video_id:
        return None

    title = ''
    m = TITLE_PATTERN.search(content)
    if m:
        title = m.group(1).strip().strip('"').strip("'")

    pub_date = ''
    m = PUBDATE_PATTERN.search(content)
    if m:
        pub_date = m.group(1)

    transcript_id = ''
    m = TRANSCRIPT_ID_PATTERN.search(content)
    if m:
        transcript_id = m.group(1)

    return {
        'video_id': video_id,
        'title': title,
        'filename': os.path.basename(filepath),
        'pub_date': pub_date,
        'assemblyai_transcript_id': transcript_id,
    }


def extract_from_local_transcript(filepath):
    """Extract video metadata from a local transcript .md file."""
    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()

    video_id = extract_video_id(content)
    if not video_id:
        return None

    # Local transcripts don't have a title: field, use filename stem
    title = os.path.splitext(os.path.basename(filepath))[0]
    # Strip leading date prefix (YYYY-MM-DD-) for a cleaner title
    date_prefix = re.match(r'^\d{4}-\d{2}-\d{2}-', title)
    if date_prefix:
        title = title[date_prefix.end():]
    title = title.replace('-', ' ').title()

    pub_date = ''
    m = DATEOFTALK_PATTERN.search(content)
    if m:
        pub_date = m.group(1)

    transcript_id = ''
    m = TRANSCRIPT_ID_PATTERN.search(content)
    if m:
        transcript_id = m.group(1)

    return {
        'video_id': video_id,
        'title': title,
        'filename': os.path.basename(filepath),
        'pub_date': pub_date,
        'assemblyai_transcript_id': transcript_id,
    }


def main():
    # Track video IDs we've already seen (blog posts take priority)
    seen_video_ids = set()
    rows = []
    skipped_blog = []
    skipped_local = []

    # 1. Scan blog posts
    blog_files = [f for f in os.listdir(BLOG_DIR) if f.endswith('.md')]
    print(f"Found {len(blog_files)} blog post files in {BLOG_DIR}")

    for fname in sorted(blog_files):
        filepath = os.path.join(BLOG_DIR, fname)
        result = extract_from_blog_post(filepath)
        if result:
            rows.append(result)
            seen_video_ids.add(result['video_id'])
        else:
            skipped_blog.append(fname)

    blog_count = len(rows)
    print(f"Extracted {blog_count} entries from blog posts")

    # 2. Scan local transcript files (only add videos not already found in blog posts)
    if os.path.isdir(LOCAL_TRANSCRIPT_DIR):
        local_files = [f for f in os.listdir(LOCAL_TRANSCRIPT_DIR) if f.endswith('.md')]
        print(f"Found {len(local_files)} local transcript files in {LOCAL_TRANSCRIPT_DIR}")

        for fname in sorted(local_files):
            filepath = os.path.join(LOCAL_TRANSCRIPT_DIR, fname)
            result = extract_from_local_transcript(filepath)
            if result:
                if result['video_id'] not in seen_video_ids:
                    rows.append(result)
                    seen_video_ids.add(result['video_id'])
            else:
                skipped_local.append(fname)

        local_count = len(rows) - blog_count
        print(f"Added {local_count} new entries from local transcripts (not already in blog posts)")
    else:
        print(f"Local transcript directory not found: {LOCAL_TRANSCRIPT_DIR}")

    # Write CSV
    fieldnames = ['video_id', 'title', 'filename', 'pub_date', 'assemblyai_transcript_id']
    with open(CSV_PATH, 'w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)

    print(f"\nWrote {len(rows)} total entries to {CSV_PATH}")
    if skipped_blog:
        print(f"Skipped {len(skipped_blog)} blog posts (no video ID found):")
        for s in skipped_blog:
            print(f"  {s}")
    if skipped_local:
        print(f"Skipped {len(skipped_local)} local transcripts (no video ID found):")
        for s in skipped_local:
            print(f"  {s}")

    # Show some stats
    video_ids = [r['video_id'] for r in rows]
    unique_ids = set(video_ids)
    if len(video_ids) != len(unique_ids):
        dupes = [vid for vid in unique_ids if video_ids.count(vid) > 1]
        print(f"\nDuplicate video IDs found ({len(dupes)}):")
        for vid in dupes:
            matching = [r['filename'] for r in rows if r['video_id'] == vid]
            print(f"  {vid}: {matching}")


if __name__ == '__main__':
    main()
