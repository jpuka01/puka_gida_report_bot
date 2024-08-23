from unittest.mock import patch, MagicMock
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
    # check_email,
    # scheduler,
    # load_authorized_clients,
    # extract_email_address,
    # authenticate_google_sheets
)

'''
Test suite for the email_bot module.
    
This class contains unit tests for the functions in the email_bot module. It 
uses the unittest framework and mocks external dependencies to ensure that the 
tests are isolated and reliable.
'''
class TestEmailBot(unittest.TestCase):
    
    '''
    Test the authenticate_gmail function.

    This test mocks the os.path.exists, Credentials.from_authorized_user_file,
    and build functions to simulate the presence of the token.json file and
    the creation of the Gmail service. It verifies that the authenticate_gmail
    function returns a valid Gmail service object.
        
    Args:
    - mock_build (MagicMock): Mock for the googleapiclient.discovery.build 
      function.
    - mock_from_authorized_user_file (MagicMock): Mock for the 
      Credentials.from_authorized_user_file function.
    - mock_path_exists (MagicMock): Mock for the os.path.exists function.
    '''
    @patch('os.path.exists')
    @patch('src.email_bot.Credentials.from_authorized_user_file')
    @patch('src.email_bot.build')
    def test_authenticate_gmail(self, mock_build, 
                                mock_from_authorized_user_file, 
                                mock_path_exists):
        # Mock the os.path.exists to return True
        mock_path_exists.return_value = True

        # Mock the Credentials.from_authorized_user_file to return a mock 
        # credentials object
        mock_creds = MagicMock()
        mock_from_authorized_user_file.return_value = mock_creds

        # Mock the build function to return a mock Gmail service object
        mock_gmail_service = MagicMock()
        mock_build.return_value = mock_gmail_service

        # Call the function
        result = authenticate_gmail()

        # Assertions
        mock_path_exists.assert_called_once_with('token.json')
        mock_from_authorized_user_file.assert_called_once_with('token.json', 
                                                               scopes=SCOPES)
        mock_build.assert_called_once_with('gmail', 'v1', 
                                           credentials=mock_creds)
        self.assertEqual(result, mock_gmail_service)

    @patch('os.path.exists')
    def test_authenticate_gmail_token_not_found(self, mock_path_exists):
        # Mock the os.path.exists to return False
        mock_path_exists.return_value = False

        # Call the function
        result = authenticate_gmail()

        # Assertions
        mock_path_exists.assert_called_once_with('token.json')
        self.assertIsNone(result)

if __name__ == '__main__':
    unittest.main(verbosity=2)