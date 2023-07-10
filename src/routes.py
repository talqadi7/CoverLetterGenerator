from flask import (
    render_template,
    request,
    redirect,
    url_for,
    Response,
    stream_with_context,
    jsonify,
    send_file
)
from threading import Thread
from src.services import *


def register_routes(app, cover_letter_generator):
    @app.route("/")
    def index():
        return redirect(url_for("set_keys"))
    
    
    @app.route("/job_details_page", methods=["GET"])
    def job_details_page():
        # handler logic here
        return render_template("job_details_page.html")
    
        
    @app.route("/scrape_linkedin", methods=["POST"])
    def scrape_linkedin():
        linkedin_url = request.form.get("linkedin_url")

        # Get the HTML content of the LinkedIn job posting page
        html_doc = get_html_from_url(linkedin_url)

        # Scrape the job posting
        job_title, company_name, job_description = scrape_linkedin_job_posting(html_doc)

        # Return the scraped data as a JSON response
        return {
            "job_title": job_title,
            "company_name": company_name,
            "job_description": job_description
        }

    @app.route("/generate_cover_letter", methods=["POST"])
    def generate_cover_letter():
        with cover_letter_generator.lock:
            if cover_letter_generator.is_running:
                return {"status": "A cover letter generation is already in progress."}, 409
        print("Generating cover letter.")
        company_name = request.form.get("company_name")
        position = request.form.get("position")
        job_descript = request.form.get("job_descript")

        Thread(
            target=cover_letter_generator.query, args=(company_name, position, job_descript)
        ).start()

        return {"status": "Generating cover letter..."}, 202
        # cover_letter = cover_letter_generator.query(company_name, position, job_descript)
        # save_cover_letter_to_file(cover_letter)
        # return {"cover_letter": cover_letter}


    @app.route('/get_final_cover_letter', methods=['GET'])
    def get_final_cover_letter():
        with cover_letter_generator.lock:
            if cover_letter_generator.is_running:
                return {"status": "A cover letter generation is in progress."}, 409
        cover_letter_final = cover_letter_generator.query_final()
        save_cover_letter_to_file(cover_letter_final, cover_letter_generator.company_name)
        
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
    
    
    @app.route('/download', methods=['GET'])
    def download():
        company_name = cover_letter_generator.company_name.replace(" ", "_")
        txt_filename = f"generated_cover_letters/txt/{company_name}_cover_letter.txt"
        pdf_filename = f"generated_cover_letters/pdf/{company_name}_cover_letter.pdf"

        # Open the cover letter text file
        with open(txt_filename, 'r') as f:
            text = f.read()

        pdf = PDFDocument(pdf_filename)
        pdf.init_report()
        pdf.generate_style(font_size=11, font_name='Times-Roman')
        pdf.p(text)
        pdf.generate()

        # # Check if the PDF was created successfully
        if not os.path.exists(pdf_filename):
            return "Error: could not create PDF"
        cover_letter_generator.reset()  # re-initialize the cover letter generator
        # Send the PDF file to the user
        return send_file(pdf_filename, as_attachment=True)

