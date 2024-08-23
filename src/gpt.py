# Script for utilizing GPT and analyzing the data
# from openai import OpenAI --> DEBUG
'''
import json
import os

# Load API key from config.json
with open('API_KEY.json') as f:
    api_key_data = json.load(f)
    os.environ['OPENAI_API_KEY'] = api_key_data['OPENAI_API_KEY']

"""
DEBUG

client = OpenAI(
    api_key=os.environ.get("OPENAI_API_KEY"),
)
"""

def generate_prompt(summary_data, additional_comments=None):
    """
    Generates a prompt for GPT-4 based on the summarized survey data.
    """
    prompt = f"""
    You are a data analyst specializing in customer feedback for food services.
    Analyze the following customer feedback data for a food company called
    Puka Gida. The company's subsidiaries include:
    - Puka Doner (a fast food chain restaurant)
    - Puka Restoran (a family restaurant)
    - Puka Delicatessen (meat and delicatessen shops)
    The company is based in Uzunkopru, Edirne, Turkey, and is a startup.

    Your task is to:
    1. Summarize the overall sentiment.
    2. Identify key positive aspects.
    3. Highlight areas for improvement.

    Consider the location, demographics, and other relevant factors in your analysis.
    """
    # Include each summary point if it exists in the summary_data
    for key, value in summary_data.items():
        prompt += f"- {key}: {value}\n"

    if additional_comments:
        prompt += f"- Additional Comments: {additional_comments}\n"

    prompt += """
    Organize your analysis into the following categories:
    1. Puka Doner (fast food chain)
    2. Puka Restoran (family restaurant)
    3. Puka Delicatessen (meat and delicatessen shops)

    Provide a concise, well-formatted summary that is easy to read.
    """

    return prompt

def report(summary_data, additional_comments=None):
    """
    Sends the generated prompt to the GPT-4o model and returns the summary.
    """
    """
    prompt = generate_prompt(summary_data, additional_comments)

    try:
        response = client.chat.completions.create(
            messages=[
                {"role": "system", "content": "You are an expert data analyst."},
                {"role": "user", "content": prompt}
            ],
            model="gpt-4o-mini", # Switch to gpt-4 later or gpt-4o-mini
            max_tokens=200,
            temperature=0.7,
        )

        # Extract the message from the response
        summary = response.choices[0].message.content.strip()
        print(summary) # Debugging statement
        return summary
    
   # except openai.OpenAIError as e: FOR DEBUGGING LATER!!!
    except Exception as e:
        print(f"An error occured: {e}")
        return "There was an error in generating the report. Please try again later."
    """
    return "MOCK SUMMARY FOR DEBUGGING"
'''