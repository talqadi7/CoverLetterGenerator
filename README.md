# Automated Cover Letter Generator 

This project produces personalized cover letters based on the input of company name, job position, and job description. Leveraging a unique combination of document loaders, embeddings, and streaming server-sent events, it delivers a real-time, user-friendly experience while maintaining precise formatting and high-quality content. The generator is built with Python, utilizing the Flask web framework, LangChain, and OpenAI. It allows you to input a company name, job title, and job description, and then generates a professional, targeted cover letter that uses your resume (required), sample of cover letter (optional), and any other information.

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

---

## Testing and Linting

This repository uses a GitHub Actions workflow for automated testing and linting. With each push, this workflow runs the tests defined in the `tests` directory using `pytest`, and checks the code for styling issues with `flake8`. You can see the details of this workflow in `.github/workflows/main.yml`.

You can also run the tests and linting locally before pushing to the repository. To run the tests and linting, open a terminal in the root directory of the project and execute the following command:

```bash
bash run_tests.sh
```

## Future Updates

Here are some planned enhancements for future updates:

- ✅ **Integrate Streaming Responses:** I'm looking to include stream responses, to alleviate the total wait time for the prediction.

- **Integration with Google SERPer:** I aim to connect the agent with the internet so as to leverage real-time data during the cover letter creation process. This could make the tool even more dynamic and relevant.

- **Secure Key Storage:** Security is crucial when dealing with sensitive data such as API keys. I'm exploring more secure options for storing these keys instead of just saving them in statically in a file, to ensure that the application remains secure.

- ✅ **Simplified Job Input:** To enhance user experience, I'm looking to eventually implement a feature where you only need to provide a link to a job posting. The application would then scrape necessary details such as company name, job title, and job description directly from the posting.

## Contact

If you have any questions or feedback, please feel free to reach out or open an issue. Contributions are also welcome.
