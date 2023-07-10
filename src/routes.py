from flask import (
    render_template,
    request,
    redirect,
    url_for,
    Response,
    stream_with_context,
    jsonify,
    send_file,
)
from src.services import *
from pdfdocument.document import PDFDocument
import os

logging.basicConfig(level=logging.INFO)


def register_routes(app, cover_letter_generator):
    @app.route("/")
    def index():
        return redirect(url_for("set_keys"))

    @app.route("/job_details_page", methods=["GET"])
    def job_details_page():
        return render_template("job_details_page.html")

    @app.route("/scrape_linkedin", methods=["POST"])
    def scrape_linkedin():
        linkedin_url = request.form.get("linkedin_url")
        job_title, company_name, job_description = get_linkedin_job_details(
            linkedin_url
        )

        # Return the scraped data as a JSON response
        return {
            "job_title": job_title,
            "company_name": company_name,
            "job_description": job_description,
        }

    @app.route("/generate_cover_letter", methods=["POST"])
    def generate_cover_letter():
        company_name = request.form.get("company_name")
        position = request.form.get("position")
        job_descript = request.form.get("job_descript")
        is_running, response, status_code = generate_cover_letter_async(
            cover_letter_generator, company_name, position, job_descript
        )
        if is_running:
            return response, status_code
        else:
            return response, status_code

    @app.route("/get_final_cover_letter", methods=["GET"])
    def get_final_cover_letter():
        with cover_letter_generator.lock:
            if cover_letter_generator.is_running:
                return {"status": "A cover letter generation is in progress."}, 409
        cover_letter_final = cover_letter_generator.query_final()
        save_cover_letter_to_file(
            cover_letter_final, cover_letter_generator.company_name
        )

        return jsonify({"cover_letter": cover_letter_final})

    @app.route("/generate_cover_letter", methods=["GET"])
    def stream_generate_cover_letter():
        # cover_letter_generator.reset()
        def generate():
            for message in cover_letter_generator.get_streamed_messages():
                yield f"data: {message}\n\n"

        return Response(stream_with_context(generate()), mimetype="text/event-stream")

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

    @app.route("/upload_page", methods=["GET"])
    def upload_page():
        logging.info("IN PAGE.")
        return render_template("upload_files.html")

    @app.route("/upload_resume", methods=["POST"])
    def upload_resume():
        logging.info("In upload_resume!")
        if "file" in request.files:
            save_uploaded_file(cover_letter_generator, request.files["file"], "resume")
            return "", 200

    @app.route("/upload_cover_letter", methods=["POST"])
    def upload_cover_letter():
        logging.info("In upload_cover_letter!")
        if "file" in request.files:
            save_uploaded_file(
                cover_letter_generator, request.files["file"], "cover_letter"
            )
            return "", 200

    @app.route("/upload_other", methods=["POST"])
    def upload_other():
        logging.info("In upload_other!")
        if "file" in request.files:
            save_uploaded_file(cover_letter_generator, request.files["file"], "other")
            return "", 200

    @app.route("/download", methods=["GET"])
    def download():
        txt_filename = generate_filename(cover_letter_generator.company_name, "txt")
        pdf_filename = generate_filename(cover_letter_generator.company_name, "pdf")

        # Check if the text file exists
        if not file_exists(txt_filename):
            return "Error: text file not found"

        # Read the text from the text file
        text = read_text_file(txt_filename)

        # Create a PDF from the text
        create_pdf_from_text(text, pdf_filename)

        # Check if the PDF was created successfully
        if not file_exists(pdf_filename):
            return "Error: could not create PDF"

        # re-initialize the cover letter generator
        reset_generator(cover_letter_generator)

        # Send the PDF file to the user
        return send_file(pdf_filename, as_attachment=True)
