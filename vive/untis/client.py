import requests
import os
from dotenv import load_dotenv # type: ignore
from datetime import datetime, timedelta

# Load credentials once
load_dotenv()
USERNAME = os.getenv("UNTIS_USERNAME")
PASSWORD = os.getenv("UNTIS_PASSWORD")
SCHOOL = "gym-haan"
BASE_URL = f"https://hepta.webuntis.com/WebUntis/jsonrpc.do?school={SCHOOL}"

SUBJECTS = {
    91: "Informatik",
    96: "English",
    229: "Sport",
    206: "Politik",
    199: "Physik",
    607: "Latein",
    175: "Mathe",
    127: "Geschichte",
    107: "Erdkunde",
    69: "Chemie",
    114: "Religion",
}

def convert_to_time_format(num):
    num_str = str(num).zfill(4)
    return f"{num_str[:2]}:{num_str[2:]}"

def convert_date(date_int):
    date_str = str(date_int)
    return f"{date_str[6:8]}.{date_str[4:6]}.{date_str[0:4]}"

class UntisClient:
    def __init__(self):
        self.session = requests.Session()
        self.person_id = None
        self.logged_in = False

    def login(self):
        payload = {
            "id": "ID_LOGIN",
            "method": "authenticate",
            "params": {
                "user": USERNAME,
                "password": PASSWORD,
                "client": "VIVE FRAMEWORK"
            },
            "jsonrpc": "2.0"
        }
        response = self.session.post(BASE_URL, json=payload)
        data = response.json()

        if "error" in data:
            raise Exception(f"Login failed: {data['error']['message']}")

        self.person_id = data["result"]["personId"]
        self.logged_in = True

    def logout(self):
        if not self.logged_in:
            return
        payload = {
            "id": "ID_LOGOUT",
            "method": "logout",
            "params": {},
            "jsonrpc": "2.0"
        }
        self.session.post(BASE_URL, json=payload)
        self.logged_in = False

    def get_timetable(self, days_ahead=1):
        if not self.logged_in:
            raise Exception("Not logged in!")

        today = datetime.now()
        start_date = int((today + timedelta(days=1)).strftime("%Y%m%d"))
        end_date = int((today + timedelta(days=days_ahead)).strftime("%Y%m%d"))

        payload = {
            "id": "ID_TIMETABLE",
            "method": "getTimetable",
            "params": {
                "id": self.person_id,
                "type": 5, # Student
                "startDate": start_date,
                "endDate": end_date
            },
            "jsonrpc": "2.0"
        }
        response = self.session.post(BASE_URL, json=payload)
        data = response.json()

        if "result" not in data:
            return []

        lessons = []
        for lesson in data["result"]:
            subject_id = lesson['su'][0]['id'] if lesson['su'] else None
            subject = SUBJECTS.get(subject_id, f"Unknown (ID {subject_id})")
            teacher_id = lesson['te'][0]['id'] if lesson['te'] else None
            room_id = lesson['ro'][0]['id'] if lesson['ro'] else None

            lessons.append({
                "date": convert_date(lesson['date']),
                "start_time": convert_to_time_format(lesson['startTime']),
                "end_time": convert_to_time_format(lesson['endTime']),
                "subject": subject,
                "teacher_id": teacher_id,
                "room_id": room_id
            })

        return sorted(lessons, key=lambda x: (x['date'], x['start_time']))

    def __enter__(self):
        self.login()
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        self.logout()

