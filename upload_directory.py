import os
import requests
import json
from pathlib import Path
import mimetypes
import time

# API configuration
BASE_URL = "https://na.folderfort.com/api/v1"

def get_api_token():
    """Ask the user for their API token"""
    print("Please provide your FolderFort API token.")
    print("You can find this in your account settings on the FolderFort website.")
    return input("API Token: ").strip()

def create_folder(name, parent_id=None, api_token=None):
    """Create a folder and return its ID"""
    folder_url = f"{BASE_URL}/folders"
    headers = {"Authorization": f"Bearer {api_token}"}
    payload = {
        "name": name,
        "parentId": parent_id
    }

    response = requests.post(folder_url, json=payload, headers=headers)
    if response.status_code != 200:
        print(f"Failed to create folder '{name}': {response.text}")
        return None

    data = response.json()
    return data.get("folder", {}).get("id")

def upload_file(file_path, parent_id=None, api_token=None):
    """Upload a file to the specified parent folder"""
    upload_url = f"{BASE_URL}/uploads"
    headers = {"Authorization": f"Bearer {api_token}"}

    # Determine file MIME type
    mime_type, _ = mimetypes.guess_type(file_path)
    if mime_type is None:
        mime_type = "application/octet-stream"

    try:
        with open(file_path, "rb") as file:
            files = {"file": (os.path.basename(file_path), file, mime_type)}
            data = {"parentId": parent_id}

            response = requests.post(upload_url, headers=headers, data=data, files=files)

            if response.status_code != 201:
                print(f"Failed to upload file '{file_path}': {response.text}")
                return False

            print(f"Successfully uploaded: {file_path}")
            return True
    except Exception as e:
        print(f"Error uploading {file_path}: {str(e)}")
        return False

def upload_directory(directory_path, parent_id=None, api_token=None, exclude_patterns=None):
    """Recursively upload a directory and its contents"""
    if exclude_patterns is None:
        exclude_patterns = ['.git', '__pycache__', '.DS_Store', '.env', 'venv', 'node_modules']

    # Convert to Path object for easier handling
    directory = Path(directory_path)

    # Process all items in the directory
    for item in directory.iterdir():
        # Skip excluded patterns
        if any(pattern in str(item) for pattern in exclude_patterns):
            continue

        # Skip files that are too large (adjust the size limit as needed)
        if item.is_file() and item.stat().st_size > 100 * 1024 * 1024:  # 100 MB
            print(f"Skipping large file: {item} ({item.stat().st_size / (1024 * 1024):.2f} MB)")
            continue

        try:
            if item.is_dir():
                # Create folder
                folder_name = item.name
                folder_id = create_folder(folder_name, parent_id, api_token)
                if folder_id:
                    print(f"Created folder: {folder_name} (ID: {folder_id})")
                    # Recursively upload contents of this folder
                    upload_directory(item, folder_id, api_token, exclude_patterns)
            else:
                # Upload file
                upload_file(item, parent_id, api_token)
                # Add a small delay to avoid overwhelming the API
                time.sleep(0.5)
        except Exception as e:
            print(f"Error processing {item}: {str(e)}")

def main():
    # Get API token from user
    api_token = get_api_token()
    if not api_token:
        print("API token is required. Cannot proceed.")
        return

    # Get current directory
    current_dir = os.getcwd()
    print(f"Uploading current directory: {current_dir}")

    # Ask if user wants to upload to root or create a new folder
    choice = input("Upload to root (r) or create a new folder (f)? ").lower()

    parent_id = None  # Root folder
    if choice == 'f':
        folder_name = input("Enter folder name: ")
        parent_id = create_folder(folder_name, None, api_token)
        if not parent_id:
            print("Failed to create parent folder. Uploading to root instead.")

    # Start uploading
    upload_directory(current_dir, parent_id, api_token)
    print("Directory upload completed.")

if __name__ == "__main__":
    main()