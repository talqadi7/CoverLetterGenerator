from openai import OpenAI

import logging

# Template for the cover letter prompt
COVER_LETTER_TEMPLATE = """You're a cover letter writer expert. Use the details and instructions below to write me a professional and tailored cover letter.

My name: {name}
My address: {address}
My email: {email}

Details:
Job position, company name, and job description: {question}
Resume and Information: {context}

Writing Style Reference:
{cover_letter_samples}

Instructions:
1. FOCUS ON THE JOB DESCRIPTION! But you don't have to address every point in the job description.
2. Figure out what skills that job requires, and match it with the provided information.
3. Use the details provided as a guide, but DO NOT COPY DIRECTLY. Paraphrase and present the information in a unique and original manner.
4. DON'T make up any information or an answer.
5. You don't have to address every point in the job description.
6. If possible, focus on my most recent experience
7. If a skill is not listed in the provided information, then I don't have experience in it.
8. Follow the cover letter instructions.
9. IMPORTANT: If cover letter samples are provided, match the tone, style, and format of those samples in your output.

This is some information for writing an effective cover letter:

Cover letter is a writing sample and a part of the screening process. By putting your best foot forward, you can increase your chances of being interviewed. A good way to create a response-producing cover letter is to highlight your skills or experiences that are most applicable to the job or industry and to tailor the letter to the specific organization you are applying to.
Some general rules about letters:
• Address your letters to a specific person if you can.
• Tailor your letters to specific situations or organizations by doing research before writing your letters.
• Keep letters concise and factual, no more than a single page. Avoid flowery language.
• Give examples that support your skills and qualifications.
• Put yourself in the reader's shoes. What can you write that will convince the reader that you are ready and able to do the job?
• Don't overuse the pronoun "I".
• Remember that this is a marketing tool. Use lots of action words.
• Reference skills or experiences from the job description and draw connections to your credentials.
• Make sure your resume and cover letter are prepared with the same font type and size.
• Make the addressee want to read your resume.
• Be brief, but specific.
• Ask for a meeting.
• End the cover letter with a nice statement about their company reputation or why you'd like to
work for them specifically.

Cover Letter:"""

def generate_cover_letter(question, context, cover_letter_samples="", name="", address="", email="", stream=False, stream_handler=None):
    """
    Generate a cover letter using the OpenAI API.
    
    Args:
        question: The job details (position, company, job description)
        context: Resume and other relevant information
        cover_letter_samples: Previous cover letters to use as writing style examples
        name: User's name
        address: User's address
        email: User's email
        stream: Whether to stream the response
        stream_handler: Handler for streaming chunks
        
    Returns:
        The generated cover letter
    """
    # Add a writing style instruction if cover letter samples are provided
    writing_style_section = ""
    if cover_letter_samples:
        writing_style_section = "Below are examples of my previous cover letters. Please use these as a reference for my writing style and tone:\n\n" + cover_letter_samples
    else:
        writing_style_section = "No previous cover letter samples provided. Please use a professional, concise style."
    
    prompt = COVER_LETTER_TEMPLATE.format(
        question=question,
        context=context,
        cover_letter_samples=writing_style_section,
        name=name,
        address=address,
        email=email
    )
    
    client = OpenAI()
    try:
        # Call the OpenAI API directly
        response = client.chat.completions.create(model="gpt-4.5-preview",
        messages=[
            {"role": "system", "content": "You are a professional cover letter writer. Match the writing style of any provided samples."},
            {"role": "user", "content": prompt}
        ],
        temperature=0.2,
        max_tokens=3000,
        stream=stream)

        # If streaming, handle the chunks and construct the full response
        if stream:
            full_response = ""
            for chunk in response:
                if stream_handler:
                    stream_handler.handle_chunk(chunk)
                if hasattr(chunk, 'choices') and len(chunk.choices) > 0 and chunk.choices[0].delta.content:
                    full_response += chunk.choices[0].delta.content
            return full_response
        else:
            # Return the full response for non-streaming case
            return response.choices[0].message.content

    except Exception as e:
        logging.error(f"Error generating cover letter: {e}")
        return f"Error generating cover letter: {e}"