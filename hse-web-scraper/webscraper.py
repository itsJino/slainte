import os
import requests
from bs4 import BeautifulSoup
import pdfkit

# Set the base URL for HSE
base_url = "https://www2.hse.ie"

# Load the HTML file
with open("Health A to Z - HSE.ie.html", "r", encoding="utf-8") as file:
    soup = BeautifulSoup(file, "html.parser")

# Extract all links to condition pages
condition_links = []
for link in soup.find_all("a", class_="hse-list-panel__link"):
    href = link.get("href")
    if href and href.startswith("/conditions/"):
        condition_links.append(base_url + href)

# Create a directory to save the PDFs
output_dir = "HSE_Condition_Pages"
os.makedirs(output_dir, exist_ok=True)

# Iterate through each link, fetch the page, and save as PDF
for link in condition_links:
    try:
        response = requests.get(link)
        if response.status_code == 200:
            # Extract the condition name from the URL
            condition_name = link.split("/")[-2].replace("-", " ").capitalize()
            output_file = os.path.join(output_dir, f"{condition_name}.pdf")
            
            # Convert HTML to PDF and save
            pdfkit.from_string(response.text, output_file)
            print(f"Saved: {output_file}")
        else:
            print(f"Failed to fetch {link}, status code: {response.status_code}")
    except Exception as e:
        print(f"Error processing {link}: {e}")

