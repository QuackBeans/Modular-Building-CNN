import requests
import pandas as pd
import math
import os
import pickle
from monday import MondayClient
import mimetypes
from dotenv import load_dotenv
import numpy as np
from PIL import Image
import io
from sklearn.preprocessing import LabelEncoder
from sklearn.preprocessing import MultiLabelBinarizer
from tqdm import tqdm
import urllib.parse
import random

# Load environment variables from .env file
load_dotenv()
apiKey = os.getenv('MONDAY_API_KEY') 
apiUrl = 'https://api.monday.com/v2'
headers = {"Authorization" : apiKey,
           "API-Version": '2024-04'}

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
data_list = []  # Initialize list to store image URLs and categories

# Read the last processed item ID
last_processed_item_id = read_last_processed_item_id()

# Create a folder to store images
image_folder = 'images'
if not os.path.exists(image_folder):
    os.makedirs(image_folder)

# Loop to fetch all items using pagination with cursor
while cursor:
    # Define the query for fetching items
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

    # Make the request
    response = requests.post(apiUrl, json={'query': query}, headers=headers)
    data = response.json()

    items = data['data']['boards'][0]['items_page']['items']
    cursor = data['data']['boards'][0]['items_page']['cursor']

    # Iterate through fetched items
    for item in items:
        item_id = item['id']

        # Skip items until the last processed item ID is reached
        if last_processed_item_id and int(item_id) <= int(last_processed_item_id):
            continue

        tags = None
        images = None

        # Extract tags and images from column values
        for column in item['column_values']:
            column_title = column['column']['title']
            text = column['text']

            if column_title == 'TAGS':
                tags = text
            elif column_title == 'Images':
                images = text

        # Process items with images
        if images:
            image_count += 1
            public_urls = [asset['public_url'] for asset in item['assets']]
            for url in public_urls:
                # Download the image and save it locally
                try:
                    response = requests.get(url)
                    response.raise_for_status()

                    # Open the image using the PIL library
                    img = Image.open(io.BytesIO(response.content))
                    
                    # Find the position of the image name using find and rfind, then save it to the folder
                    end_index = str(url).find('.jpg') + 4
                    start_index = str(url).rfind('/', 0, end_index) + 1
                    image_name = str(url)[start_index:end_index]
                    print(image_name)
                    image_filename = os.path.join(image_folder, image_name)
                    if os.path.exists(image_filename):
                        print(f"{image_name} already exists, skipping.")
                    else:
                      img.save(image_filename)
                      print(f"{image_name} was saved.")

                    # Append image file path and corresponding categories to the list
                    data_list.append({'Image': image_filename, 'Categories': tags})

                except requests.HTTPError as http_err:
                    print(f"HTTP error occurred: {http_err}")
                    write_last_processed_item_id(item_id)
                    break

                except Exception as e:
                    print(f"Error downloading {url}: {e}")
                    write_last_processed_item_id(item_id)
                    continue

    # Write the last processed item ID to file
    write_last_processed_item_id(item_id)

# Create a DataFrame from the list
df = pd.DataFrame(data_list)

# Save DataFrame to CSV. Use this CSV to remove particular rows with poor images and clean the data etc.
df.to_csv('images_and_categories.csv', index=False)

print("CSV file saved successfully!")
