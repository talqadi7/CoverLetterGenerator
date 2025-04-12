from werkzeug.utils import secure_filename
import logging
import configparser
import os
import requests
from bs4 import BeautifulSoup
import json
import html
from threading import Thread
import openai
import re

from pdfdocument.document import PDFDocument

# Get the directory of the current script
script_dir = os.path.dirname(os.path.realpath(__file__))

# Build the path to the secrets file
secrets_file = os.path.join(script_dir, "../secrets.ini")


def get_html_from_url(url):
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/96.0.4664.110 Safari/537.36'
    }
    response = requests.get(url, headers=headers)
    response.raise_for_status()  # This will raise an exception if there's an error
    return response.text


def scrape_linkedin_job_posting(html_doc):
    soup = BeautifulSoup(html_doc, "html.parser")

    # Initialize variables with default values
    company_name = "Company"
    job_title = "Position"
    job_description = "No job description found"

    try:
        # Try to get the job title and company name from the page title
        page_title = soup.find("title").text.strip()
        logging.info(f"Page title: {page_title}")

        # Extract job title from the 'og:title' meta tag if it exists
        og_title_tag = soup.find("meta", property="og:title")
        if og_title_tag and "content" in og_title_tag.attrs:
            og_title = og_title_tag["content"]
            logging.info(f"Found og:title: {og_title}")

            # Try different patterns to extract information
            if " hiring " in og_title:
                split_title = og_title.split(" hiring ")
                company_name = split_title[0].strip()

                if len(split_title) > 1:
                    rest = split_title[1]
                    # Check if it contains " in " to extract job title
                    if " in " in rest:
                        job_title = rest.split(" in ")[0].strip()
                    else:
                        job_title = rest.strip()
            else:
                # Alternative method: Try to extract from page title
                # Common format: Job Title | Company | LinkedIn
                parts = page_title.split("|")
                if len(parts) >= 2:
                    job_title = parts[0].strip()
                    company_name = parts[1].strip()

        # Extract job description - first try to find the specific job-details div (as in the example)
        job_details_div = soup.find("div", id="job-details")
        if job_details_div:
            logging.info("Found job-details div")
            job_description = job_details_div.get_text(separator="\n").strip()
        else:
            # If not found, try the JSON-LD schema
            job_posting_schema = soup.find("script", type="application/ld+json")

            if job_posting_schema:
                try:
                    job_posting_data = json.loads(job_posting_schema.string)
                    if "description" in job_posting_data:
                        job_description_html = job_posting_data["description"]

                        # Convert HTML to plain text
                        job_description_soup = BeautifulSoup(job_description_html, "html.parser")
                        job_description = job_description_soup.get_text(separator="\n")

                        # Unescape HTML entities
                        job_description = html.unescape(job_description)

                        # If title not found earlier, try getting it from the schema
                        if job_title == "Position" and "title" in job_posting_data:
                            job_title = job_posting_data["title"]

                        # If company name not found earlier, try getting it from the schema
                        if company_name == "Company" and "hiringOrganization" in job_posting_data:
                            if isinstance(job_posting_data["hiringOrganization"], dict):
                                company_name = job_posting_data["hiringOrganization"].get("name", company_name)
                except json.JSONDecodeError:
                    logging.error("Failed to parse JSON schema data")

            # If we still don't have a description, try to find any job description content
            if job_description == "No job description found":
                # Try common class names for job descriptions
                job_desc_candidates = [
                    soup.find("div", class_=lambda c: c and "jobs-description-content" in c),
                    soup.find("div", class_=lambda c: c and "job-description" in c),
                    soup.find("section", class_=lambda c: c and "description" in c),
                    # Add more potential selectors here
                ]

                for candidate in job_desc_candidates:
                    if candidate:
                        job_description = candidate.get_text(separator="\n").strip()
                        break

    except Exception as e:
        logging.error(f"Error scraping LinkedIn job posting: {e}")

    # Clean up extracted text
    job_description = re.sub(r'\n+', '\n', job_description)  # Remove excessive newlines
    job_description = re.sub(r'\s+', ' ', job_description)   # Normalize whitespace within lines

    logging.info(f"Extracted job title: {job_title}")
    logging.info(f"Extracted company name: {company_name}")
    logging.info(f"Extracted job description length: {len(job_description)}")

    return job_title, company_name, job_description


