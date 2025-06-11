import json
from vive.modules.untis.client import UntisClient

def test_get_raw_time_table():
    client = UntisClient()
    client.login()
    raw = client.get_raw_data()
    print(raw)

def test_get_time_table():
    client = UntisClient()
    client.login()
    timetable = client.get_timetable(days_ahead=1)

    for entry in timetable:
        start_time = entry.get('start_time', 'Unknown Start Time')
        end_time = entry.get('end_time', 'N/A')
        subject = entry.get('subject', 'Unknown Subject')
        teacher_id = entry.get('teacher_id', 'Unknown Teacher')
        room_id = entry.get('room_id', 'Unknown Room')
        print(f"{start_time} - {end_time}: {subject} (Teacher ID: {teacher_id}) in Room ID: {room_id}")

if __name__ == "__main__":
    test_get_raw_time_table()
    print("-------------------------------")
    test_get_time_table()