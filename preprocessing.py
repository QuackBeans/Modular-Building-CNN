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





# GLOBAL ----------------------------------------------------------------------------------------------------

# Load environment variables from .env file
load_dotenv()
apiKey = os.getenv('MONDAY_API_KEY')
apiUrl = 'https://api.monday.com/v2'
headers = {"Authorization" : apiKey,
           "API-Version": '2024-04'}

monday = MondayClient(apiKey)



#---------------

# This query grabs all of the item ID's, tags, and photos, for all items that HAVE photos. This can be used to download the images.


initial_query =  '''{
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
}
'''


# Make the initial request to get the initial set of items
response = requests.post(apiUrl, json={'query': initial_query}, headers=headers)
data = response.json()

# Extract items and cursor
items = data['data']['boards'][0]['items_page']['items']

cursor =  data['data']['boards'][0]['items_page']['cursor']
# List to store all items
all_items = items

# Counter for items with non-empty "Images" column
image_count = 0

# Create a zip for the final elements
zipped_data = []

# Loop to fetch all items using pagination with cursor
while cursor:
    # Update the query with the cursor value
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

    # Make the request for the next set of items
    response = requests.post(apiUrl, json={'query': query}, headers=headers)
    data = response.json()
    
    # Update items and cursor
    items = data['data']['boards'][0]['items_page']['items']
    cursor =  data['data']['boards'][0]['items_page']['cursor']
    
    # Add items to all_items list
    all_items.extend(items)

# Extract TAGS and Images values for items where 'Images' column is not empty
for item in all_items:
    item_id = item['id']
    
    tags = None
    images = None
    
    for column in item['column_values']:
        column_title = column['column']['title']
        text = column['text']
        
        if column_title == 'TAGS':
            tags = text
        elif column_title == 'Images':
            images = text
    
    # Take public URLS of the images and add to a list. Also count the amount of items.
    if images:
        image_count += 1
        
        # Extract public_urls from the item
        public_urls = [asset['public_url'] for asset in item['assets']]
        
        zipped_data.append((item_id, tags, public_urls))

        print(f"Item ID: {item_id}, TAGS: {tags}, Images: {public_urls} were added to the zip!")

# save it with pickle as a backup
with open('zipped_data.pkl', 'wb') as f:
    pickle.dump(zipped_data, f)


# Print the total count of items with non-empty 'Images' column
print(f"Total items with Images: {len(zipped_data)}. Does this match the amount on the database? Check!")
#---------------


# Download images and build dataset

# Function to download, resize, and convert images to numpy arrays to build the database
def download_and_convert_images(zipped_data, target_size=(224, 224)):
    images = []
    categories = []
    
    # Calculate total number of images for tqdm progress bar
    total_images = sum(len(urls) for _, _, urls in zipped_data)
    
    with tqdm(total=total_images, desc="Processing images", unit="image") as pbar:
        for item_id, tags, public_urls in zipped_data:
            for url in public_urls:
                try:
                    
                    # Download the image
                    response = requests.get(url)
                    img = Image.open(BytesIO(response.content))
                    
                    # Resize image
                    img = img.resize(target_size)
                    
                    # Convert image to numpy array
                    img_array = np.array(img)
                    
                    # Split tags by comma and strip whitespace
                    tags_list = [tag.strip() for tag in tags.split(',')]
                    
                    # Add image and categories to lists
                    for tag in tags_list:
                        images.append(img_array)
                        categories.append(tag)
                    
                    # Update progress bar
                    pbar.update(1)
                    
                except Exception as e:
                    print(f"Error downloading {url}: {e}")
                    pbar.update(1)  # Still update progress bar for failed downloads
    
    # Convert categories to binary labels
    label_binarizer = MultiLabelBinarizer()
    categories_encoded = label_binarizer.fit_transform([[cat] for cat in categories])
    
    return np.array(images), categories_encoded, label_binarizer.classes_

# Load zipped_data from pickle
with open('zipped_data.pkl', 'rb') as f:
    zipped_data = pickle.load(f)

# Download, resize, and convert images
images, categories_encoded, classes = download_and_convert_images(zipped_data)

# Save the processed dataset
np.savez('processed_dataset.npz', images=images, categories=categories_encoded, classes=classes)
print("Dataset was created!")


# FIX IMAGE NOT DOWNLOADING