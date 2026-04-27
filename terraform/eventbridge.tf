# Create eventbridge rule to trigger lambda function on schedule

resource "aws_cloudwatch_event_rule" "practice_set_schedule" {
  for_each = { for student in var.students : student.name => student }

  name                = "tutorflow-practice-${lower(replace(each.key, " ", "-"))}"
  description         = "Weekly practice set for ${each.value.name}"
  schedule_expression = "cron(0 20 ? * SUN *)" # every Sunday at 8 PM UTC (3 PM EST)
}

resource "aws_cloudwatch_event_rule" "reminder_schedule" {
  for_each = { for student in var.students : student.name => student }

  name        = "tutorflow-reminder-${lower(replace(each.key, " ", "-"))}"
  description = "Session reminder for ${each.value.name}"
  # EventBridge cron is evaluated in UTC; this assumes reminder_time is provided in ET and shifts by +5 hours.
  schedule_expression = "cron(${tonumber(split(":", each.value.reminder_time)[1])} ${(tonumber(split(":", each.value.reminder_time)[0]) + 5) % 24} ? * ${upper(substr(each.value.reminder_day, 0, 3))} *)"
}

# Create event bridge target to link rule to lambda function
resource "aws_cloudwatch_event_target" "practice_set_target" {
  for_each = { for student in var.students : student.name => student }

  rule      = aws_cloudwatch_event_rule.practice_set_schedule[each.key].name
  target_id = "practice-set-${lower(replace(each.key, " ", "-"))}"
  arn       = aws_lambda_function.practice_set.arn

  input = jsonencode({
    student_name    = each.value.name
    student_email   = each.value.email
    student_subject = each.value.subject
    table_name      = "tutorflow-${lower(replace(each.key, " ", "-"))}"
  })
}

resource "aws_cloudwatch_event_target" "reminder_target" {
  for_each = { for student in var.students : student.name => student }

  rule      = aws_cloudwatch_event_rule.reminder_schedule[each.key].name
  target_id = "reminder-${lower(replace(each.key, " ", "-"))}"
  arn       = aws_lambda_function.reminder.arn

  input = jsonencode({
    student_name    = each.value.name
    student_email   = each.value.email
    student_subject = each.value.subject
    session_day     = each.value.session_day
    session_time    = each.value.session_time
    zoom_link       = each.value.zoom_link != null ? each.value.zoom_link : ""
  })
}

# allow event bridge to invoke lambda
resource "aws_lambda_permission" "allow_eventbridge_practice" {
  statement_id  = "AllowExecutionFromEventBridgePractice"
  action        = "lambda:InvokeFunction"
  function_name = aws_lambda_function.practice_set.function_name
  principal     = "events.amazonaws.com"
}

resource "aws_lambda_permission" "allow_eventbridge_reminder" {
  statement_id  = "AllowExecutionFromEventBridgeReminder"
  action        = "lambda:InvokeFunction"
  function_name = aws_lambda_function.reminder.function_name
  principal     = "events.amazonaws.com"
}
