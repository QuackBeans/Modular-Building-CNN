# Information

Current ver: 2.0

This is a Convolutional Neural Network built for identifying different types of modular buildings and cabins based on their images.
I started this project to aid with automating repetitive databasing tasks at my previous job.

Originally i built a more rudimentary version, however this version is built from the ground up to be more efficient and far cleaner.

The images are all sourced from modular building provider's websites, and tagged according to the provider's description.
The images of course take up quite a bit of space, so i've zipped them and uploaded them separately. Just drop them in to the main directory.

## Preprocessing.py

This file is used to extract product data from my company's database, retrieving images of the buildings and their accompanying categories that had been manually added previously. This data is used to build up the training database for the model.

Once it downloads the images, they are immediately converted into numpy format and zipped with the categories, ready to put in to the model.

This file is most likely going to be useless to the majority of people, as it relates directly to the old company database, and draws its content from there. If you wish to retrain the model, you can build and provide your own dataset.

## MB_CNN.py

This is the main module for the network training and testing.
It's a 3-block Convolutional Neural Network architecture that uses binary crossentropy in conjunction with a sigmoid activation for the output, allowing for multi-label classification (not to be confused with multiclass.)

## Final Models

This folder contains the final trained models that can loaded and used.

# Notes

**Remember to manually set last_processed_item_ID.txt back to 0 when the operation is complete**