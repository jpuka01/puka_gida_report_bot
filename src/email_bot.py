# Main script for handling email triggers, processing data, responses, and 
# Google API interactions
from google.auth.transport.requests import Request
from google.oauth2 import service_account
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from email.mime.text import MIMEText
from faker import Faker
from config import SPREADSHEET_IDS
from gpt import report
import os.path
import unicodedata
import random
import base64
import json
import pandas as pd
import re

# Acess Google Sheets and Gmail
SCOPES = ['https://www.googleapis.com/auth/gmail.modify',
          'https://www.googleapis.com/auth/spreadsheets']

RANGE_NAME = 'Form Responses 1!A1:P1000'

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
def authenticate_gmail():
    creds = None
    if os.path.exists('token.json'):
        creds = Credentials.from_authorized_user_file('token.json', 
                                                      scopes=SCOPES)
        print("Loaded Gmail credentials from token.json") # Debug --> 1; GOOD

    else:
        print("Error: token.json not found.")
        return None

    gmail_service = build('gmail', 'v1', credentials=creds)
    print(f"Gmail service started: {gmail_service}") # Debug --> 2; GOOD (Gmail service started: <googleapiclient.discovery.Resource object at 0x00000219335797C0>)
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
    results = gmail_service.users().messages().list(userId='me', labelIds=['INBOX'], maxResults=10).execute()
    messages = results.get('messages', [])

    '''
    # Sensitive Data
src/credentials.json
src/authorized_clients.
src/config.py
src/API_KEY.json

# Environment Variables
venv/
    '''

    # Check if there are any emails
    if not messages:
        print('No new messages.')
    else:
        # Loop through each emails to process
        for message in messages:
            msg = gmail_service.users().messages().get(userId='me', id=message['id']).execute()
            email_data = msg['payload']['headers']
            email_subject = None
            email_sender = None
            
            # Extract the subject and sender information from the email header
            for data in email_data:
                if data['name'] == 'Subject':
                    email_subject = data['value']
                if data['name'] == 'From':
                    email_sender = extract_email_address(data['value']) # WHY VALUE INSTEAD OF NAME?

            # Verify if the email sender is authorized and if the subject
            # contains the trigger phase
            if email_subject and email_sender:
                if "generate report" in email_subject.lower() and email_sender in authorized_clients:
                    print(f"Processing request from {email_sender}") # Debug --> 5; GOOD
                    print("Authenticating Google Sheets...") # Debug --> 6; GOOD
                    authenticate_google_sheets()

                    # summary = trigger_gpt(google_sheets_service) **Should I use authenticate google sheets first?**
                    # send_email(service_acc, email_sender, "Your Requested Report", summary)
                    print("Report sent!") # Debug (temporary) --> 9; GOOD
                else:
                    print(f"Ignoring email from {email_sender} with subject: {email_subject}")

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
Input:
Output:
Effects:
Assumptions:
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

"""
def normalize_column_names(df):
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

def clean_data(df):
    print("Cleaning data...") # Debugging statement
    # Define the expected rating columns
    expected_columns = [
        'Genel Memnuniyet', 'Dönerin Lezzeti ve Kalitesi', 'Menü Seçenekleri',
        'Hizmet Hızı', 'Temizlik', 'Personel Güler Yüzlülüğü ve Yardımseverliği',
        'Porsiyon Büyüklüğü', 'Fiyat/Performans Oranı', 'Tekrar Ziyaret Etme Olasılığı',
        'Ürün Kalitesi', 'Ürün Çeşitliliği', 'Ürünlerin Tazeliği', 'Mağaza Temizliği',
        'Personel Yardımseverliği ve Güler Yüzlülüğü', 'Genel Deneyim', 'Menü Çeşitliliği',
        'Hizmet Kalitesi', 'Çevre', 'Bekleme Süresi', 'Tavsiye Etme Olasiliği' 
    ]
    
    missing_columns = []

    # Check and clean only the columns that are present in the DataFrame
    for col in :
        if col in df.expected_columnscolumns: # CHECK THIS!!
            df[col] = pd.to_numeric(df[col], errors='coerce').fillna(0)
            print(f"Cleaned column '{col}'") # Debugging statement
        else:
            missing_columns.append(col)

    if missing_columns:
        print(f"Warning: The following columns were not found in the data and were skipped: {', '.join(missing_columns)}")

    return df

def read_sheet_data(service, spreadsheet_id):
    # For debugging purposes
    sheet = service.spreadsheets()
    spreadsheet_metadata = sheet.get(spreadsheetId=spreadsheet_id).execute()
    spreadsheet_name = spreadsheet_metadata.get('properties', {}).get('title', 'Unknown Spreadsheet')
    print(f"Reading spreadsheet: {spreadsheet_name}") # Debugging statement BAD

    result = sheet.values().get(spreadsheetId=spreadsheet_id,
                                range=RANGE_NAME).execute()
    values = result.get('values', [])

    if not values:
        print('No data found.')
        return None
    
    # Convert the data to a DataFrame
    df = pd.DataFrame(values[1:], columns=values[0])

    # Normalize the column names by removing diacritical marks
    df = normalize_column_names(df)

    print("Normalized Columns:", df.columns.tolist()) # Debugging statement BAD
    return df

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
if __name__ == "__main__":
    gmail_service = authenticate_gmail()
    check_email(gmail_service)