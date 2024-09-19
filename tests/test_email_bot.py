# email_bot_test.py

import unittest
from src.email_bot import authenticate_gmail, check_email
from unittest.mock import patch, Mock, mock_open
from google.oauth2.credentials import Credentials


class TestEmailBot(unittest.TestCase):
    @patch('src.email_bot.os.path.exists')
    @patch('src.email_bot.Credentials.from_authorized_user_file')
    @patch('src.email_bot.build')
    def test_authenticate_gmail(self, mock_build, mock_creds, mock_exists):
        mock_exists.return_value = True
        mock_creds.return_value = Mock(expired=False)
        mock_build.return_value = 'gmail_service'

        service = authenticate_gmail()
        self.assertEqual(service, 'gmail_service')


    @patch('src.email_bot.os.path.exists')
    @patch('src.email_bot.Credentials.from_authorized_user_file')
    @patch('src.email_bot.build')
    @patch('src.email_bot.Request')
    def test_authenticate_gmail_refresh_token(self, mock_request, mock_build, mock_creds, mock_exists):
        mock_exists.return_value = True
        mock_creds.return_value = Mock(expired=True, refresh_token=True)
        mock_creds.return_value.to_json.return_value = '{"token": "mock_token"}'
        mock_build.return_value = 'gmail_service'

        service = authenticate_gmail()
        self.assertEqual(service, 'gmail_service')
        mock_creds.return_value.refresh.assert_called_once_with(mock_request())

    @patch('src.email_bot.os.path.exists')
    @patch('src.email_bot.InstalledAppFlow.from_client_secrets_file')
    @patch('src.email_bot.build')
    def test_authenticate_gmail_new_token(self, mock_build, mock_flow, mock_exists):
        mock_exists.side_effect = [False, True]
        mock_flow.return_value.run_local_server.return_value = Mock()
        mock_flow.return_value.run_local_server.return_value.to_json.return_value = '{"token": "mock_token"}'
        mock_build.return_value = 'gmail_service'

        service = authenticate_gmail()
        self.assertEqual(service, 'gmail_service')
        
    creds = Credentials.from_authorized_user_file('src/credentials.json')
    #print(creds)
r'''
    @patch('src.email_bot.authenticate_gmail')
    @patch('src.email_bot.load_authorized_clients')
    @patch('src.email_bot.build')
    @patch('builtins.open', new_callable=mock_open, read_data='{"installed": {"client_id": "mock_client_id", "client_secret": "mock_client_secret", "auth_uri": "https://accounts.google.com/o/oauth2/auth", "token_uri": "https://oauth2.googleapis.com/token", "auth_provider_x509_cert_url": "https://www.googleapis.com/oauth2/v1/certs", "redirect_uris": ["http://localhost"]}}')
    def test_check_email(self, mock_open, mock_build, mock_load_clients, mock_auth_gmail):
        mock_auth_gmail.return_value = Mock()
        mock_load_clients.return_value = ['authorized@example.com']
        mock_build.return_value.users().messages().list().execute.return_value = {
            'messages': [{'id': '1'}]
        }
        mock_build.return_value.users().messages().get().execute.return_value = {
            'payload': {'headers': [{'name': 'Subject', 'value': 'Generate Report'}, {'name': 'From', 'value': 'authorized@example.com'}]}
        }

        gmail_service = authenticate_gmail()
        check_email(gmail_service)
        # SWITCH TO CREDENTIALS FROM TOKEn

    @patch('builtins.open', new_callable=mock_open, read_data='{"AUTHORIZED_CLIENTS": ["authorized@example.com"]}')
    def test_load_authorized_clients(self, mock_file):
        clients = load_authorized_clients()
        self.assertEqual(clients, ['authorized@example.com'])

    def test_extract_email_address(self):
        email = extract_email_address('John Doe <john.doe@example.com>')
        self.assertEqual(email, 'john.doe@example.com')

    @patch('src.email_bot.os.path.exists')
    @patch('src.email_bot.Credentials.from_authorized_user_file')
    @patch('src.email_bot.build')
    def test_authenticate_google_sheets(self, mock_build, mock_creds, mock_exists):
        mock_exists.return_value = True
        mock_creds.return_value = Mock()
        mock_build.return_value = 'sheets_service'

        service = authenticate_google_sheets()
        self.assertEqual(service, 'sheets_service')
'''
if __name__ == '__main__':
    unittest.main(verbosity=2)