import os
import shutil

# Define the file extensions for different categories
file_types = {
    'Videos': ['.mp4', '.mkv', '.flv', '.avi', '.mov'],
    'Photos': ['.jpg', '.jpeg', '.png', '.cr2', '.gif', '.bmp', '.tiff'],
    'Music': ['.mp3', '.wav', '.aac', '.flac', '.ogg'],
    'Documents': ['.pdf', '.doc', '.docx', '.xls', '.xlsx', '.ppt', '.pptx', '.txt']
}

# Function to organize files
def organize_files(directory):
    # Create a folder for each file type if it doesn't exist
    for folder in file_types.keys():
        folder_path = os.path.join(directory, folder)
        if not os.path.exists(folder_path):
            os.makedirs(folder_path)
    
    # Iterate over the files in the directory
    for filename in os.listdir(directory):
        file_path = os.path.join(directory, filename)
        # Skip directories
        if os.path.isdir(file_path):
            continue

        # Determine the file's type and move it to the corresponding folder
        for folder, extensions in file_types.items():
            if any(filename.lower().endswith(ext) for ext in extensions):
                shutil.move(file_path, os.path.join(directory, folder, filename))
                break

# Get the directory where the script is located
current_directory = os.path.dirname(os.path.abspath(__file__))

# Organize files in the current directory
organize_files(current_directory)
