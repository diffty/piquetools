import pickle
import os
import sys
import datetime
import re
import json
import config

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError


SCOPES = ['https://www.googleapis.com/auth/spreadsheets.readonly']


def auth():
    """Shows basic usage of the Sheets API.
    Prints values from a sample spreadsheet.
    """
    creds = None
    # The file token.json stores the user's access and refresh tokens, and is
    # created automatically when the authorization flow completes for the first
    # time.

    if os.path.exists('creds/token.json'):
        creds = Credentials.from_authorized_user_file('creds/token.json', SCOPES)

    # If there are no (valid) credentials available, let the user log in.
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file(
                'creds/credentials.json', SCOPES)
            creds = flow.run_local_server(port=0)

        # Save the credentials for the next run
        with open('creds/token.json', 'w') as token:
            token.write(creds.to_json())
    
    return creds

# http://localhost:60520/?state=C1AIYAfYzCzIuwS57yNY81EvDPrMwA&code=4/0AWtgzh4vJtOa29ZYcHZYQyOGRdFqby0RrfB7Fg63LgKstv1le6cRjBqSc3ow93d-To285Q&scope=https://www.googleapis.com/auth/spreadsheets.readonly

import locale
locale.setlocale(locale.LC_TIME,'')

import datetime

def main():
    creds = auth()

    curr_parse_day = None
    curr_parse_month = None
    curr_parse_time = None

    try:
        service = build('sheets', 'v4', credentials=creds)

        # The ID and range of a sample spreadsheet.
        SAMPLE_SPREADSHEET_ID = config.SHEET_ID
        SAMPLE_RANGE_NAME = "'Semaine 23/01-29/01'!A:C"

        # Call the Sheets API
        sheet = service.spreadsheets()
        result = sheet.values().get(spreadsheetId=SAMPLE_SPREADSHEET_ID,
                                    range=SAMPLE_RANGE_NAME).execute()
        values = result.get('values', [])

        for row in values:
            curr_parse_interval = None

            if not row[0]:
                continue
            
            date_reg_res = re.search(r"(\w+) (\d*) (\w+)", row[0], re.I)
            interval_reg_res = re.search(r"(\d{1,2}):(\d{1,2})-(\d{1,2}):(\d{1,2})", row[0], re.I)
            
            if date_reg_res:
                try:
                    parsed_date = datetime.datetime.strptime(row[0], "%A %d %B")
                    curr_parse_day = parsed_date.day
                    curr_parse_month = parsed_date.month

                except ValueError:
                    pass

            elif interval_reg_res:
                curr_parse_interval = interval_reg_res.groups()
            
            if curr_parse_interval:
                if len(row) > 1:
                    title = row[1]
                    streamer = row[2]
                    print(f"{curr_parse_day}/{curr_parse_month}: {curr_parse_interval[0]}:{curr_parse_interval[1]} -> {curr_parse_interval[2]}:{curr_parse_interval[3]}: {title} ({streamer})")

    except HttpError as err:
        print(err)


if __name__ == '__main__':
    main()
