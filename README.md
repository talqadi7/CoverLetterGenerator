# Automated Cover Letter Generator 

This project produces personalized cover letters based on the input of company name, job position, and job description. Leveraging a unique combination of document loaders, embeddings, and streaming server-sent events, it delivers a real-time, user-friendly experience while maintaining precise formatting and high-quality content. The generator is built with Python, utilizing the Flask web framework, LangChain, and OpenAI. It allows you to input a company name, job title, and job description, and then generates a professional, targeted cover letter that uses your resume (required), sample of cover letter (optional), and any other information.

## Features
- Web-based UI for user-friendly experience.
- API key management for OpenAI and Google Search.
- File upload support to create a database of past resumes and cover letters.
- Automated generation of a professional cover letter based on user's past resumes and cover letters, and the job description.

## Installation & Usage

### Prerequisites

- Python 3.12 or newer (required by the project dependencies)
- uv package manager (for faster dependency installation)

### Step 1: Install Python

Ensure you have Python 3.12+ installed on your system. You can download it from [python.org](https://www.python.org/downloads/) or use your system's package manager.

To verify your Python version:

```bash
python --version
```

### Step 2: Install uv

uv is a fast Python package installer and resolver built in Rust. Install it using one of the following methods:

**For macOS/Linux:**
```bash
curl -LsSf https://astral.sh/uv/install.sh | sh
```

**For Windows:**
```bash
powershell -c "irm https://astral.sh/uv/install.ps1 | iex"
```

**Using pip:**
```bash
pip install uv
```

### Step 3: Clone the repository

Clone the repository by running:

```bash
git clone https://github.com/talqadi7/CoverLetterGenerator
cd CoverLetterGenerator
```

### Step 4: Install the dependencies

Using uv for faster installation:

```bash
uv sync
```

### Step 5: Run the application

After installing the dependencies, start the application:

```bash
uv run python app.py
```

Then, navigate to `http://localhost:5000` in your web browser to use the application.

### Step 6: Set the API keys

The first time you run the application, it will prompt you to input your API keys for OpenAI and Google Search. This will create a secrets.ini that will store your API keys.

### Step 7: Upload your documents

You can upload your resumes and cover letters in PDF, TXT, or DOCX format. These documents will be used as a database to generate new cover letters.

### Step 8: Generate a cover letter

You can generate a new cover letter by inputting the company name, job title, and job description into the appropriate fields.

---

## Testing and Linting

This repository uses a GitHub Actions workflow for automated testing and linting. With each push, this workflow runs the tests defined in the `tests` directory using `pytest`, and checks the code for styling issues with `flake8`. You can see the details of this workflow in `.github/workflows/main.yml`.

You can also run the tests and linting locally before pushing to the repository. To run the tests and linting, open a terminal in the root directory of the project and execute the following command:

```bash
bash run_tests.sh
```
