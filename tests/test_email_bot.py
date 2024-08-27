import pytest
from unittest.mock import patch, MagicMock
from email_bot import SCOPES, authenticate_gmail

@patch('google.oauth2.credentials.Credentials.from_authorized_user_file')
@patch('googleapiclient.discovery.build')
def test_authenticate_gmail(mock_build, mock_credentials):
    # Arrange
    mock_creds = MagicMock()
    mock_credentials.return_value = mock_creds
    mock_gmail_service = MagicMock()
    mock_build.return_value = mock_gmail_service

    # Act
    gmail_service = authenticate_gmail()

    # Assert
    mock_credentials.assert_called_once_with('token.json', SCOPES)
    mock_build.assert_called_once_with('gmail', 'v1', credentials=mock_creds)
    assert gmail_service == mock_gmail_service