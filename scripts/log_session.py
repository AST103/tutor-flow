import os
import boto3
from datetime import datetime, timezone

# initialize AWS clients
dynamodb = boto3.resource(
    "dynamodb", region_name=os.environ.get("AWS_REGION_NAME", "us-east-1")
)

STUDENTS = [
    {"name": "Student One", "table": "tutorflow-student-one"},
    {"name": "Student Two", "table": "tutorflow-student-two"},
    {"name": "Student Three", "table": "tutorflow-student-three"},
]


def select_student():
    print("\n TutorFlow Student Session Logger \n")

    for i, student in enumerate(STUDENTS):
        print(f"{i + 1}. {student['name']}")

    while True:
        try:
            choice = int(input("\nSelect a student by number: "))
            if 1 <= choice <= len(STUDENTS):
                return STUDENTS[choice - 1]
            else:
                print("Invalid choice. Please enter a number from the list.")
        except ValueError:
            print("Invalid input. Please enter a number.")


def get_session_details():
    print("\nEnter session details:")

    topics_covered = input("Topics covered: ").strip()
    struggled_with = input("What the student struggled with: ").strip()
    notes = input("Additional notes: ").strip()

    return {
        "topics_covered": topics_covered or "general review",
        "struggled_with": struggled_with or "nothing specific",
        "notes": notes or "none",
    }


def save_session_notes(student, session_details):
    table = dynamodb.Table(student["table"])

    item = {
        "record_type": "session_notes",
        "timestamp": datetime.now(timezone.utc).isoformat(),
        **session_details,
    }

    table.put_item(Item=item)
    return item


def main():

    # select student
    student = select_student()

    # get session details
    session_details = get_session_details()

    # confirm before saving

    print("\nSession Summary:")
    print(f"Student: {student['name']}")
    print(f"Topics Covered: {session_details['topics_covered']}")
    print(f"Struggled With: {session_details['struggled_with']}")
    print(f"Additional Notes: {session_details['notes']}")

    confirm = input("\nSave this session note? (y/n): ").strip().lower()
    if confirm == "y":
        save_session_notes(student, session_details)
        print("\nSession notes saved successfully!")
    else:
        print("\nSession notes not saved.")


if __name__ == "__main__":
    main()
