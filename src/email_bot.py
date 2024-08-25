'''
Name:    email_bot.py
Author:  John Puka
Purpose: Main script for handling email triggers, processing data, responses, 
         and  Google API interactions
'''
from apscheduler.schedulers.background import BackgroundScheduler
from flask import Flask, request, jsonify
from google.auth.transport.requests import Request
from google.auth.exceptions import RefreshError
from google.oauth2 import service_account
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from email.mime.text import MIMEText
from faker import Faker
from config import SPREADSHEET_IDS
from faker import Faker
# from gpt import report
import os.path
import unicodedata
import random
import base64
import json
import pandas as pd
import time
import re

# Acess Google Sheets and Gmail
SCOPES = ['https://www.googleapis.com/auth/gmail.modify',
          'https://www.googleapis.com/auth/spreadsheets']

RANGE_NAME = 'Form Responses 1!A1:P1000'

# app = Flask(__name__)

'''
Name:        authenticate_gmail
Purpose:     Authenticates with the Gmail API using a 'token.json' file that 
             contains the OAuth authentication
Inputs:      None
Outputs:     A Gmail service object if authentication is enabled; otherwise
             None
Effects:     Reads from the 'token.json' file
Assumptions: The file 'token.json' exists and contains valid credentials for 
             the Gmail
'''
# CHANGE FUNCTION CONTRACT
def authenticate_gmail():
    creds = None
    if os.path.exists('token.json'):
        creds = Credentials.from_authorized_user_file('token.json', 
                                                      scopes=SCOPES)
        print("Loaded Gmail credentials from token.json successfuly.\n") # Debug --> 1; GOOD

    # Refresh the token if it has expired
    if creds and creds.expired and creds.refresh_token:
        try:
            creds.refresh(Request())
            print("Token refreshed successfully.\n") # Debug --> 2; GOOD
            # Save the refresh token back to token.json
            with open('token.json', 'w') as token:
                token.write(creds.to_json())
        except RefreshError:
            print("Token expired or revoked. Initiating a new token \
                  authentication flow.\n")
            creds = None
    
    # If no valid credentials were loaded or token.json does not exist
    if not creds:
        if not os.path.exists('credentials.json'):
            print("Error: credentials.json not found.\n")
            return None
        flow = InstalledAppFlow.from_client_secrets_file('credentials.json', 
                                                         scopes=SCOPES)
        creds = flow.run_local_server(port=0)
        # Save the new credentials to token.json
        with open('token.json', 'w') as token:
            token.write(creds.to_json())
        print("New token saved to token.json.\n")

    gmail_service = build('gmail', 'v1', credentials=creds)
    print(f"Gmail service started: {gmail_service}.\n") # Debug --> 3; GOOD (Gmail service started: <googleapiclient.discovery.Resource object at 0x00000XXXXXXX>)
    return gmail_service
'''
Name:        check_email 
Purpose:     Checks the 10 most recent emails for a "Generate Report" string
             and processes the request if the sender is authorized
Input:       The authenticated Gmail and Sheets service object
Output:      None
Effects:     Reads emails from the Gmail inbox and processes the request
Assumptions: The Gmail and Sheets service object is authenticated and the 
             authorized clients list is loaded
'''
def check_email(gmail_service): # include google_sheets_service
    # Load the list of authorized clients
    authorized_clients = load_authorized_clients()

    # Retrieve the 10 most recent emails in the inbox of the receiver (AUTOMATE THIS LATER)
    results = gmail_service.users().messages().list(userId='me', 
                                                    labelIds=['INBOX'], 
                                                    maxResults=10).execute()
    messages = results.get('messages', [])

    # Check if there are any emails
    if not messages:
        print('No new messages.')
    else:
        # Loop through each emails to process
        for message in messages:
            msg = gmail_service.users().messages().get(userId='me', 
                                                       id=message['id']
                                                       ).execute()
            email_data = msg['payload']['headers']
            email_subject = None
            email_sender = None
            
            # Extract the subject and sender information from the email header
            for data in email_data:
                if data['name'] == 'Subject':
                    email_subject = data['value']
                if data['name'] == 'From':
                    email_sender = extract_email_address(data['value'])

            # Verify if the email sender is authorized and if the subject
            # contains the trigger phase
            if email_subject and email_sender:
                if "generate report" in email_subject.lower() and \
                    email_sender in authorized_clients:
                    print(f"Processing request from {email_sender}") # Debug --> 5; GOOD
                    print("Authenticating Google Sheets...") # Debug --> 6; GOOD
                    authenticate_google_sheets()

                    # summary = trigger_gpt(google_sheets_service) **Should I use authenticate google sheets first?**
                    # send_email(service_acc, email_sender, "Your Requested Report", summary)
                    print("Report sent!") # Debug (temporary) --> 9; GOOD
                else:
                    print(f"Ignoring email from {email_sender} with subject: "
                          f"{email_subject}")
