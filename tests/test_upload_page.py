import os
import pytest
from flask import url_for
from unittest.mock import patch


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


# def test_upload_page(client, move_vectorstore, cleanup_files):

#     with patch('main.CoverLetterGenerator.load_documents') as mock_load_documents:
#         mock_load_documents.return_value = None  # load_documents doesn't return anything
#         test_file_path = os.path.join(os.path.dirname(__file__), "test_data/test_resume.txt")

#         with open(test_file_path, "rb") as f:
#             data = {"file": (f, "test_data/test_resume.txt")}
#             response = client.post(
#                 url_for("upload_resume"), content_type="multipart/form-data", data=data
#             )

#         # Check if the request was successful
#         assert response.status_code == 200
#         # Check if load_documents was atleast called
#         mock_load_documents.assert_called()
