import base64
import os
from email.mime.text import MIMEText
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

app = FastAPI()

class EmailRequest(BaseModel):
    to: str
    subject: str
    message: str

SCOPES = ['https://www.googleapis.com/auth/gmail.send']

def gmail_authenticate():
    creds = None
    if os.path.exists('token.json'):
        creds = Credentials.from_authorized_user_file('token.json', SCOPES)
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file('creds.json', SCOPES)
            creds = flow.run_local_server(port=0)
        with open('token.json', 'w') as token:
            token.write(creds.to_json())
    return build('gmail', 'v1', credentials=creds)

def create_message(to, subject, message_text):
    if subject ==  None:
        subject = ""
    message = MIMEText(message_text)
    message['to'] = to
    message['subject'] = subject
    raw = base64.urlsafe_b64encode(message.as_bytes())
    return {'raw': raw.decode()}

def send_message(service, user_id, message):
    try:
        sent_message = service.users().messages().send(userId=user_id, body=message).execute()
        print(f'Message sent: {sent_message["id"]}')
        return sent_message
    except Exception as e:
        print(f'An error occurred: {e}')
        return None
    
@app.post("/sendmail")
async def send_email(email: EmailRequest):
    try:
        service = gmail_authenticate()
        message = create_message(email.to, email.subject, email.message)
        result = send_message(service, "me", message)
        if result:
            return {"status": "success", "message_id": result["id"]}
        else:
            raise HTTPException(status_code=500, detail="Failed to send email")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


