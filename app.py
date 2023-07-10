from flask import Flask
import os
import configparser
from src.routes import register_routes
from src.main import CoverLetterGenerator
import logging

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

# Register the routes
register_routes(app, cover_letter_generator)


if __name__ == "__main__":
    app.run(debug=True)
