from flask import (
    Flask,
    render_template,
    request,
    redirect,
    url_for,
    Response,
    stream_with_context,
    jsonify,
)
import os
from werkzeug.utils import secure_filename
import logging
import configparser
from threading import Thread

from main import CoverLetterGenerator

logging.basicConfig(level=logging.INFO)
app = Flask(__name__)

secrets_file = "secrets.ini"

# Check if the secrets file exists when the application starts. If not, create one
if not os.path.exists(secrets_file):
    config = configparser.ConfigParser()
    config["DEFAULT"] = {
        "OPENAI_API_KEY": "",
        "GOOGLE_SEARCH_KEY": "",
        "GOOGLE_CSE_ID": "",
        "GOOGLE_API_KEY": "",
    }
    with open(secrets_file, "w") as configfile:
        config.write(configfile)

cover_letter_generator = CoverLetterGenerator()  # initialize the cover letter generator


@app.route("/")
def index():
    return redirect(url_for("set_keys"))


@app.route("/job_details_page", methods=["GET"])
def job_details_page():
    # handler logic here
    return render_template("job_details_page.html")


# def get_job_details(url):
#     logging.info("Getting job details from: ", url)
#     response = requests.get(url)
#     soup = BeautifulSoup(response.text, 'html.parser')
#     logging.info('response.text: ', response.text)
#     logging.info('soup: ', soup)
#     position = soup.find('h1', {'class': 't-24 t-bold jobs-unified-top-card__job-title'}).text
#     company = soup.find('a', {'class': 'ember-view t-black t-normal'}).text
#     job_description = soup.find('div', class_='jobs-description-content__text').text

#     return company, position, job_description

# @app.route('/fetch_linkedin_data', methods=['POST'])
# def fetch_linkedin_data():
#     url = request.form.get('url')
#     company, position, description = get_job_details(url)
#     return jsonify({'company': company, 'position': position, 'description': description})


@app.route("/generate_cover_letter", methods=["POST"])
def generate_cover_letter():
    company_name = request.form.get("company_name")
    position = request.form.get("position")
    job_descript = request.form.get("job_descript")

    # Call your main function here, passing the company_name, position, and job_descript as arguments.
    Thread(
        target=cover_letter_generator.query, args=(company_name, position, job_descript)
    ).start()

    return {"status": "Generating cover letter..."}, 202
    # cover_letter = cover_letter_generator.query(company_name, position, job_descript)
    # save_cover_letter_to_file(cover_letter)
    # return {"cover_letter": cover_letter}


@app.route("/generate_cover_letter_final", methods=["GET"])
def get_query_final():
    final_response = cover_letter_generator.query_final()

    return jsonify({"cover_letter": final_response})


@app.route("/generate_cover_letter", methods=["GET"])
def stream_generate_cover_letter():
    def generate():
        for message in cover_letter_generator.get_streamed_messages():
            yield f"data: {message}\n\n"

    return Response(stream_with_context(generate()), mimetype="text/event-stream")


def update_secrets_in_file(
    openai_api_key=None, google_api_key=None, google_cse_id=None
):
    config = configparser.ConfigParser()
    config.read("secrets.ini")

    if openai_api_key:
        config["DEFAULT"]["OPENAI_API_KEY"] = openai_api_key

    if google_api_key:
        config["DEFAULT"]["GOOGLE_API_KEY"] = google_api_key

    if google_cse_id:
        config["DEFAULT"]["GOOGLE_CSE_ID"] = google_cse_id

    with open("secrets.ini", "w") as configfile:
        config.write(configfile)


def are_keys_set():
    config = configparser.ConfigParser()
    config.read(secrets_file)
    return all(val for val in config["DEFAULT"].values())


@app.route("/set_keys", methods=["GET", "POST"])
def set_keys():
    # Location of the secrets file

    # If the secrets file already exists and the keys are set, redirect to upload page
    if are_keys_set():
        return redirect(url_for("upload_page"))

    if request.method == "POST":
        new_openai_api_key = request.form.get("openai_api_key")
        new_google_api_key = request.form.get("google_api_key")
        new_google_cse_id = request.form.get("google_cse_id")

        # Call the function to update the keys in the secrets.ini file
        update_secrets_in_file(
            openai_api_key=new_openai_api_key,
            google_api_key=new_google_api_key,
            google_cse_id=new_google_cse_id,
        )

        return redirect(url_for("upload_page"))
    else:
        return render_template("set_keys.html")


ALLOWED_EXTENSIONS = {"txt", "pdf", "docx"}


def allowed_file(filename):
    return "." in filename and filename.rsplit(".", 1)[1].lower() in ALLOWED_EXTENSIONS


@app.route("/upload_page", methods=["GET"])
def upload_page():
    logging.info("IN PAGE.")
    return render_template("upload_files.html")


@app.route("/upload_resume", methods=["POST"])
def upload_resume():
    logging.info("In upload_resume!")
    if "file" in request.files:
        resume_file = request.files["file"]
        if allowed_file(resume_file.filename):
            _, file_extension = os.path.splitext(
                resume_file.filename
            )  # Get file extension
            filename = "resume" + file_extension  # Create new filename
            resume_file_name = secure_filename(filename)
            file_path = os.path.join("Data", resume_file_name)
            logging.info(f"Saving file to: {file_path}")
            resume_file.save(file_path)
            cover_letter_generator.load_documents()

    return "", 200


@app.route("/upload_cover_letter", methods=["POST"])
def upload_cover_letter():
    logging.info("In upload_cover_letter!")
    if "file" in request.files:
        cover_letter_file = request.files["file"]
        if allowed_file(cover_letter_file.filename):
            _, file_extension = os.path.splitext(
                cover_letter_file.filename
            )  # Get file extension
            filename = "cover_letter" + file_extension  # Create new filename
            cover_file_name = secure_filename(filename)
            file_path = os.path.join("Data", cover_file_name)
            logging.info(f"Saving file to: {file_path}")
            cover_letter_file.save(file_path)
            cover_letter_generator.load_documents()
    return "", 200


@app.route("/upload_other", methods=["POST"])
def upload_other():
    logging.info("In upload_other!")
    if "file" in request.files:
        other_file = request.files["file"]
        if allowed_file(other_file.filename):
            _, file_extension = os.path.splitext(
                other_file.filename
            )  # Get file extension
            filename = "other" + file_extension  # Create new filename
            other_file_name = secure_filename(filename)
            file_path = os.path.join("Data", other_file_name)
            logging.info(f"Saving file to: {file_path}")
            other_file.save(file_path)
            cover_letter_generator.load_documents()
    return "", 200


def save_cover_letter_to_file(cover_letter):
    file_path = "generated_cover_letters.txt"

    with open(file_path, "a") as f:
        f.write("==== New Cover Letter ====\n\n")
        f.write(cover_letter)
        f.write("\n\n")


if __name__ == "__main__":
    app.run(debug=True)
