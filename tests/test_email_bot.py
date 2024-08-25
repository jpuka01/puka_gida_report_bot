from unittest.mock import MagicMock, patch, mock_open
from google.auth.exceptions import RefreshError
import unittest
import pandas as pd
import sys
import os

# Add the src directory to the Python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), 
                                                '../src')))

from src.email_bot import (
    SCOPES,
    authenticate_gmail,
    check_email,
    scheduler,
    load_authorized_clients,
    extract_email_address,
    authenticate_google_sheets
)

'''
Test suite for the email_bot module.
    
This class contains unit tests for the functions in the email_bot module. It 
uses the unittest framework and mocks external dependencies to ensure that the 
tests are isolated and reliable.
'''
class TestEmailBot(unittest.TestCase):
    r'''
    ''
    Checks if the function correctly uses an existing, valid 'token.json' file
    to authenticate and build the Gmail service
    ''
    @patch('os.path.exists')
    @patch('builtins.open', new_callable=mock_open)
    @patch('src.email_bot.Credentials.from_authorized_user_file')
    @patch('src.email_bot.build')
    def test_authenticate_gmail_with_valid_token(self, mock_open, mock_build, 
                                                 mock_from_authorized_user_file,
                                                 mock_path_exists):
        # Setup mocks
        mock_path_exists.side_effect = lambda x: True if x in ['token.json', 'credentials.json'] else False
        mock_creds = MagicMock()
        mock_creds.expired = False
        mock_creds.refresh = MagicMock()
        mock_from_authorized_user_file.return_value = mock_creds
        
        # Call the function
        service = authenticate_gmail()

        # Assertions
        mock_from_authorized_user_file.assert_called_once_with('token.json', 
                                                               scopes=SCOPES)
        # mock_build.assert_called_once_with('gmail', 'v1', 
        #                                   credentials=mock_creds)
        mock_creds.refresh.assert_not_called()
            
    ''
    Verifies the behavior when the token is expired and the refresh token is 
    used; Also checks the fallback to a new token generation if the refresh 
    fails
    '
    @patch('os.path.exists')
    @patch('builtins.open', new_callable=mock_open)
    @patch('src.email_bot.Credentials.from_authorized_user_file')
    @patch('src.email_bot.build')
    @patch('src.email_bot.InstalledAppFlow.from_client_secrets_file')
    def test_authenticate_gmail_with_expired_token(self, mock_open,
                                                   mock_from_client_secrets_file,
                                                   mock_build, mock_from_authorized_user_file,
                                                   mock_path_exists):
        # Setup mocks
        mock_path_exists.side_effect = lambda x: True if x in ['token.json', 'credentials.json'] else False
        mock_creds = MagicMock()
        mock_creds.expired = True
        mock_creds.refresh = MagicMock()
        mock_creds.refresh.side_effect = RefreshError("Token expired or revoked.")
        mock_from_authorized_user_file.return_value = mock_creds
        mock_flow = MagicMock()
        mock_from_client_secrets_file.return_value = mock_flow
        mock_flow.run_local_server.return_value = mock_creds
        
        # Call the function
        service = authenticate_gmail()

        # Assertions
        mock_creds.refresh.assert_called_once()
        mock_from_client_secrets_file.assert_called_once_with('credentials.json',
                                                              scopes=SCOPES)
        mock_build.assert_called_once_with('gmail', 'v1', 
                                           credentials=mock_creds)
        mock_creds.refresh.assert_called_once_with('credentials.json')
        self.assertIsNotNone(service)
    '''
    '''
    Covers the scenario where 'token.json' does not exist, and new credentials 
    need to be generated using 'credentials.json'
    '''
    @patch('os.path.exists')
    @patch('builtins.open', new_callable=mock_open)
    @patch('src.email_bot.Credentials.from_authorized_user_file')
    @patch('src.email_bot.build')
    def test_authenticate_gmail_no_token_json(self, 
                                              mock_build, 
                                              mock_from_authorized_user_file, 
                                              mock_open, mock_path_exists):
        # Setup mocks
        mock_path_exists.side_effect = lambda x: True if x == 'credentials.json' else False
        mock_creds = MagicMock()
        mock_from_authorized_user_file.return_value = None
        mock_flow = MagicMock()
        mock_flow.run_local_server.return_value = mock_creds
        
        # Patch InstalledAppFlow
        with patch('src.email_bot.InstalledAppFlow.from_client_secrets_file', 
                   return_value=mock_flow) as mock_from_client_secrets_file:
            # Call the function
            service = authenticate_gmail()

            # Assertions
            mock_from_client_secrets_file.assert_called_once_with('credentials.json',
                                                                  scopes=SCOPES)
            mock_build.assert_called_once_with('gmail', 'v1',
                                               credentials=mock_creds)
            self.assertIsNotNone(service)
