import os
import datetime
import re
import config
import copy

from typing import List

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


import locale
locale.setlocale(locale.LC_TIME,'')

import datetime


def get_timetable_from_sheet(sheet_id, sheet_name):
    creds = auth()

    curr_parse_day = None
    curr_parse_month = None

    interval_list = []
    curr_interval = None

    try:
        service = build('sheets', 'v4', credentials=creds)

        # Call the Sheets API
        sheet = service.spreadsheets()
        result = sheet.values().get(spreadsheetId=sheet_id,
                                    range=f"'{sheet_name}'!A:D").execute()

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
                    if len(row) >= 4:
                        category = row[3]
                    else:
                        category = "Discussions"

                    start_date = datetime.datetime(year=datetime.datetime.now().year, month=int(curr_parse_month), day=int(curr_parse_day), hour=int(curr_parse_interval[0]), minute=int(curr_parse_interval[1]))
                    delta_date = datetime.timedelta(hours=int(curr_parse_interval[2])-int(curr_parse_interval[0]), minutes=int(curr_parse_interval[3])-int(curr_parse_interval[1]))

                    if delta_date.total_seconds() < 0:
                        delta_date += datetime.timedelta(days=1)

                    if curr_interval is not None and title != curr_interval["title"] and streamer != curr_interval["streamer"]:
                        interval_list.append(curr_interval)
                        curr_interval = None

                    if curr_interval is None:
                        curr_interval = {
                            "start": None,
                            "end": None,
                            "title": None,
                            "streamer": None,
                            "category": None,
                        }

                    if curr_interval["start"] is None:
                        curr_interval["start"] = start_date
                        curr_interval["end"] = copy.deepcopy(start_date)
                        curr_interval["title"] = title
                        curr_interval["streamer"] = streamer
                        curr_interval["category"] = category

                    curr_interval["end"] += delta_date
                else:
                    if curr_interval is not None:
                        interval_list.append(curr_interval)
                        curr_interval = None

    except HttpError as err:
        print(err)

    if curr_interval is not None:
        interval_list.append(curr_interval)

    return interval_list


def find_current_show(t: datetime.datetime) -> dict:
    timetable = get_timetable_from_sheet(config.SHEET_ID, 'Semaine 30/01-05/02')
    for show in timetable:
        if show["start"] < t and show["end"] > t:
            return show


def find_next_show(t: datetime.datetime) -> dict:
    timetable = get_timetable_from_sheet(config.SHEET_ID, 'Semaine 30/01-05/02')
    for i, show in enumerate(timetable):
        if show["start"] > t:
            return timetable[i]


def time_before_show(show: dict) -> float:
        return (show["start"] - datetime.datetime.now()).total_seconds()


if __name__ == '__main__':
    timetable = get_timetable_from_sheet(config.SHEET_ID, 'Semaine 30/01-05/02')
    t = datetime.datetime(year=2023, month=1, day=30, hour=4, minute=14)
    print(find_current_show(t))
    next_show = find_next_show(datetime.datetime.now())
    print(next_show)
    print(time_before_show(next_show))
