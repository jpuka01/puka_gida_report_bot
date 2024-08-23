TODO:
- Automatic update on .csv files
- Email is sent on-demand (upon request via sending an email to the server)
- Include "robert@pukacreations.com" and "sezer@pukacreations.com" to authorized_clients.json
- Test the GPT analysis
- What if Google Sheets fails? Ensure robustness
- Delete synthetic data later (Is synthetic data even being used?)
- Update and fix OpenAI (gpt3.5 --> gpt4o) + service account
- Better prompt engineering
- Print synthetic data
- Comment out gpt (if possible) to save tokens
- Simplify all json, config, and other key files for simplicity 
- Note on backend speed performance
- Find all edge cases and testing, testing, testing (unit tests)!!!
- Add brief function contract
- Which model is best suited for this program?
- Note project uses a pipeline
- License the project
- Should I include unit tests or gitignore?
- Create a webhook using Flask
- To test: PS E:\VSCode\Puka Survey Report> python -m unittest -v tests.test_email_bot

FUTURE WORKS:
- Different endpoint options (i.e. various email companies (Yahoo, Outlook, etc),
  text (IMessage, Whatsapp, etc))
- Ease for client to upload survey file to analyze and customization options (i.e.
  prompt)
- More security features (either for individual or business)
- Tiers (free and paid options)?
    - How to make which features are enabled
- Who to market, where to market, why to market, how to market, what to market,
  when to market?
- Use pub/sub for gmail notifications
- Organize the data better into three ways (doner, restaurant, and markets) +
  add explicitly written words into the email report

  /////////////////////////////////////////////////////////////////////////////

  To achieve both functionalities using push notifications for the trigger word and a scheduler for the 29th, you can use Gmail's push notifications along with `APScheduler`. Gmail's push notifications can be set up using Google Cloud Pub/Sub, which has a free tier that should be sufficient for low to moderate usage.

### Steps to Implement

1. **Set up Google Cloud Pub/Sub**:
   - Create a Google Cloud project.
   - Enable the Pub/Sub API.
   - Create a Pub/Sub topic and subscription.
   - Configure Gmail to send push notifications to the Pub/Sub topic.

2. **Handle Pub/Sub messages**:
   - Create a webhook endpoint to receive Pub/Sub messages.
   - Process the messages to check for the trigger word.

3. **Schedule the report generation**:
   - Use `APScheduler` to schedule the report generation on the 29th of every month.

### Implementation

#### 1. Set up Google Cloud Pub/Sub
Follow the [Google Cloud Pub/Sub documentation](https://cloud.google.com/pubsub/docs/quickstart-console) to set up a Pub/Sub topic and subscription.

#### 2. Configure Gmail for Push Notifications
Follow the [Gmail API documentation](https://developers.google.com/gmail/api/guides/push) to configure push notifications.

#### 3. Handle Pub/Sub Messages and Schedule Reports

```python
from flask import Flask, request
from apscheduler.schedulers.background import BackgroundScheduler
from googleapiclient.discovery import build
from google.oauth2.credentials import Credentials
import json
import base64
import time

app = Flask(__name__)

# Initialize the Gmail API service
def get_gmail_service():
    creds = Credentials.from_authorized_user_file('token.json', SCOPES)
    return build('gmail', 'v1', credentials=creds)

# Function to retrieve the 10 most recent emails
def retrieve_emails():
    gmail_service = get_gmail_service()
    results = gmail_service.users().messages().list(userId='me', labelIds=['INBOX'], maxResults=10).execute()
    messages = results.get('messages', [])
    
    # Process the emails as needed
    for message in messages:
        msg = gmail_service.users().messages().get(userId='me', id=message['id']).execute()
        print(f"Email snippet: {msg['snippet']}")

# Webhook endpoint to receive Pub/Sub messages
@app.route('/pubsub', methods=['POST'])
def pubsub():
    envelope = request.get_json()
    if not envelope:
        return 'Bad Request: No JSON payload received', 400

    pubsub_message = envelope['message']
    message_data = base64.b64decode(pubsub_message['data']).decode('utf-8')
    message_json = json.loads(message_data)

    # Check for the trigger word in the message
    if 'trigger message' in message_json.get('snippet', ''):
        print("Trigger message found. Retrieving emails...")
        retrieve_emails()

    return 'OK', 200

# Set up the scheduler
scheduler = BackgroundScheduler()
scheduler.add_job(retrieve_emails, 'cron', day=29, hour=0, minute=0)  # Run at midnight on the 29th
scheduler.start()

# Keep the script running
if __name__ == '__main__':
    try:
        app.run(port=8080)  # Run the Flask app to handle Pub/Sub messages
    except (KeyboardInterrupt, SystemExit):
        scheduler.shutdown()
```

### Notes
- **Flask App**: The Flask app handles incoming Pub/Sub messages.
- **Push Notifications**: Gmail sends push notifications to the Pub/Sub topic, which are then forwarded to the Flask app.
- **Scheduler**: `APScheduler` schedules the report generation on the 29th of every month.
- **Free Tier**: Google Cloud Pub/Sub has a free tier that should be sufficient for low to moderate usage.

This setup ensures that you can handle both trigger-based and scheduled reports efficiently while keeping costs low.