'''
    Ensures that the function correctly handles the absence of both 'token.json'
    and 'credentials.json', returning 'None'
    
    @patch('os.path.exists')
    @patch('src.email_bot.build')
    def test_authenticate_gmail_no_credentials_json(self, mock_build, 
                                                    mock_path_exists):
        # Setup mocks
        mock_path_exists.side_effect = lambda x: False
        
        # Call the function
        service = authenticate_gmail()

        # Assertions
        self.assertIsNone(service)
        mock_build.assert_not_called()

    
    @patch('src.email_bot.load_authorized_clients')
    @patch('src.email_bot.authenticate_google_sheets')
    @patch('src.email_bot.extract_email_address')
    @patch('src.email_bot.build')
    def test_check_gmail_with_generate_report_subject(self,
                                                      mock_extract_email,
                                                      mock_auth_google_sheets,
                                                      mock_load_auth_clients, 
                                                      mock_build):
        # Mocking the authorized clients
        mock_load_auth_clients.return_value = ['authorized@example.com']
        mock_extract_email.return_value = 'authorized@example.com'
        mock_auth_google_sheets.return_value = MagicMock()

        # Mocking Gmail service response
        mock_gmail_service = MagicMock()
        mock_gmail_service.users.return_value.messages.return_value.list.return_value.execute.return_value = {
            'messages': [{'id': '1'}, {'id': '2'}]
        }
        mock_gmail_service.users().messages().list().execute.side_effect = [
            {'payload': {'headers': [{'name': 'Subject', 'value': 'Generate Report'}, {'name': 'From', 'value': 'authorized@example.com'}]}},
            {'payload': {'headers': [{'name': 'Subject', 'value': 'Ignore this'}, {'name': 'From', 'value': 'unauthorized@example.com'}]}}
        ]

        check_email(mock_gmail_service)

        mock_gmail_service.users().messages().list.assert_called_once()
        mock_gmail_service.users().messages().get.assert_called()
        mock_auth_google_sheets.assert_called_once()

   
   
    @patch('src.email_bot.load_authorized_clients')
    @patch('src.email_bot.build')
    def test_check_gmail_no_messages(self, mock_build, mock_load_auth_clients):
        # Mocking the authorized clients
        mock_load_auth_clients.return_value = ['authorized@example.com']

        # Mocking Gmail service with no messages
        mock_gmail_service = MagicMock()
        mock_gmail_service.users.return_value.messages.return_value.list.return_value.execute.return_value = {
            'messages': []
        }

        check_email(mock_gmail_service)

        mock_gmail_service.users.return_value.messages.return_value.list.assert_called_once()
        mock_gmail_service.users.return_value.messages.return_value.get.assert_not_called()

    @patch('src.email_bot.load_authorized_clients')
    @patch('src.email_bot.extract_email_address')
    @patch('src.email_bot.build')
    def test_check_email_unauthorized_clients(self, mock_build, mock_extract_email, 
                                              mock_load_auth_clients):
        # Mocking the authorized clients
        mock_load_auth_clients.return_value = ['authorized@example.com']
        mock_extract_email.return_value = 'unauthorized@example.com'

        # Mocking Gmail service response
        mock_gmail_service = MagicMock()
        mock_gmail_service.users.return_value.messages.return_value.list.return_value.execute.return_value = {
            'messages': [{'id': '1'}]
        }
        mock_gmail_service.users.return_value.messages.return_value.get.return_value.execute.return_value = {
            'payload': {'headers': [{'name': 'Subject', 'value': 'Generate Report'}, {'name': 'From', 'value': 'unauthorized@example.com'}]}
        }

        check_email(mock_gmail_service)

        mock_gmail_service.users.return_value.messages.return_value.list.assert_called_once()
        mock_gmail_service.users.return_value.messages.return_value.get.assert_called_once()
        self.assertFalse(mock_extract_email.return_value in mock_load_auth_clients.return_value)
'''
if __name__ == '__main__':
    unittest.main(verbosity=2)