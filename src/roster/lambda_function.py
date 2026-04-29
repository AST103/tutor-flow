import os
import json
import boto3

dynamodb = boto3.resource("dynamodb", region_name=os.environ["AWS_REGION_NAME"])
ROSTER_TABLE_NAME = os.environ.get("ROSTER_TABLE_NAME", "tutorflow-student-roster")


def lambda_handler(event, context):

    # this function will populate the roster table with student data on deployment

    print("Populating roster table with student data...")

    try:
        students = json.loads(os.environ["STUDENTS_JSON"])
        table = dynamodb.Table(ROSTER_TABLE_NAME)

        desired_names = {student["name"] for student in students}

        # Delete students that are no longer in the desired list
        deleted = 0
        scan_kwargs = {}
        while True:
            response = table.scan(**scan_kwargs)
            for item in response.get("Items", []):
                existing_name = item.get("student_name")
                if existing_name and existing_name not in desired_names:
                    table.delete_item(Key={"student_name": existing_name})
                    deleted += 1

            last_key = response.get("LastEvaluatedKey")
            if not last_key:
                break
            scan_kwargs["ExclusiveStartKey"] = last_key

        for student in students:
            table.put_item(
                Item={
                    "student_name": student["name"],
                    "subject": student["subject"],
                    "session_day": student["session_day"],
                    "session_time": student["session_time"],
                    "reminder_day": student.get("reminder_day", ""),
                    "reminder_time": student.get("reminder_time", ""),
                    "zoom_link": student.get("zoom_link", ""),
                    "email": student["email"],
                    "table_name": f"tutorflow-{student['name'].lower().replace(' ', '-')}",
                }
            )

        if deleted:
            print(f"Deleted {deleted} students removed from config.")
        return {
            "statusCode": 200,
            "body": json.dumps({"message": "Roster table populated successfully."}),
        }

    except Exception as e:
        print(f"Error populating roster table: {str(e)}")
        return {
            "statusCode": 500,
            "body": json.dumps({"message": "Failed to populate roster table."}),
        }
