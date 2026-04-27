# Create a CloudWatch dashboard to monitor Lambda function invocations and errors

resource "aws_cloudwatch_dashboard" "tutorflow" {
  dashboard_name = "TutorFlow-Pipeline"

  dashboard_body = jsonencode({
    widgets = [
      {
        type   = "metric"
        x      = 0
        y      = 0
        width  = 12
        height = 6
        properties = {
          title  = "Practice Set Lambda"
          view   = "timeSeries"
          region = var.aws_region
          metrics = [
            ["AWS/Lambda", "Invocations", "FunctionName", aws_lambda_function.practice_set.function_name],
            ["AWS/Lambda", "Errors", "FunctionName", aws_lambda_function.practice_set.function_name]
          ]
          period = 300
          stat   = "Sum"
        }
      },
      {
        type   = "metric"
        x      = 12
        y      = 0
        width  = 12
        height = 6
        properties = {
          title  = "Reminder Lambda"
          view   = "timeSeries"
          region = var.aws_region
          metrics = [
            ["AWS/Lambda", "Invocations", "FunctionName", aws_lambda_function.reminder.function_name],
            ["AWS/Lambda", "Errors", "FunctionName", aws_lambda_function.reminder.function_name]
          ]
          period = 300
          stat   = "Sum"
        }
      },
      {
        type   = "metric"
        x      = 0
        y      = 6
        width  = 12
        height = 6
        properties = {
          title  = "Practice Set Lambda Duration"
          view   = "timeSeries"
          region = var.aws_region
          metrics = [
            ["AWS/Lambda", "Duration", "FunctionName", aws_lambda_function.practice_set.function_name]
          ]
          period = 300
          stat   = "Average"
        }
      },
      {
        type   = "metric"
        x      = 12
        y      = 6
        width  = 12
        height = 6
        properties = {
          title  = "Reminder Lambda Duration"
          view   = "timeSeries"
          region = var.aws_region
          metrics = [
            ["AWS/Lambda", "Duration", "FunctionName", aws_lambda_function.reminder.function_name]
          ]
          period = 300
          stat   = "Average"
        }
      },
      {
        type   = "alarm"
        x      = 0
        y      = 12
        width  = 24
        height = 3
        properties = {
          title = "Active Alarms"
          alarms = [
            aws_cloudwatch_metric_alarm.practice_set_errors.arn,
            aws_cloudwatch_metric_alarm.reminder_errors.arn
          ]
        }
      }
    ]
  })
}

# alarm if practice set lambda has any errors
resource "aws_cloudwatch_metric_alarm" "practice_set_errors" {
  alarm_name          = "tutorflow-practice-set-errors"
  comparison_operator = "GreaterThanThreshold"
  evaluation_periods  = 1
  metric_name         = "Errors"
  namespace           = "AWS/Lambda"
  period              = 300
  statistic           = "Sum"
  threshold           = 0
  alarm_description   = "Alarm if there are any errors in the practice set Lambda function"

  dimensions = {
    FunctionName = aws_lambda_function.practice_set.function_name
  }
}

# alarm if reminder lambda has any errors
resource "aws_cloudwatch_metric_alarm" "reminder_errors" {
  alarm_name          = "tutorflow-reminder-errors"
  comparison_operator = "GreaterThanThreshold"
  evaluation_periods  = 1
  metric_name         = "Errors"
  namespace           = "AWS/Lambda"
  period              = 300
  statistic           = "Sum"
  threshold           = 0
  alarm_description   = "Alarm if there are any errors in the reminder Lambda function"

  dimensions = {
    FunctionName = aws_lambda_function.reminder.function_name
  }
}
