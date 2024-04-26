import requests
import pandas as pd
import math
import os
import pickle
from monday import MondayClient
import mimetypes
from dotenv import load_dotenv
import numpy as np
import requests
from PIL import Image
from io import BytesIO
from sklearn.preprocessing import LabelEncoder
from sklearn.preprocessing import MultiLabelBinarizer
import pickle
from tqdm import tqdm
import urllib.parse


# GLOBAL ----------------------------------------------------------------------------------------------------

# Load environment variables from .env file
load_dotenv()
apiKey = os.getenv('MONDAY_API_KEY') # Add your key as a string here, or use environment variables .env
apiUrl = 'https://api.monday.com/v2'
headers = {"Authorization" : apiKey,
           "API-Version": '2024-04'}

monday = MondayClient(apiKey)


#---------------

# Function to read the last processed item ID from a .txt file
def read_last_processed_item_id(filename='last_processed_item_id.txt'):
    try:
        with open(filename, 'r') as file:
            last_item_id = int(file.read().strip())
    except FileNotFoundError:
        last_item_id = None
    return last_item_id

# Function to write the last processed item ID to a .txt file
def write_last_processed_item_id(item_id, filename='last_processed_item_id.txt'):
    with open(filename, 'w') as file:
        file.write(str(item_id))

# This query grabs all of the item ID's, tags, and photos, for all items that HAVE photos. This can be used to download the images.


# ... (previous imports and functions)

# Initial query to grab items
initial_query = '''{
  boards (ids: 1450631968) {
    items_page (limit: 500) {
      cursor
      items {
        id
        column_values {
          column {
            title
          }
          text
        }
        assets {
          public_url
        }
      }
    }
  }
}'''

# Make the initial request
response = requests.post(apiUrl, json={'query': initial_query}, headers=headers)
data = response.json()

items = data['data']['boards'][0]['items_page']['items']
cursor = data['data']['boards'][0]['items_page']['cursor']

all_items = items
image_count = 0
zipped_data = []
categories = []  # Initialize categories list

# Read the last processed item ID
last_processed_item_id = read_last_processed_item_id()

categories = []  # Initialize categories list
images_list = []  # Initialize images list

# Loop to fetch all items using pagination with cursor
while cursor:
    query = '''{
  boards(ids: 1450631968) {
    items_page(limit: 500, cursor:"%s") {
      cursor
      items {
        id
        column_values {
          column {
            title
          }
          text
        }
        assets {
          public_url
        }
      }
    }
  }
}''' % cursor
    

    response = requests.post(apiUrl, json={'query': query}, headers=headers)
    data = response.json()

    items = data['data']['boards'][0]['items_page']['items']
    cursor = data['data']['boards'][0]['items_page']['cursor']

    for item in items:
        item_id = item['id']

        # Skip items until the last processed item ID is reached
        if last_processed_item_id and int(item_id) <= int(last_processed_item_id):
            continue

        tags = None
        images = None

        for column in item['column_values']:
            column_title = column['column']['title']
            text = column['text']

            if column_title == 'TAGS':
                tags = text
            elif column_title == 'Images':
                images = text

        if images:
            image_count += 1
            public_urls = [asset['public_url'] for asset in item['assets']]
            zipped_data.append((item_id, tags, public_urls))
            print(f"Item ID: {item_id}, TAGS: {tags}, Images: {public_urls} were added to the zip!")

            # Download, resize, and convert images
            for url in public_urls:
                try:
                    response = requests.get(url)
                    response.raise_for_status()

                    img = Image.open(BytesIO(response.content))
                    print(img)
                    img = img.resize((224, 224))
                    img_array = np.array(img)

                    tags_list = [tag.strip() for tag in tags.split(',')]
                    for tag in tags_list:
                        images_list.append(img_array)
                        categories.append(tag)

                except requests.HTTPError as http_err:
                    print(f"HTTP error occurred: {http_err}")
                    write_last_processed_item_id(item_id)
                    break

                except Exception as e:
                    print(f"Error downloading {url}: {e}")
                    write_last_processed_item_id(item_id)
                    continue

        # Convert categories to binary labels
        label_binarizer = MultiLabelBinarizer()
        categories_encoded = label_binarizer.fit_transform([[cat] for cat in categories])

        # Save zipped_data with pickle
        with open('zipped_data.pkl', 'wb') as f:
            pickle.dump(zipped_data, f)

        # Convert images_list to numpy array
        images_array = np.array(images_list)

        # Save the processed dataset
        np.savez('processed_dataset.npz', images=images_array, categories=categories_encoded, classes=label_binarizer.classes_)

        print(f"Total items with Images: {len(zipped_data)}. Does this match the amount on the database? Check!")
        print("Dataset was created!")