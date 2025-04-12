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
from src.document_manager import DocumentManager
import os
import logging

logging.basicConfig(level=logging.INFO)


def register_routes(app, cover_letter_generator):
    # Initialize the document manager
    document_manager = DocumentManager()
    
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
        
        # Get the new user information fields
        user_name = request.form.get("user_name", "")
        user_address = request.form.get("user_address", "")
        user_email = request.form.get("user_email", "")
        
        is_running, response, status_code = generate_cover_letter_async(
            cover_letter_generator, company_name, position, job_descript,
            user_name, user_address, user_email
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
        
        # Save the cover letter to a file and get the filename
        txt_filename = save_cover_letter_to_file(
            cover_letter_final, cover_letter_generator.company_name
        )
        
        logging.info(f"Cover letter saved to {txt_filename}")
        return jsonify({"cover_letter": cover_letter_final})

    @app.route("/generate_cover_letter", methods=["GET"])
    def stream_generate_cover_letter():
        def generate():
            for message in cover_letter_generator.get_streamed_messages():
                yield f"data: {message}\n\n"

        return Response(stream_with_context(generate()), mimetype="text/event-stream")

    @app.route("/set_keys", methods=["GET", "POST"])
    def set_keys():
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
        try:
            # Get sanitized company name
            sanitized_company_name = sanitize_filename(cover_letter_generator.company_name)
            logging.info(f"Downloading cover letter for company: {sanitized_company_name}")
            
            # Generate filenames
            txt_filename = generate_filename(sanitized_company_name, "txt")
            pdf_filename = generate_filename(sanitized_company_name, "pdf")

            logging.info(f"Text filename: {txt_filename}")
            logging.info(f"PDF filename: {pdf_filename}")
            
            # Ensure directories exist
            os.makedirs(os.path.dirname(txt_filename), exist_ok=True)
            os.makedirs(os.path.dirname(pdf_filename), exist_ok=True)

            # If text file doesn't exist, create it from the current cover letter
            if not file_exists(txt_filename):
                logging.info("Text file doesn't exist, creating it now")
                cover_letter_text = cover_letter_generator.query_final()
                if not cover_letter_text:
                    logging.error("No cover letter content available")
                    return "Error: No cover letter has been generated", 400
                
                # Save the cover letter to a file
                txt_filename = save_cover_letter_to_file(cover_letter_text, sanitized_company_name)
            
            # Read the text from the text file
            try:
                text = read_text_file(txt_filename)
                logging.info(f"Successfully read text file with {len(text)} characters")
            except Exception as e:
                logging.error(f"Error reading text file: {e}")
                return f"Error reading text file: {str(e)}", 500

            # Create a PDF from the text
            try:
                create_pdf_from_text(text, pdf_filename)
                logging.info(f"Successfully created PDF file at {pdf_filename}")
            except Exception as e:
                logging.error(f"Error creating PDF: {e}")
                return f"Error creating PDF: {str(e)}", 500

            # Check if the PDF was created successfully
            if not file_exists(pdf_filename):
                logging.error(f"PDF file was not created: {pdf_filename}")
                return "Error: Could not create PDF", 500

            # Send the PDF file to the user
            try:
                download_name = f"{sanitized_company_name}_cover_letter.pdf"
                logging.info(f"Sending file {pdf_filename} as {download_name}")
                return send_file(
                    pdf_filename, 
                    as_attachment=True, 
                    download_name=download_name
                )
            except Exception as e:
                logging.error(f"Error sending file: {e}")
                return f"Error sending file: {str(e)}", 500
                
        except Exception as e:
            logging.error(f"Unexpected error in download route: {e}")
            return f"An unexpected error occurred: {str(e)}", 500
            
    # New routes for document management
    @app.route("/manage_documents", methods=["GET"])
    def manage_documents():
        resumes, cover_letters, other_documents = document_manager.get_documents()
        return render_template("manage_documents.html", 
                             resumes=resumes, 
                             cover_letters=cover_letters, 
                             other_documents=other_documents)
    
    @app.route("/view_document/<document_id>", methods=["GET"])
    def view_document(document_id):
        document = document_manager.get_document_by_id(document_id)
        if document is None:
            return "Document not found", 404
        
        # Determine content type based on file extension
        _, file_extension = os.path.splitext(document['path'])
        content_type = "text/plain"  # Default content type
        
        if file_extension.lower() == '.pdf':
            content_type = "application/pdf"
        elif file_extension.lower() == '.docx':
            content_type = "application/vnd.openxmlformats-officedocument.wordprocessingml.document"
            
        return send_file(document['path'], mimetype=content_type)
    
    @app.route("/download_document/<document_id>", methods=["GET"])
    def download_document(document_id):
        document = document_manager.get_document_by_id(document_id)
        if document is None:
            return "Document not found", 404
            
        return send_file(
            document['path'], 
            as_attachment=True, 
            download_name=document['filename']
        )
    
    @app.route("/delete_document/<document_id>", methods=["DELETE"])
    def delete_document(document_id):
        success = document_manager.delete_document(document_id)
        if success:
            # Reset the generator to reload documents
            reset_generator(cover_letter_generator)
            return jsonify({"status": "success"}), 200
        else:
            return jsonify({"status": "error", "message": "Failed to delete document"}), 400