# CrossPooter

## Overview

CrossPooter is designed to poot your toots across different platforms. It reads an RSS feed and posts new entries to GoToSocial and Bluesky.

## Features

- Poot a toot using the linked article's title, URL, and description taken from OpenGraph tags.
- Optionally include media (images/videos) if og:image exists.

## Installation

```bash
python3 -m venv venv
source venv/bin/activate
python3 -m pip install -r requirements.txt
```

## Usage

To use CrossPooter, you need to set up some environment variables:

1. `GTS_TOKEN`, is your access token for GoToSocial.
2. `BSKY_DID` is the DID for your Bluesky account
3. `BSKY_PASSWORD` is an app password for your Bluesky account

And set up the URL for each service you want to reach in the script.

1. `rss_url` is the feed you want to read
2. `gts_url` is the URL for your GoToSocial instance

Then just run the python script, by hand or by cron

```bash
python crosspooter.py
```

## Other notes

The script assumes that you will run this via cron at a faster rate than articles are posted. So it will only post one article per run, and will only keep track of the last article it posted. If articles are posted too quickly, it will miss some.

This was inspired by [EchoFeed](https://echofeed.app) but I wanted to try building one myself.