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
import shutil

# GLOBAL ---------------------------------------------------------------------------------------------

# Load environment variables from .env file
load_dotenv()
apiKey = os.getenv('MONDAY_API_KEY') 
apiUrl = 'https://api.monday.com/v2'
headers = {"Authorization" : apiKey,
           "API-Version": '2024-04'}

# FUNCTIONS ---------------------------------------------------------------------------------------------

# Read and Write functions to continue the script where it left off if it's interrutped or runs in parts
# Function to read the last processed item ID from a .txt file
def read_last_processed_item_id(filename='last_processed_item_id.txt'):
    try:
        with open(filename, 'r') as file:
            last_item_id = int(file.read().strip())
    except FileNotFoundError:
        last_item_id = None
    except ValueError:
        print("ID is empty, starting fresh run.")
        return 0
    return last_item_id


# Function to write the last processed item ID to a .txt file
def write_last_processed_item_id(item_id, filename='last_processed_item_id.txt'):
    with open(filename, 'w') as file:
        file.write(str(item_id))


# Function to create folders for each category if they don't exist already
def create_category_folders(categories):
    for category in categories:
        folder_path = os.path.join('images', category)
        if not os.path.exists(folder_path):
            os.makedirs(folder_path)


# Function to copy images to their respective category folders
def copy_images_to_category_folders(image_path, categories):
    for category in categories:
        folder_path = os.path.join('images', category)
        image_name = os.path.basename(image_path)
        target_path = os.path.join(folder_path, image_name)
        # Check if the image doesn't already exist in the target folder
        if not os.path.exists(target_path):
            # Copy the image to the target folder
            shutil.copy(image_path, folder_path)

# PROCESSING ---------------------------------------------------------------------------------------------

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

image_count = 0 # Counter for amount of images
data_list = []  # Initialize list to store image URLs and categories from all pages

# Read the last processed item ID
last_processed_item_id = read_last_processed_item_id()

# Create a folder to store images
image_folder = 'images'
if not os.path.exists(image_folder):
    os.makedirs(image_folder)

# Loop to fetch all items. This will run & process for each page, until there is no new cursor pointing to a new page.
while cursor:
    print("Fetching items, please do not abort until one download batch is complete.")

    try:
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
          tags = None
          images = None

          # Skip items until the last processed item ID is reached
          if last_processed_item_id == 0:
              pass
          elif last_processed_item_id != int(item_id):
              print("Finding last processed item ID...")
              continue
          else:
              print("Last item ID was found! Continuing process.")
              # Write the last processed item ID only if it matches
              write_last_processed_item_id(item_id)

          # Now you can proceed with processing the item
          # Extract tags and images from column values
          for column in item['column_values']:
              column_title = column['column']['title']
              text = column['text']

              if column_title == 'TAGS':
                  tags = text.split(', ') if text else []
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
                      image_filename = os.path.join(image_folder, image_name)
                      if os.path.exists(image_filename):
                          print(f"{image_name} already exists, skipping.")
                      else:
                          img.save(image_filename)
                          print(f"{image_name} was saved.")
                          
                          # Create folders for each category
                          create_category_folders(tags)
                          
                          # Copy the image to its respective category folders
                          copy_images_to_category_folders(image_filename, tags)

                  except requests.HTTPError as http_err:
                      print(f"HTTP error occurred: {http_err}")
                      write_last_processed_item_id(item_id)
                      break

                  except Exception as e:
                      print(f"Error downloading {url}: {e}")
                      write_last_processed_item_id(item_id)
                      continue
                  
   # Handle errors for cursor loop. If the link expires, continue the loop to regenerate URL's and continue on from last ID.            
    except Exception as e:
        # Handle other exceptions
        print(f"An error occurred: {e}")

        # Check if the error is AccessDenied on the HTML page
        if '<Code>AccessDenied</Code>' in str(e):
            print("Access Denied. Continuing to next batch.")
            continue  # Continue loop from the beginning
    

    # Write the last processed item ID to file
    write_last_processed_item_id(item_id)
    # Check how many images have been processed so far
    print(f"\nBatch complete. {image_count} have been processed so far.\n")


print("Operation Complete")
# write_last_processed_item_id(0)

