from PIL import Image
import os

def convert_tif_to_jpg(tif_path, jpg_path):
    # Open the TIF file
    with Image.open(tif_path) as image:
        # Convert to RGB format
        rgb_image = image.convert('RGB')
        # Save as JPG
        rgb_image.save(jpg_path)

# Example usage
tif_folder = 'sar_dataset/test_images'
jpg_folder = 'sar_dataset/jpg_images'
if not os.path.exists(jpg_folder):
    os.makedirs(jpg_folder)

for file_name in os.listdir(tif_folder):
    if file_name.endswith('.tif'):
        # Get the paths to the TIF and JPG files
        tif_path = os.path.join(tif_folder, file_name)
        jpg_path = os.path.join(jpg_folder, file_name.replace('.tif', '.jpg'))
        # Convert TIF to JPG
        convert_tif_to_jpg(tif_path, jpg_path)
