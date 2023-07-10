from werkzeug.utils import secure_filename
import logging
import configparser
import os
import requests
from bs4 import BeautifulSoup
import json
import html

def get_html_from_url(url):
    response = requests.get(url)
    response.raise_for_status()  # This will raise an exception if there's an error
    return response.text

def scrape_linkedin_job_posting(html_doc):
    soup = BeautifulSoup(html_doc, 'html.parser')

    # Extract job title from the 'og:title' meta tag
    og_title = soup.find('meta', property='og:title')['content']

    # Split the 'og:title' content by ' hiring '
    split_title = og_title.split(' hiring ')

    # The first part is the company name
    company_name = split_title[0]

    # The second part contains the job title and location, split it by ' in '
    job_title_location = split_title[1].split(' in ')

    # The first part is the job title
    job_title = job_title_location[0]

    # Extract job description from the 'JobPosting' schema
    job_posting_schema = soup.find('script', type='application/ld+json')
    job_posting_data = json.loads(job_posting_schema.string)
    job_description_html = job_posting_data['description']

    # Convert HTML to plain text
    job_description_soup = BeautifulSoup(job_description_html, 'html.parser')
    job_description = job_description_soup.get_text(separator='\n')

    # Unescape HTML entities
    job_description = html.unescape(job_description)

    return job_title, company_name, job_description


def update_secrets_in_file(
    openai_api_key=None, google_api_key=None, google_cse_id=None
):
    config = configparser.ConfigParser()
    config.read("../secrets.ini")

    if openai_api_key:
        config["DEFAULT"]["OPENAI_API_KEY"] = openai_api_key

    if google_api_key:
        config["DEFAULT"]["GOOGLE_API_KEY"] = google_api_key

    if google_cse_id:
        config["DEFAULT"]["GOOGLE_CSE_ID"] = google_cse_id

    with open("secrets.ini", "w") as configfile:
        config.write(configfile)


def are_keys_set():
    secrets_file = "secrets.ini"
    config = configparser.ConfigParser()
    config.read(secrets_file)
    return all(val for val in config["DEFAULT"].values())


def allowed_file(filename):

    ALLOWED_EXTENSIONS = {"txt", "pdf", "docx"}
    return "." in filename and filename.rsplit(".", 1)[1].lower() in ALLOWED_EXTENSIONS


def save_cover_letter_to_file(cover_letter, company_name):
    txt_filename = f"generated_cover_letters/txt/{company_name}_cover_letter.txt"
    # Save the cover letter as a text file
    with open(txt_filename, 'w') as file:
        file.write(cover_letter)