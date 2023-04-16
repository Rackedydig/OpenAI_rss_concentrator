# OpenAI_rss_concentrator
This Python script aggregates and deduplicates threat intelligence news from various RSS feeds. It uses the OpenAI GPT API to extract the main ideas from each article, compares them to identify similar stories, and generates an HTML output with the most relevant and unique stories. The script is easy to configure and maintain, allowing you to customize the list of RSS feeds and other settings through a configuration file.
Features

    Fetches news from multiple threat intelligence RSS feeds
    Deduplicates stories based on main ideas extracted using OpenAI GPT
    Sorts stories based on priority (number of occurrences across feeds)
    Generates an HTML output with story titles, links, and main ideas

Dependencies

    Python 3.6+
    feedparser
    python-dateutil
    requests
    openai
    scikit-learn

You can install the required packages using the following command:

bash

pip install feedparser python-dateutil requests openai scikit-learn

Configuration

The script uses a configuration file named settings.conf to store settings such as the OpenAI API key, the list of RSS feeds, and other adjustable thresholds.

Here's a sample settings.conf file:

css

[OpenAI]
api_key=your_openai_api_key_here

[General]
rss_feed_urls=['https://threatpost.com/feed/', 'https://krebsonsecurity.com/feed/', 'https://www.darkreading.com/rss_simple.asp']
threshold=0.7
hours=72
time_limit_hours=72

Replace your_openai_api_key_here with your actual OpenAI API key.
Usage

To run the script, simply execute the following command:

bash

python threat_intelligence_feed.py

The script will generate an HTML output file named output.html containing the deduplicated and prioritized threat intelligence news.
Customization

You can easily customize the script by modifying the settings in the settings.conf file:

    rss_feed_urls: A Python list of RSS feed URLs to fetch news from
    threshold: The similarity threshold to use for deduplication (0.0-1.0, higher values mean higher similarity)
    hours: The number of hours to consider for fetching the latest news
    time_limit_hours: The time limit in hours to consider for fetching the latest news (e.g., 72 hours)
