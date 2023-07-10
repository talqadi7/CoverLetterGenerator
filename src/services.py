from werkzeug.utils import secure_filename
import logging
import configparser
import os
import requests
from bs4 import BeautifulSoup
import json
import html
from threading import Thread

from pdfdocument.document import PDFDocument

# Get the directory of the current script
script_dir = os.path.dirname(os.path.realpath(__file__))

# Build the path to the secrets file
secrets_file = os.path.join(script_dir, "../secrets.ini")


def get_html_from_url(url):
    response = requests.get(url)
    response.raise_for_status()  # This will raise an exception if there's an error
    return response.text


def scrape_linkedin_job_posting(html_doc):
    soup = BeautifulSoup(html_doc, "html.parser")

    # Extract job title from the 'og:title' meta tag
    og_title = soup.find("meta", property="og:title")["content"]

    # Split the 'og:title' content by ' hiring '
    split_title = og_title.split(" hiring ")

    # The first part is the company name
    company_name = split_title[0]

    # The second part contains the job title and location, split it by ' in '
    job_title_location = split_title[1].split(" in ")

    # The first part is the job title
    job_title = job_title_location[0]

    # Extract job description from the 'JobPosting' schema
    job_posting_schema = soup.find("script", type="application/ld+json")
    job_posting_data = json.loads(job_posting_schema.string)
    job_description_html = job_posting_data["description"]

    # Convert HTML to plain text
    job_description_soup = BeautifulSoup(job_description_html, "html.parser")
    job_description = job_description_soup.get_text(separator="\n")

    # Unescape HTML entities
    job_description = html.unescape(job_description)

    return job_title, company_name, job_description


def update_secrets_in_file(
    openai_api_key=None, google_api_key=None, google_cse_id=None
):
    config = configparser.ConfigParser()
    config.read(secrets_file)

    if openai_api_key:
        config["DEFAULT"]["OPENAI_API_KEY"] = openai_api_key

    if google_api_key:
        config["DEFAULT"]["GOOGLE_API_KEY"] = google_api_key

    if google_cse_id:
        config["DEFAULT"]["GOOGLE_CSE_ID"] = google_cse_id

    with open(secrets_file, "w") as configfile:
        config.write(configfile)


def are_keys_set():
    config = configparser.ConfigParser()
    config.read(secrets_file)
    return all(val for val in config["DEFAULT"].values())


def allowed_file(filename):
    ALLOWED_EXTENSIONS = {"txt", "pdf", "docx"}
    return "." in filename and filename.rsplit(".", 1)[1].lower() in ALLOWED_EXTENSIONS


def save_cover_letter_to_file(cover_letter, company_name):
    txt_filename = f"generated_cover_letters/txt/{company_name}_cover_letter.txt"
    # Save the cover letter as a text file
    with open(txt_filename, "w") as file:
        file.write(cover_letter)


def save_uploaded_file(cover_letter_generator, file, filename_prefix):
    if allowed_file(file.filename):
        _, file_extension = os.path.splitext(file.filename)
        filename = filename_prefix + file_extension
        secure_file_name = secure_filename(filename)
        file_path = os.path.join("Data", secure_file_name)
        logging.info(f"Saving file to: {file_path}")
        file.save(file_path)
        cover_letter_generator.load_documents()


def get_linkedin_job_details(url):
    # Get the HTML content of the LinkedIn job posting page
    html_doc = get_html_from_url(url)

    # Scrape the job posting
    return scrape_linkedin_job_posting(html_doc)


def generate_cover_letter_async(
    cover_letter_generator, company_name, position, job_descript
):
    with cover_letter_generator.lock:
        if cover_letter_generator.is_running:
            return (
                True,
                {"status": "A cover letter generation is already in progress."},
                409,
            )
    logging.info("Generating cover letter.")
    Thread(
        target=cover_letter_generator.query,
        args=(company_name, position, job_descript),
    ).start()
    return False, {"status": "Generating cover letter..."}, 202


def generate_filename(company_name: str, extension: str) -> str:
    company_name = company_name.replace(" ", "_")
    filename = (
        f"generated_cover_letters/{extension}/{company_name}_cover_letter.{extension}"
    )
    return filename


def read_text_file(filename: str) -> str:
    with open(filename, "r") as f:
        text = f.read()
    return text


def create_pdf_from_text(text: str, pdf_filename: str) -> None:
    pdf = PDFDocument(pdf_filename)
    pdf.init_report()
    pdf.generate_style(font_size=11, font_name="Times-Roman")
    pdf.p(text)
    pdf.generate()


def file_exists(filename: str) -> bool:
    return os.path.exists(filename)


def reset_generator(cover_letter_generator):
    cover_letter_generator.reset()