'''
Name:        scheduler()
Purpose:     Sets a monthly scheduled report generation task to be executed
Inputs:      None
Outputs:     None
Effects:     Schedules a task to run the check_email function each month
Assumptions: The check_email function is defined # CHECK IF SYSTEM HAS A TASK
'''
def scheduler():
    # Set up the scheduler
    scheduler = BackgroundScheduler()
    scheduler.add_job(check_email, 'cron', day=29, hour=7, minute=0, 
                      args=[gmail_service] ) # Run morning on the 29th monthly
    scheduler.start()
    print("Scheduler started") # Debug

'''
Name:        load_authorized_clients (helper function)
Purpose:     Loads and returns a list of authorized client email addresses from
             a file called 'authorized_clients.json'
Inputs:      None
Outputs:     A list of email addresses as strings of authorized clients 
             (List[str])
Effects:     Reads from 'authorized_clients.json'
Assumptions: File 'authorized_clients.json' exists, formatted correctly, and
             has a key "AUTHORIZED_CLIENTS" containing the list of authorized
             clients
'''
def load_authorized_clients():
    with open('authorized_clients.json', 'r') as file:
        data = json.load(file)
        authorized_clients = [client.strip().lower() for client in 
                              data.get("AUTHORIZED_CLIENTS", [])]
        print(f"Authorized Clients:  {authorized_clients}") # Debug --> 3; GOOD
    return authorized_clients

'''
Name:        extract_email_address (helper function)
Purpose:     Extracts the email address from a given string
Input:       A string that potentially contains an email address
Output:      The extracted email address as a string if found, otherwise None
Effects:     None
Assumptions: The input string may or may not contain a valid email address
'''
def extract_email_address(email_string):
    match = re.search(r'[\w\.-]+@[\w\.-]+', email_string)
    print(f"Extracted email address: {match}") # Debug --> 4; GOOD
    return match.group(0).strip().lower() if match else None
'''
Name:        authenticate_google_sheets
Purpose:     Authenticates with the Sheets API using a 'token.json' file that 
             contains the OAuth authentication
Input:       None
Outputs:     A Google Sheets service object if authentication is enabled; 
             otherwise None
Effects:     Reads from the 'token.json' file
Assumptions: The file 'token.json' exists and contains valid credentials for 
             Google Sheets
'''
def authenticate_google_sheets():
    creds = None
    if os.path.exists('token.json'):
        creds = Credentials.from_authorized_user_file('token.json',
                                                  scopes=SCOPES)
        print("Loaded Google Sheets credentials from token.json") # Debug --> 7; GOOD

    else:
        print("Error: token.json not found.")
        return None
    
    google_sheets_service = build('sheets', 'v4', credentials=creds)
    print(f"Authenticated Google Sheets service: {google_sheets_service}" ) # Debug --> 8; GOOD (Authenticated Google Sheets service: <googleapiclient.discovery.Resource object at 0x000001C5CFBCCA40>)
    return google_sheets_service
