# Automated Cover Letter Generator 

This repository contains an Automated Cover Letter Generator, a tool that I've created for my portfolio to aid my job search. The generator is built with Python, utilizing the Flask web framework, LangChain, and OpenAI. It allows you to input a company name, job title, and job description, and then generates a professional, targeted cover letter that uses your resume (required), sample of cover letter (optional), and any other information.

## Features
- Web-based UI for user-friendly experience.
- API key management for OpenAI and Google Search.
- File upload support to create a database of past resumes and cover letters.
- Automated generation of a professional cover letter based on user's past resumes and cover letters, and the job description.

## Installation & Usage

### Prerequisites

- Python 3.9 or newer.

### Step 1: Clone the repository

You can clone the repository by running the following command:

```
git clone https://github.com/talqadi7/CoverLetterGenerator
```

### Step 2: Install the requirements

To install the requirements, navigate into the cloned repository and run:

```
pip install -r requirements.txt
```

### Step 3: Run the application

After installing the requirements, you can start the application by running:

```
python app.py
```

Then, navigate to `http://localhost:5000` in your web browser to use the application.

### Step 4: Set the API keys

The first time you run the application, it will prompt you to input your API keys for OpenAI and Google Search. This will create a secrets.ini that will store your API keys.

### Step 5: Upload your documents

You can upload your resumes and cover letters in PDF, TXT, or DOCX format. These documents will be used as a database to generate new cover letters.

### Step 6: Generate a cover letter

You can generate a new cover letter by inputting the company name, job title, and job description into the appropriate fields.

## Contact

If you have any questions or feedback, please feel free to reach out or open an issue. Contributions are also welcome.
