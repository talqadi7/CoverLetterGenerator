from flask import Flask
from src.routes import register_routes
from src.main import CoverLetterGenerator

app = Flask(__name__, static_folder='static')
cover_letter_generator = CoverLetterGenerator()
register_routes(app, cover_letter_generator)

if __name__ == "__main__":
    app.run(debug=True)