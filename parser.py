import configparser
import os
import re
import feedparser
import requests
import openai
import time
from datetime import datetime, timedelta
from dateutil.parser import parse as parse_date
from dateutil.tz import tzlocal
from difflib import SequenceMatcher
from html import escape
from http.client import RemoteDisconnected
from pathlib import Path
from sklearn.feature_extraction.text import TfidfVectorizer, ENGLISH_STOP_WORDS
from sklearn.metrics.pairwise import cosine_similarity
import ast

# Constants
CONFIG_FILE_PATH = "settings.conf"

# Read settings from the configuration file
config = configparser.ConfigParser()
config.read(CONFIG_FILE_PATH)

try:
    rss_feed_urls = ast.literal_eval(config.get("General", "rss_feed_urls"))
    threshold = config.getfloat("General", "threshold")
    hours = config.getint("General", "hours")
    output_file = config.get("General", "output_file")
    time_limit_hours = config.getint("General", "time_limit_hours")
    title = config.get("General", "HTML_title") 

except configparser.NoSectionError:
    raise ValueError("Error: The 'General' section is missing in the settings.conf file")

try:
    openai_api_key = config.get("OpenAI", "api_key")
    openai_language = config.get("OpenAI", "language")

except configparser.NoSectionError:
    raise ValueError("Error: The 'OpenAI' section is missing in the settings.conf file")

openai.api_key = openai_api_key


def fetch_rss_feed(feed_url, retries=3, delay=5):
    for attempt in range(retries):
        try:
            feed = feedparser.parse(feed_url)
            feed.entries.reverse() 
            return feed
        except RemoteDisconnected as e:
            if attempt < retries - 1:
                print(f"Error fetching feed from {feed_url}: {e}. Retrying in {delay} seconds...")
                time.sleep(delay)
            else:
                print(f"Could not retrieve feed from {feed_url}")
                class Empty:
                    pass

                empty_object = Empty()
                empty_object.entries = []

                return empty_object


def summarize_content(content):
    prompt = f"Summarize the following content in one sentence, in {openai_language}: {content}"

    response = openai.Completion.create(
        engine="text-davinci-002",
        prompt=prompt,
        max_tokens=60,
        n=1,
        stop=None,
        temperature=0.5,
    )

    text = response.choices[0].text.strip()
    sentences = re.split(r'(?<=[.!?])\s+|\s+(?=[.!?])', text)
    summary_until_period = sentences[0].strip() + '.'
    # sentences = " ".join(sentences)
    return summary_until_period


def deduplicate_stories(stories, threshold=0.7):
    def has_non_stop_words(text):
        words = text.lower().split()
        return any(word not in ENGLISH_STOP_WORDS and word.strip() for word in words)

    filtered_stories = [story for story in stories if has_non_stop_words(story["title"] + " " + story["description"])]

    if not filtered_stories:
        print("Warning: All documents contain only stop words, empty or whitespace. Skipping deduplication.")
        return stories

    vectorizer = TfidfVectorizer()
    tfidf_matrix = vectorizer.fit_transform([story["title"] + " " + story["description"] for story in filtered_stories])
    cosine_matrix = cosine_similarity(tfidf_matrix)

    unique_stories = []
    unique_indices = set()

    for i, story in enumerate(filtered_stories):
        if i not in unique_indices:
            unique_stories.append(story)
            for j in range(i + 1, len(filtered_stories)):
                if cosine_matrix[i, j] > threshold:
                    unique_indices.add(j)

    return unique_stories

def deduplicate_main_ideas(stories, threshold=0.7):
    unique_main_ideas = []
    for story in stories:
        found = False
        for unique_story in unique_main_ideas:
            if compare_main_ideas(story["main_idea"], unique_story["main_idea"], threshold):
                unique_story["count"] += 1
                found = True
                break
        if not found:
            story["count"] = 1
            unique_main_ideas.append(story)

    return unique_main_ideas

def create_html_output(stories, file_name="output.html"):
    html = f"""
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{title}</title>
    <style>
        body {{
            font-family: Arial, sans-serif;
        }}
        h1 {{
            text-align: center;
        }}
        article {{
            margin-bottom: 2rem;
        }}
    </style>
</head>
<body>
    <h1>Threat Intelligence Feed</h1>
"""

    for story in stories:
        html += f"""
    <article>
        <h2>{escape(story["title"])}</h2>
        <p><a href="{escape(story["link"])}">Read the full story</a></p>
        <p>{escape(story["main_idea"])}</p>
    </article>
"""

    html += """
</body>
</html>
"""

    with open(file_name, "w", encoding="utf-8") as file:
        file.write(html)

def compare_main_ideas(main_idea1, main_idea2, threshold=0.7):
    similarity = SequenceMatcher(None, main_idea1, main_idea2).ratio()
    return similarity >= threshold

stories = []
time_limit = datetime.now(tzlocal()) - timedelta(hours=time_limit_hours)

for feed_url in rss_feed_urls:
    try:
        feed = fetch_rss_feed(feed_url)
        for entry in feed.entries:
            if hasattr(entry, "published"):
                published_date = parse_date(entry.published).astimezone(tzlocal())

                if published_date >= time_limit:

                    main_idea = summarize_content(entry.description)

                    stories.append({
                        "title": entry.title,
                        "description": entry.description,
                        "link": entry.link,
                        "published": published_date,
                        "source": feed_url,
                        "main_idea": main_idea,
                    })
            else:
                pass
    except (requests.exceptions.RequestException, ValueError) as e:
        print(f"Error fetching feed from {feed_url}: {e}")

unique_main_ideas = deduplicate_main_ideas(stories)
sorted_unique_main_ideas = sorted(unique_main_ideas, key=lambda x: x["count"], reverse=True)
create_html_output(sorted_unique_main_ideas, file_name=output_file)