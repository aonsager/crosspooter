import feedparser
from bs4 import BeautifulSoup
import requests
import os
import logging
from atproto import Client
from atproto import client_utils
from atproto import models

# Fixed variables
rss_url = "https://invisibleparade.com/feed.xml" 
gts_url = "https://gts.invisibleparade.com/api/v1/"
gts_token = os.getenv('GTS_TOKEN')
gts_headers = {'Authorization': f'Bearer {gts_token}'}
bsky = Client()
bsky.login(os.getenv('BSKY_DID'), os.getenv('BSKY_PASSWORD'))

# Configure logging
logging.basicConfig(filename='script.log', level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# Save the article's image to a local folder and return the filename
def save_image(url, filename):
    response = requests.get(url)
    with open("images/" + filename, 'wb') as file:
        file.write(response.content)

# Upload the image to the GTS server and return the media ID
def upload_image_to_gts(filename, image_alt):
    image_path = "images/" + filename
    files = { 'file': (filename, open(image_path, 'rb'), 'multipart/form-data') }
    data = { 'description': image_alt }
    post_response = requests.post(gts_url + "media", headers=gts_headers, files=files, data=data)
    
    # Get the media ID from the response
    media_id = post_response.json()['id']
    return media_id

# Post the message to the GTS server
def post_to_gts(title, url, description, filename, image_alt):
    # First we upload the image if it exists
    if filename:
        media_id = upload_image_to_gts(filename, image_alt)

    # Post the message
    data = {
        "status": title + "\n\n" + url + "\n\n" + description,
        "media_ids[]": [media_id] if filename else [],
        "visibility": "public",
    }
    post_response = requests.post(gts_url + "statuses", headers=gts_headers, data=data)
    if post_response.status_code == 200:
        logging.info("Posted to GTS successfully.")
    else:
        logging.error("Posting to GTS failed: " + post_response.text)

# Post the message to Bluesky
def post_to_bsky(title, url, description, filename, image_alt):
    tb = client_utils.TextBuilder()
    tb.text(title + "\n\n")
    tb.link(url, url)
    tb.text("\n\n" + description)

    if filename:
        thumb = bsky.upload_blob(open("images/" + filename, 'rb'))
    else: 
        thumb = None

    embed = models.AppBskyEmbedExternal.Main(
        external=models.AppBskyEmbedExternal.External(
            title=title,
            description=description,
            uri=url,
            thumb=thumb.blob if thumb else None,
        )
    )
    post = bsky.send_post(tb, embed=embed)

    if post.uri:
        logging.info("Posted to Bluesky successfully")
    else:
        logging.error("Posting to Bluesky failed: " + post.error)

# 
def check_for_new_posts():
    try:
        with open('last_id.txt', 'r') as id_file:
            last_id = id_file.readline().strip()
    except FileNotFoundError:
        last_id = None
    

    # Parse the RSS feed
    rss_feed = feedparser.parse(rss_url)
    # Only do the first post
    post = rss_feed.entries[0]
    logging.info(f"Got latest post: {post.id}")
    if post.id == last_id:
        logging.info(f"Skipping because already seen.")
    else:
        # Make a get request to the post's link
        response = requests.get(post.link)
        # Soupify the response
        soup = BeautifulSoup(response.text, 'html.parser')
    
        # Find the OpenGraph tags and extract its content
        og_properties = {
            'og:description': None,
            'og:title': None,
            'og:url': None,
            'og:image': None,
            'og:image_alt': None,
        }
        
        for prop in og_properties.keys():
            og_tag = soup.find('meta', attrs={'property': prop, 'content': True})
            if og_tag:
                og_properties[prop] = og_tag['content']
        
        description, title, url, image, image_alt = og_properties.values()

        # Save the image locally
        if image:
            filename = image.split('/')[-1]
            save_image(image, filename)
        else:
            filename = None

        logging.info(f"Posting with following information: \nTitle: {title}\nDescription: {description}\nFilename: {filename}\nImage Alt: {image_alt}")
        # Post the content to both GoToSocial and Bluesky        
        post_to_gts(title, url, description, filename, image_alt)
        post_to_bsky(title, url, description, filename, image_alt)

         # Write the latest post's ID to the file
        with open('last_id.txt', 'w') as id_file:
            id_file.write(post.id)
   
def main():
    check_for_new_posts()

if __name__ == '__main__':
    main()