###############################################################################
r"""
def read_sheet_data(google_sheets_service, spreadsheet_id):
    format_type = SPREADSHEET_IDS[spreadsheet_id]
    RANGE_NAME = 'Form Responses 1!A1:P1000'
    
    sheet = google_sheets_service.spreadsheets()
    result = google_sheets_service.values().get(spreadsheetId=spreadsheet_id,
                                                range=RANGE_NAME).execute()
    values = result.get('values', [])

    if not values:
        print('No data found.')
        return None
    
    # Convert the data to a DataFrame
    df = pd.DataFrame(values[1:], columns=values[0])

    # Normalize the column names by removing diacritical marks and clean data
    df = normalize_column_names(df, format_type)
    df = clean_data(df, format_type)

    print("Normalized Columns:", df.columns.tolist()) # Debug
    return df

# helper function
def normalize_column_names(df, format_type):
    if format_type == 'market':
        column_mapping = {
            'Genel Memnuniyet': 'General Satisfaction',
            'Ürün Kalitesi': 'Product Quality',
            'Ürün Çeşitliliği': 'Product Variety',
            'Ürünlerin Tazeliği': 'Product Freshness',
            'Mağaza Temizliği': 'Store Cleaniness',
            'Personel Yardımseverliği ve Güler Yüzlülüğü': 'Staff Quality',
            'Fiyat/Performans Oranı': 'Pricing',
            'Bekleme Süresi': 'Waiting Time',
            'Tavsiye Etme Olasılığı': 'Recommendation Likelihood',
            # 'Ek Yorumlar ve Öneriler'
            # 'İsim'
        }
        # ADD PRINT ERROR
    elif format_type == 'doner':
        column_mapping = {
            'Genel Memnuniyet': 'General Satisfaction',
            'Dönerin Lezzeti ve Kalitesi': 'Doner Taste and Quality',
            'Menü Seçenekleri': 'Menu Options',
            'Hizmet Hızı': 'Service Speed',
            'Temizlik': 'Cleanliness',
            'Personel Güler Yüzlülüğü ve Yardımseverliği': 'Staff Quality',
            'Porsiyon Büyüklüğü': 'Serving Size',
            'Fiyat/Performans Oranı': 'Pricing',
            'Tekrar Ziyaret Etme Olasılığı': 'Revisit Likelihood',
            # 'Ek Yorumlar ve Öneriler'
            # 'İsim'
        }
    elif format_type == 'restaurant':
        column_mapping = {
            'Genel Deneyim': 'Overall Experience',
            'Yemek Kalitesi': 'Food Quality',
            'Menü Çeşitliliği': 'Menu Variety',
            'Hizmet Kalitesi': 'Service Quality',
            'Temizlik': 'Cleanliness',
            'Fiyat/Performans Oranı': 'Pricing',
            'Çevre': 'Restaurant Atmosphere',
            'Bekleme Süresi': 'Waiting Time',
            'Tavsiye Etme Olasılığı': 'Recommendation Likelihood',
            # 'Ek Yorumlar'
            # 'İsim'
        }

    df.rename(columns=column_mapping, inplace=True)
    return df

    '''
    print('Normalizing column names...') # Debugging statement
    normalized_columns = {}
    for col in df.columns:
        # Normalize the column names by removing diacritical marks
        normalized_col = unicodedata.normalize('NFKD', col).encode('ascii', 'ignore').decode('ascii').strip()
        normalized_col = re.sub(r'[^A-Za-z0-9\s]', '', normalized_col)
        normalized_col = re.sub(r'\s+', ' ', normalized_col)
        normalized_col = normalized_col.strip().title()
        normalized_columns[col] = normalized_col
        print(f"Normalized '{col}' to '{normalized_col}") # Debugging statement
    df.rename(columns=normalized_columns, inplace=True)
    return df
    '''


def clean_data(df, format_type):
    print("Cleaning data...") # Debugging statement
    
    # Define the expected columns for each format type
    expected_columns_mapping = {
        'market': [
            'Genel Memnuniyet', 'Ürün Kalitesi', 'Ürün Çeşitliliği',
            'Ürünlerin Tazeliği', 'Mağaza Temizliği',
            'Personel Yardımseverliği ve Güler Yüzlülüğü', 'Fiyat/Performans Oranı',
            'Bekleme Süresi', 'Tavsiye Etme Olasılığı'
        ],
        'doner': [
            'Genel Memnuniyet', 'Dönerin Lezzeti ve Kalitesi', 'Menü Seçenekleri',
            'Hizmet Hızı', 'Temizlik',
            'Personel Güler Yüzlülüğü ve Yardımseverliği', 'Porsiyon Büyüklüğü',
            'Fiyat/Performans Oranı', 'Tekrar Ziyaret Etme Olasılığı'
        ],
        'restaurant': [
            'Genel Deneyim', 'Yemek Kalitesi', 'Menü Çeşitliliği',
            'Hizmet Kalitesi', 'Temizlik', 'Fiyat/Performans Oranı', 'Çevre',
            'Bekleme Süresi', 'Tavsiye Etme Olasılığı'
        ]
    }

    # Get the expected columns for the given format type
    expected_columns = expected_columns_mapping.get(format_type, []) 
    
    missing_columns = []

    # Check and clean only the columns that are present in the DataFrame
    for col in expected_columns:
        if col in df.columns: # CHECK THIS!!
            df[col] = pd.to_numeric(df[col], errors='coerce').fillna(0)
            print(f"Cleaned column '{col}'") # Debugging statement
        else:
            missing_columns.append(col)

    if missing_columns:
        print(f"Warning: The following columns were not found in the data and were skipped: {', '.join(missing_columns)}")

    return df
///////////////////////////////////////////////////////////////////////////////
def summarize_data(df):
    print("Summarizing data...") # Debugging statement
    summary = {}

    if 'Genel Memnuniyet' in df.columns or 'Genel Deneyim' in df.columns:
        if 'Genel Memnuniyet' in df.columns:
            summary['General Satisfaction'] = df['Genel Memnuniyet'].mode()[0]
        elif 'Genel Deneyim' in df.columns:
             summary['General Satisfaction'] = df['Genel Deneyim'].mode()[0]

    if 'Dönerin Lezzeti ve Kalitesi' in df.columns:
        summary['Taste and Quality of Doner'] = df['Dönerin Lezzeti ve Kalitesi'].mode()[0]

    if 'Menü Seçenekleri' in df.columns:
        summary['Menu Options'] = df['Menü Seçenekleri'].mode()[0]

    if 'Hizmet Hızı' in df.columns or 'Bekleme Süresi' in df.columns:
        if 'Hizmet Hızı' in df.columns:
            summary['Service Speed'] = df['Hizmet Hızı'].mode()[0]
        elif 'Bekleme Süresi' in df.columns:
            summary['Service Speed'] = df['Bekleme Süresi'].mode()[0]

    if 'Temizlik' in df.columns or 'Mağaza Temizliği' in df.columns:
        if 'Temizlik' in df.columns:
            summary['Cleanliness'] = df['Temizlik'].mode()[0]
        elif 'Mağaza Temizliği' in df.columns:
            summary['Cleanliness'] = df['Mağaza Temizliği'].mode()[0]

    if 'Personel Güler Yüzlülüğü ve Yardımseverliği' in df.columns or 'Personel Yardımseverliği ve Güler Yüzlülüğü' in df.columns:
        if 'Personel Güler Yüzlülüğü ve Yardımseverliği' in df.columns:
            summary['Staff Quality'] = df['Personel Güler Yüzlülüğü ve Yardımseverliği'].mode()[0]
        elif 'Personel Yardımseverliği ve Güler Yüzlülüğü' in df.columns:
            summary['Staff Quality'] = df['Personel Yardımseverliği ve Güler Yüzlülüğü'].mode()[0]
    
    if 'Porsiyon Büyüklüğü' in df.columns:
        summary['Serving Size'] = df['Porsiyon Büyüklüğü'].mode()[0]
    
    if 'Fiyat/Performans Oranı' in df.columns:
        summary['Pricing'] = df['Fiyat/Performans Oranı'].mode()[0]

    if 'Tekrar Ziyaret Etme Olasılığı' in df.columns:
        summary['Return Rate'] = df['Tekrar Ziyaret Etme Olasılığı'].mode()[0]

    if 'Ürün Kalitesi' in df.columns or 'Ürünlerin Tazeliği' in df.columns:
        if 'Ürün Kalitesi' in df.columns:
            summary['Product Quality/Freshness'] = df['Ürün Kalitesi'].mode()[0]
        elif 'Ürünlerin Tazeliği' in df.columns:
            summary['Product Quality/Freshness'] = df['Ürünlerin Tazeliği'].mode()[0]

    if 'Ürün Çeşitliliği' in df.columns:
        summary['Product Variety'] = df['Ürün Çeşitliliği'].mode()[0]
    
    if 'Menü Çeşitliliği' in df.columns:
        summary['Menu Variety'] = df['Menü Çeşitliliği'].mode()[0]

    if 'Hizmet Kalitesi' in df.columns:
        summary['Service Quality'] = df['Hizmet Kalitesi'].mode()[0]
    
    if 'Çevre' in df.columns:
        summary['Environment'] = df['Çevre'].mode()[0]

    if 'Tavsiye Etme Olasılığı' in df.columns:
        summary['Willing to Recommend'] = df['Tavsiye Etme Olasılığı'].mode()[0]

    return summary

def generate_contextual_comment(fake):
    templates = [
        "I really enjoyed the {} at your {}.",
        "The {} was {} but the {} could use some improvement.",
        "I found the {} to be {}. Keep up the good work!",
        "The {} was a bit {} this time, but overall a good experience.",
        "I would definitely recommend the {} at your {}."
    ]
    
    # Contextual words
    food_items = ['doner', 'menu', 'service', 'staff']
    places = ['restaurant', 'location', 'branch']
    adjectives_positive = ['excellent', 'fantastic', 'great']
    adjectives_negative = ['average', 'underwhelming', 'disappointing']

    # Randomly choose a template and fill in the placeholders
    template = random.choice(templates)
    sentence = template.format(
        random.choice(food_items),
        random.choice(places),
        random.choice(food_items),
        random.choice(adjectives_negative),
        random.choice(adjectives_positive)
    )

    print("Contextual comments: " + sentence) # Debugging statement

    return sentence

def generate_synthetic_data(num_rows=25):
    print(f"Generating {num_rows} rows of synthetic data...") # Debugging statement
    fake = Faker()
    synthetic_data = []
    for _ in range(num_rows):
        row = {
            'Genel Memnuniyet': random.choice(['Çok Memnun', 'Memnun', 'Nötr', 'Memnun Değil', 'Hiç Memnun Değil']),
            'Dönerin Lezzeti ve Kalitesi': random.choice(['Mükemmel', 'İyi', 'Ortalama', 'Ortalama Alti', 'Kötü']),
            'Menü Seçenekleri': random.choice(['Çok Memnun', 'Memnun', 'Nötr', 'Memnun Değil', 'Hiç Memnun Değil']),
            'Hizmet Hızı': random.choice(['Mükemmel', 'İyi', 'Ortalama', 'Ortalama Alti', 'Kötü']), 
            'Temizlik': random.choice(['Çok Temiz', 'Temiz', 'Ortalama', 'Ortalama Alti', 'Kötü']), 
            'Personel Güler Yüzlülüğü ve Yardımseverliği': random.choice(['Mükemmel', 'İyi', 'Ortalama', 'Ortalama Alti', 'Kötü']),
            'Porsiyon Büyüklüğü': random.choice(['Çok Memnun', 'Memnun', 'Nötr', 'Memnun Değil', 'Hiç Memnun Değil']),
            'Fiyat/Performans Oranı': random.choice(['Mükemmel', 'İyi', 'Ortalama', 'Ortalama Alti', 'Kötü']), 
            'Tekrar Ziyaret Etme Olasılığı': random.choice(['Çok Yüksek', 'Yüksek', 'Nötr', 'Düşük', 'Çok Düşük']), 
            'Ürün Kalitesi': random.choice(['Mükemmel', 'İyi', 'Ortalama', 'Ortalama Alti', 'Kötü']), 
            'Ürün Çeşitliliği': random.choice(['Çok Memnun', 'Memnun', 'Nötr', 'Memnun Değil', 'Hiç Memnun Değil']),
            'Ürünlerin Tazeliği': random.choice(['Mükemmel', 'İyi', 'Ortalama', 'Ortalama Alti', 'Kötü']),  
            'Mağaza Temizliği': random.choice(['Çok Temiz', 'Temiz', 'Ortalama', 'Ortalama Alti', 'Kötü']), 
            'Personel Yardımseverliği ve Güler Yüzlülüğü': random.choice(['Mükemmel', 'İyi', 'Ortalama', 'Ortalama Alti', 'Kötü']),  
            'Genel Deneyim': random.choice(['Çok Memnun', 'Memnun', 'Nötr', 'Memnun Değil', 'Hiç Memnun Değil']), 
            'Menü Çeşitliliği': random.choice(['Çok Memnun', 'Memnun', 'Nötr', 'Memnun Değil', 'Hiç Memnun Değil']),
            'Hizmet Kalitesi': random.choice(['Mükemmel', 'İyi', 'Ortalama', 'Ortalama Alti', 'Kötü']),  
            'Çevre': random.choice(['Mükemmel', 'İyi', 'Ortalama', 'Ortalama Alti', 'Kötü']),  
            'Bekleme Süresi': random.choice(['Çok Memnun', 'Memnun', 'Nötr', 'Memnun Değil', 'Hiç Memnun Değil']), 
            'Tavsiye Etme Olasılığı': random.choice(['Çok Yüksek', 'Yüksek', 'Nötr', 'Düşük', 'Çok Düşük']),  
            'Ek Yorumlar': generate_contextual_comment(fake),
            'İsim': fake.first_name(),
            'WhatsApp Telefon Numarasi': fake.phone_number(),
            'Email': fake.email()
        }
        synthetic_data.append(row)
        df = pd.DataFrame(synthetic_data)
        print(f"Synthetic data generated: {df.head()} rows") # Debugging statement
    return df
        
def trigger_gpt(google_sheets_service):
    print("Triggering GPT...") # Debugging statement
    summary = ""
    for name, spreadsheet_id in SPREADSHEET_IDS.items():
        print(f"Processing sheet: {name}") # Debugging statement
        data = read_sheet_data(google_sheets_service, spreadsheet_id)
        if data is not None:
            data = clean_data(data)
            summary_data = summarize_data(data)
            additional_comments = data['Ek Yorumlar'].tolist() if 'Ek Yorumlar' in data.columns else None
            summary += f"\nReport for {name}:\n"
            summary += report(summary_data, additional_comments)
            print(f"Generated summary for {name}:\n" + summary) # Debugging statement
    return summary

def send_email(service, recipient, subject, body):
    message = MIMEText(body)
    message['to'] = recipient
    message['subject'] = subject
    raw = base64.urlsafe_b64encode(message.as_bytes()).decode()
    message = {'raw': raw}
    send_message = service.users().messages().send(userId='me', body=message).execute()
    print(f'Message sent to {recipient} with ID: {send_message["id"]}')
"""
# Webhook endpoint to trigger report generation
# @app.route()

if __name__ == "__main__":
    gmail_service = authenticate_gmail()

    check_email(gmail_service)
    scheduler()

    # Keep the script running
    try:
        while True:
            time.sleep(1)
    except (KeyboardInterrupt, SystemExit):
        scheduler.shutdown()