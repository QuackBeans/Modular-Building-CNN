import tensorflow as tf
from tensorflow.keras.preprocessing.image import ImageDataGenerator
import preprocessing as pre
from matplotlib import pyplot
import time
import re

# Directories for train/val/test dataset
train_dir = 'Dataset/train'
validation_dir = 'Dataset/validation'
test_dir = 'Dataset/test'

# Define image dimensions and batch size
img_width, img_height = 224, 224
batch_size = 32

# Get steps from dividing image totals by batch size. Optional for specifying steps.
train_steps = round(pre.count_images_in_subfolders(r'C:\Programming\Python\Modular_Building_CNN\Dataset\train') / batch_size)
val_steps = round(pre.count_images_in_subfolders(r'C:\Programming\Python\Modular_Building_CNN\Dataset\validation') / batch_size)

print(train_steps, val_steps)

# Utilizing ImageDataGenerator to augment the samples for each epoch, improving model generalisation.
train_datagen = ImageDataGenerator(
    rescale=1./255,  # Rescale pixel values to [0, 1]
    rotation_range=20,  # Rotate images by up to 20 degrees
    width_shift_range=0.2,  # Shift images horizontally
    height_shift_range=0.2,  # Shift images vertically
    shear_range=0.2,  # Shear intensity
    zoom_range=0.2,  # Zoom range
    horizontal_flip=True  # Randomly flip images horizontally
)

validation_datagen = ImageDataGenerator(rescale=1./255)
test_datagen = ImageDataGenerator(rescale=1./255)

# Load and augment images from directories using datagens. Uses flow_from_directory uses the folder names as csategories.
train_generator = train_datagen.flow_from_directory(
    train_dir,
    target_size=(img_width, img_height),
    batch_size=batch_size,
    class_mode='categorical'
)

print(train_generator)

validation_generator = validation_datagen.flow_from_directory(
    validation_dir,
    target_size=(img_width, img_height),
    batch_size=batch_size,
    class_mode='categorical'
)

test_generator = test_datagen.flow_from_directory(
    test_dir,
    target_size=(img_width, img_height),
    batch_size=batch_size,
    class_mode='categorical'
)


# Define the model for multi-label classification
model = tf.keras.models.Sequential([
    tf.keras.layers.Conv2D(32, (3,3), activation='relu', input_shape=(img_width, img_height, 3)),
    tf.keras.layers.MaxPooling2D(2, 2),
    tf.keras.layers.Conv2D(64, (3,3), activation='relu'),
    tf.keras.layers.MaxPooling2D(2,2),
    tf.keras.layers.Conv2D(128, (3,3), activation='relu'),
    tf.keras.layers.MaxPooling2D(2,2),
    tf.keras.layers.Flatten(),
    tf.keras.layers.Dense(512, activation='relu'),
    tf.keras.layers.Dense(15, activation='sigmoid')  # Use sigmoid activation for multi-label
])

# Compile the model with binary cross-entropy loss
model.compile(loss='binary_crossentropy',
              optimizer='adam',
              metrics=['accuracy'])


# Print summary to check weights
model.summary()

# Train the model
history = model.fit(
      train_generator, # The training dataset generated above
      steps_per_epoch=None,
      epochs=15,
      validation_data=validation_generator,
      validation_steps=None,
      verbose=1)


# Save model prompt
while True:
    save_model = input("Do you want to save the model? (yes/no): ")
    if save_model.lower() == 'yes' or save_model.lower() == 'y':
        while True:
            mod_name = input("Enter name for model: ")
            # Check for valid naming conventions and save the model
            if bool(re.match(r'^[\w\-. ]+$', mod_name)):
                model.save(f"final_models/{mod_name}.h5")
                print(f"Model saved as '{mod_name}.h5'.")
                break
            else:
                print("invalid name, please use only letters and numbers.")
        break
    elif save_model.lower() == 'no' or save_model.lower() == 'n':
        print("Model not saved.")
        break

    else:
        print('Invalid input, please enter YES or NO.')

# Plot training data prompt
while True:
    plot_data = input("Do you want to plot the training data? (yes/no): ")
    if plot_data.lower() == 'yes' or plot_data.lower() == 'y':
        # Plot training & validation data for analysis
        pyplot.figure(figsize=(12, 4))

        pyplot.subplot(1, 2, 1)
        pyplot.plot(history.history['accuracy'])
        pyplot.plot(history.history['val_accuracy'])
        pyplot.title('Model accuracy')
        pyplot.ylabel('Accuracy')
        pyplot.xlabel('Epoch')
        pyplot.legend(['Train', 'Validation'], loc='upper left')

        # Plot training & validation loss values
        pyplot.subplot(1, 2, 2)
        pyplot.plot(history.history['loss'])
        pyplot.plot(history.history['val_loss'])
        pyplot.title('Model loss')
        pyplot.ylabel('Loss')
        pyplot.xlabel('Epoch')
        pyplot.legend(['Train', 'Validation'], loc='upper left')

        pyplot.tight_layout()
        pyplot.show()

        print("Operation complete.")
        break
    if plot_data.lower() == 'no' or plot_data.lower() == 'n':
        print("Operation complete.")
        break
    else:
        print('Invalid input, please enter YES or NO.')
