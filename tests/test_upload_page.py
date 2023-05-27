import os
import pytest
from flask import url_for
from main import CoverLetterGenerator


@pytest.fixture
def move_vectorstore():
    # rename vectorstore.pkl before the test
    if os.path.exists("vectorstore.pkl"):
        os.rename("vectorstore.pkl", "vectorstore.pkl.temp")

    yield

    # rename vectorstore.pkl back after the test
    if os.path.exists("vectorstore.pkl.temp"):
        os.rename("vectorstore.pkl.temp", "vectorstore.pkl")


@pytest.fixture
def cleanup_files():
    yield
    # remove uploaded file and vectorstore.pkl after the test
    if os.path.exists("Data/resume.txt"):
        os.remove("Data/resume.txt")
    if os.path.exists("vectorstore.pkl"):
        os.remove("vectorstore.pkl")


def test_upload_page(client, move_vectorstore, cleanup_files):
    test_file_path = os.path.join(os.path.dirname(__file__), "data/test_resume.txt")

    with open(test_file_path, "rb") as f:
        data = {"file": (f, "data/test_resume.txt")}
        response = client.post(
            url_for("upload_resume"), content_type="multipart/form-data", data=data
        )

    # Check if the request was successful
    assert response.status_code == 200

    cover_letter_generator = CoverLetterGenerator()
    assert cover_letter_generator.embeddings_exists()
