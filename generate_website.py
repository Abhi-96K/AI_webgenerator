#!/usr/bin/env python3
"""
Python script to generate websites using your AI Website Generator API
"""

import requests
import sys
import os
import zipfile

API_URL = "http://localhost:8000/generator/generate/"

def generate_website(prompt):
    """Generate a website using the AI API"""
    data = {"prompt": prompt}
    
    try:
        response = requests.post(API_URL, data=data)
        response.raise_for_status()
        
        result = response.json()
        print(f"✅ Website generated successfully!")
        print(f"📁 Site ID: {result['site_id']}")
        print(f"📥 Download URL: {result['download_url']}")
        
        return result
        
    except requests.exceptions.RequestException as e:
        print(f"❌ Error generating website: {e}")
        return None

def download_and_extract(site_id, download_url):
    """Download and extract the generated website"""
    # Download the ZIP file
    zip_url = f"http://localhost:8000{download_url}"
    
    try:
        response = requests.get(zip_url)
        response.raise_for_status()
        
        # Save ZIP file
        zip_filename = f"generated_site_{site_id}.zip"
        with open(zip_filename, 'wb') as f:
            f.write(response.content)
        
        # Extract ZIP file
        extract_dir = f"generated_site_{site_id}"
        os.makedirs(extract_dir, exist_ok=True)
        
        with zipfile.ZipFile(zip_filename, 'r') as zip_ref:
            zip_ref.extractall(extract_dir)
        
        print(f"📂 Website extracted to: {extract_dir}/")
        print(f"🌐 Open {extract_dir}/index.html in your browser")
        
        return extract_dir
        
    except Exception as e:
        print(f"❌ Error downloading website: {e}")
        return None

def main():
    if len(sys.argv) < 2:
        print("Usage: python generate_website.py 'Your website prompt here'")
        print("\nExample prompts:")
        print("  'Create a portfolio website for a photographer'")
        print("  'Build a landing page for a coffee shop'")
        print("  'Make a simple blog layout with sidebar'")
        sys.exit(1)
    
    prompt = " ".join(sys.argv[1:])
    print(f"🤖 Generating website with prompt: '{prompt}'")
    
    # Generate website
    result = generate_website(prompt)
    if not result:
        sys.exit(1)
    
    # Download and extract
    extract_dir = download_and_extract(result['site_id'], result['download_url'])
    if extract_dir:
        print(f"\n🎉 Website generation complete!")
        print(f"📁 Files saved in: {extract_dir}/")

if __name__ == "__main__":
    main()