def update_secrets_in_file(
    openai_api_key=None, google_api_key=None, google_cse_id=None
):
    config = configparser.ConfigParser()
    config.read(secrets_file)

    if openai_api_key:
        config["DEFAULT"]["OPENAI_API_KEY"] = openai_api_key
        # Update the current session as well

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


def sanitize_filename(filename):
    """
    Sanitize a filename by removing invalid characters and replacing spaces with underscores.
    """
    # Remove any characters that aren't alphanumeric, dash, underscore, or space
    sanitized = re.sub(r'[^\w\-\s]', '', filename)
    # Replace spaces with underscores
    sanitized = sanitized.replace(' ', '_')
    # Ensure the filename isn't too long
    if len(sanitized) > 100:
        sanitized = sanitized[:100]
    return sanitized


def save_cover_letter_to_file(cover_letter, company_name):
    """
    Save the cover letter to a text file.
    """
    # Sanitize the company name to create a valid filename
    sanitized_company_name = sanitize_filename(company_name)
    logging.info(f"Sanitized company name: {sanitized_company_name}")
    
    # Make sure the directory exists
    os.makedirs("generated_cover_letters/txt", exist_ok=True)

    txt_filename = f"generated_cover_letters/txt/{sanitized_company_name}_cover_letter.txt"
    logging.info(f"Saving cover letter to {txt_filename}")
    
    # Save the cover letter as a text file
    with open(txt_filename, "w") as file:
        file.write(cover_letter)
    
    return txt_filename


def save_uploaded_file(cover_letter_generator, file, filename_prefix):
    if allowed_file(file.filename):
        _, file_extension = os.path.splitext(file.filename)
        filename = filename_prefix + file_extension
        secure_file_name = secure_filename(filename)
        # Make sure the directory exists
        os.makedirs("Data", exist_ok=True)
        file_path = os.path.join("Data", secure_file_name)
        logging.info(f"Saving file to: {file_path}")
        file.save(file_path)
        cover_letter_generator.load_documents()


def get_linkedin_job_details(url):
    try:
        # Get the HTML content of the LinkedIn job posting page
        html_doc = get_html_from_url(url)

        # Scrape the job posting
        return scrape_linkedin_job_posting(html_doc)
    except Exception as e:
        logging.error(f"Error fetching LinkedIn job details: {e}")
        return "Position", "Company", "Unable to retrieve job description. Please enter the details manually."


def generate_cover_letter_async(
    cover_letter_generator, company_name, position, job_descript,
    user_name="", user_address="", user_email=""
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
        args=(company_name, position, job_descript, user_name, user_address, user_email),
    ).start()
    return False, {"status": "Generating cover letter..."}, 202


def generate_filename(company_name: str, extension: str) -> str:
    """
    Generate a filename for a cover letter with the given company name and extension.
    """
    # Sanitize company name for filename
    sanitized_company_name = sanitize_filename(company_name)
    
    # Make sure the directory exists
    os.makedirs(f"generated_cover_letters/{extension}", exist_ok=True)

    filename = (
        f"generated_cover_letters/{extension}/{sanitized_company_name}_cover_letter.{extension}"
    )
    return filename


def read_text_file(filename: str) -> str:
    """
    Read the contents of a text file.
    """
    logging.info(f"Attempting to read file: {filename}")
    if not os.path.exists(filename):
        logging.error(f"File does not exist: {filename}")
        raise FileNotFoundError(f"File not found: {filename}")
        
    with open(filename, "r") as f:
        text = f.read()
    return text


def create_pdf_from_text(text: str, pdf_filename: str) -> None:
    """
    Create a PDF file from the given text.
    """
    try:
        pdf = PDFDocument(pdf_filename)
        pdf.init_report()
        pdf.generate_style(font_size=11, font_name="Times-Roman")
        pdf.p(text)
        pdf.generate()
        logging.info(f"Successfully created PDF at {pdf_filename}")
    except Exception as e:
        logging.error(f"Error creating PDF: {e}")
        raise


def file_exists(filename: str) -> bool:
    """
    Check if a file exists.
    """
    exists = os.path.exists(filename)
    logging.info(f"Checking if file exists: {filename} - {exists}")
    return exists


def reset_generator(cover_letter_generator):
    """
    Reset the cover letter generator.
    """
    cover_letter_generator.reset()