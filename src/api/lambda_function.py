import os
import json
import boto3
from datetime import datetime, timezone
from boto3.dynamodb.conditions import Key

dynamodb = boto3.resource("dynamodb", region_name=os.environ["AWS_REGION_NAME"])
ROSTER_TABLE_NAME = os.environ.get("ROSTER_TABLE_NAME", "tutorflow-student-roster")


def get_cors_headers():
    # common CORS headers for API responses
    return {
        "Access-Control-Allow-Origin": "*",
        "Access-Control-Allow-Methods": "GET, POST, OPTIONS",
        "Access-Control-Allow-Headers": "Content-Type",
    }


def handle_get_students():
    try:
        # fetch roster FIRST — this defines students
        roster_table = dynamodb.Table(ROSTER_TABLE_NAME)
        response = roster_table.scan()
        students = response.get("Items", [])

        # NOW loop through students
        for student in students:
            table_name = student.get("table_name")
            activity_table = dynamodb.Table(table_name)

            # get last practice set date
            try:
                practice_response = activity_table.query(
                    KeyConditionExpression=Key("record_type").eq("practice_set"),
                    ScanIndexForward=False,
                    Limit=1,
                )
                practice_items = practice_response.get("Items", [])
                student["last_practice_date"] = (
                    practice_items[0]["timestamp"] if practice_items else None
                )
            except Exception as e:
                print(f"Error fetching practice set: {str(e)}")
                student["last_practice_date"] = None

            # get last session date
            try:
                session_response = activity_table.query(
                    KeyConditionExpression=Key("record_type").eq("session_notes"),
                    ScanIndexForward=False,
                    Limit=1,
                )
                session_items = session_response.get("Items", [])
                student["last_session_date"] = (
                    session_items[0]["timestamp"] if session_items else None
                )
            except Exception as e:
                print(f"Error fetching session notes: {str(e)}")
                student["last_session_date"] = None

        students.sort(key=lambda x: x["student_name"])

        return {
            "statusCode": 200,
            "headers": get_cors_headers(),
            "body": json.dumps(students),
        }

    except Exception as e:
        print(f"Error fetching students: {str(e)}")
        return {
            "statusCode": 500,
            "headers": get_cors_headers(),
            "body": json.dumps({"message": "Failed to fetch students."}),
        }


def handle_log_session(body):
    # save session notes to activity table
    try:
        data = json.loads(body)

        student_name = data.get("student_name")
        topics_covered = data.get("topics_covered", "general review")
        struggled_with = data.get("struggled_with", "nothing specific")
        notes = data.get("notes", "none")

        if not student_name:
            return {
                "statusCode": 400,
                "headers": get_cors_headers(),
                "body": json.dumps({"message": "Missing required field: student_name"}),
            }

        # look up student in roster to get table name
        roster_table = dynamodb.Table(ROSTER_TABLE_NAME)
        response = roster_table.get_item(Key={"student_name": student_name})
        student = response.get("Item")

        if not student:
            return {
                "statusCode": 404,
                "headers": get_cors_headers(),
                "body": json.dumps(
                    {"message": f"Student {student_name} not found in roster."}
                ),
            }

        # write session notes
        activity_table = dynamodb.Table(student["table_name"])
        activity_table.put_item(
            Item={
                "record_type": "session_notes",
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "topics_covered": topics_covered,
                "struggled_with": struggled_with,
                "notes": notes,
            }
        )
        return {
            "statusCode": 200,
            "headers": get_cors_headers(),
            "body": json.dumps(
                {"message": f"Session notes logged for {student_name}."}
            ),
        }

    except Exception as e:
        print(f"Error logging session notes: {str(e)}")
        return {
            "statusCode": 500,
            "headers": get_cors_headers(),
            "body": json.dumps({"message": "Failed to log session notes."}),
        }


def lambda_handler(event, context):
    # route API requests based on HTTP method and path

    http_method = event.get("httpMethod")
    path = event.get("path")

    if http_method == "OPTIONS":
        return {"statusCode": 200, "headers": get_cors_headers(), "body": ""}

    if http_method == "GET" and path == "/students":
        return handle_get_students()

    if http_method == "POST" and path == "/log-session":
        return handle_log_session(event.get("body", "{}"))

    return {
        "statusCode": 404,
        "headers": get_cors_headers(),
        "body": json.dumps({"message": "Endpoint not found."}),
    }
