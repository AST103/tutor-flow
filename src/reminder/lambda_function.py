import os
import json
import boto3

# initialize AWS clients
ses = boto3.client("ses", region_name=os.environ["AWS_REGION_NAME"])


def send_reminder_email(
    student_name, student_email, student_subject, session_day, session_time, zoom_link
):
    # send reminder email via SES

    try:
        if zoom_link:
            zoom_section = f"""
            <div style="background-color: #e8f4fd; padding: 15px; border-radius: 8px; margin: 20px 0;">
                <strong> Join your session: </strong><br/>
                <a href="{zoom_link}" style="color: #0066cc;">{zoom_link}</a>
            </div>
            """
        else:
            zoom_section = """
            <div style="background-color: #f9f9f9; padding: 15px; border-radius: 8px; margin: 20px 0;">
                <strong>In-person session</strong> - see you there!
            </div>
            """

        ses.send_email(
            Source=os.environ["TUTOR_EMAIL"],
            Destination={"ToAddresses": [student_email]},
            Message={
                "Subject": {
                    "Data": f"IMPORTANT: {student_subject} Tutoring Session Tomorrow!"
                },
                "Body": {
                    "Html": {
                        "Data": f"""
                        <html>
                        <body style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto;">
                            <h2>Hi {student_name}!</h2>
                            <p>This is a reminder that you have a {student_subject} session scheduled for tomorrow ({session_day}) at {session_time}.</p>
                            {zoom_section}
                            <hr/>
                            <p>Looking forward to seeing you there! Let me know if you have any questions.</p>
                        </body>
                        </html>
                        """
                    }
                },
            },
        )

    except ses.exceptions.MessageRejected as e:
        print(f"SES MessageRejected error: {str(e)}")
        raise
    except ses.exceptions.MailFromDomainNotVerifiedException as e:
        print(f"SES MailFromDomainNotVerifiedException: {str(e)}")
        raise
    except Exception as e:
        print(f"Error sending reminder email: {str(e)}")
        raise


def lambda_handler(event, context):
    # read student data from event payload
    student_name = event["student_name"]
    student_email = event["student_email"]
    student_subject = event["student_subject"]
    session_day = event["session_day"]
    session_time = event["session_time"]
    zoom_link = event.get("zoom_link", None)

    print(
        f"Sending reminder email to {student_name} for {student_subject} session on {session_day} at {session_time}"
    )

    try:
        send_reminder_email(
            student_name,
            student_email,
            student_subject,
            session_day,
            session_time,
            zoom_link,
        )
        print(f"Successfully sent reminder email to {student_name}")
        return {
            "statusCode": 200,
            "body": json.dumps({"message": f"Reminder email sent to {student_name}."}),
        }
    except Exception as e:
        print(f"Failed to send reminder email to {student_name}: {str(e)}")
        return {
            "statusCode": 500,
            "body": json.dumps(
                {"message": f"Failed to send reminder email to {student_name}."}
            ),
        }
