import sys
import jwt
import http.client
import datetime
import json
import os
import pytz
import argparse

# Given a Zoom meeting ID, get participant listing for all instances

parser = argparse.ArgumentParser(description='Zoom meeting participant report')
parser.add_argument('meetingId', metavar='meetingId', type=int,
                    help='Zoom meeting ID')

args = parser.parse_args()
meetingId = args.meetingId

# Then get API Key, API Secret and insert below
api_key = os.getenv('ZOOM_API_KEY')
api_sec = os.getenv('ZOOM_API_SECRET')

payload = {
    'iss': api_key,
    'exp': datetime.datetime.now(pytz.timezone('US/Eastern')) + datetime.timedelta(hours=1)
}

jwt_encoded = jwt.encode(payload, api_sec, algorithm="HS256")


conn = http.client.HTTPSConnection("api.zoom.us")
headers = {
    'authorization': "Bearer %s" % jwt_encoded,
    'content-type': "application/json"
}

conn.request("GET", f"/v2/past_meetings/{meetingId}/instances", headers=headers)
res = conn.getresponse()
response_string = res.read().decode('utf-8')
response_obj = json.loads(response_string)
meetingInstances = response_obj['meetings']

# Sort by meeting start time
meetingInstances.sort(key=lambda x: x['start_time'], reverse=False)

for m in meetingInstances:

    meeting_start_time_object = datetime.datetime.strptime(m['start_time'], '%Y-%m-%dT%H:%M:%SZ').replace(tzinfo=datetime.timezone.utc).astimezone()

    print(f"\n\nMeeting start: {meeting_start_time_object.strftime('%m/%d/%Y, %-I:%M:%S %p')}")

    #conn.request("GET", f"/v2/past_meetings/{m['uuid']}/participants?page_size=300", headers=headers)
    conn.request("GET", f"/v2/report/meetings/{m['uuid']}/participants", headers=headers)

    res = conn.getresponse()
    response_string = res.read().decode('utf-8')
    response_obj = json.loads(response_string)
    if "participants" not in response_obj:
        print(f"   No participants found")
        print(response_obj)
        continue

    participants = response_obj['participants']
    # Sort participants by name
    participants.sort(key=lambda x: (x['name'], x['join_time']), reverse=False)

    for p in participants:
        start_time_obj = datetime.datetime.strptime(p['join_time'], '%Y-%m-%dT%H:%M:%SZ').replace(tzinfo=datetime.timezone.utc).astimezone()
        leave_time_obj = datetime.datetime.strptime(p['leave_time'], '%Y-%m-%dT%H:%M:%SZ').replace(tzinfo=datetime.timezone.utc).astimezone()
        duration = round((leave_time_obj-start_time_obj).total_seconds() / 60, 1)

        print(f"   {p['name']}    {duration} minutes:  {start_time_obj.strftime('%-I:%M:%S %p')} to {leave_time_obj.strftime('%-I:%M:%S %p')}")


