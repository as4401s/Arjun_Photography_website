import os
import re
import urllib.parse

def get_existing_data(html_path):
    with open(html_path, 'r') as f:
        content = f.read()
    
    # Extract all IDs
    ids = [int(m) for m in re.findall(r'id:\s*(\d+)', content)]
    max_id = max(ids) if ids else 0
    
    # Extract all URLs (decoding them to match file system paths for comparison)
    urls = set()
    # Matches url: "..."
    for m in re.findall(r'url:\s*"([^"]+)"', content):
        # Decode %20 to space, etc.
        decoded_url = urllib.parse.unquote(m)
        urls.add(decoded_url)
        
    return max_id, urls

def scan_images(root_dirs):
    found_files = []
    for root_dir in root_dirs:
        for root, dirs, files in os.walk(root_dir):
            for file in files:
                if file.lower().endswith(('.webp', '.jpg', '.jpeg', '.png')):
                    # Get relative path
                    full_path = os.path.join(root, file)
                    # We want path relative to the website root (where index.html is)
                    # Assuming script is run from website root
                    rel_path = os.path.relpath(full_path, '.')
                    found_files.append(rel_path)
    return found_files

def generate_entry(file_path, new_id):
    # Determine metadata
    # Path format examples: 
    # poy/IMG_123.webp -> Country: "", isPoy: true
    # poy/countries/india/IMG_123.webp -> Country: "India", isPoy: false
    
    parts = file_path.split(os.sep)
    
    country = ""
    is_poy = "false"
    
    if parts[0] == 'poy':
        if len(parts) > 1 and parts[1] == 'countries':
            if len(parts) > 2:
                # e.g. poy/countries/india/...
                country_raw = parts[2]
                # Capitalize words (e.g. south korea -> South Korea)
                country = country_raw.title()
        else:
            # Directly in poy/ or poy/something_else (not countries)
            # Based on existing data, direct poy/ images are isPoy: true
            is_poy = "true"
            
    # URL encode the path for the JS string (e.g. spaces to %20)
    # But we want to keep slashes
    url_encoded = urllib.parse.quote(file_path)
    # quote encodes / to %2F, we need to revert that
    url_encoded = url_encoded.replace('%2F', '/')
    
    return f'            {{ id: {new_id}, url: "{url_encoded}", title: "", country: "{country}", isPoy: {is_poy} }},'

def main():
    html_path = 'index.html'
    scan_dirs = ['poy', 'images']
    
    print(f"Scanning existing data from {html_path}...")
    max_id, existing_urls = get_existing_data(html_path)
    print(f"Found {len(existing_urls)} existing images. Max ID: {max_id}")
    
    print(f"Scanning directories: {scan_dirs}...")
    found_files = scan_images(scan_dirs)
    print(f"Found {len(found_files)} files on disk.")
    
    new_entries = []
    current_id = max_id + 1
    
    print("\n--- New Images ---")
    for file_path in found_files:
        # Compare with existing. 
        # existing_urls are decoded (spaces), file_path has spaces.
        # But wait, existing URLs in file might be "poy/countries/south%20korea/..."
        # get_existing_data decodes them to "poy/countries/south korea/..."
        # So we can compare directly.
        
        if file_path not in existing_urls:
            # Double check for safety (sometimes ./ prefix issues)
            if file_path.startswith('./'):
                clean_path = file_path[2:]
            else:
                clean_path = file_path
                
            if clean_path not in existing_urls:
                entry = generate_entry(clean_path, current_id)
                new_entries.append(entry)
                current_id += 1
    
    if new_entries:
        print(f"Found {len(new_entries)} new images.")
        print("Copy the following lines into index.html allPhotos array:")
        print("-" * 20)
        for entry in new_entries:
            print(entry)
        print("-" * 20)
    else:
        print("No new images found.")

if __name__ == "__main__":
    main()
