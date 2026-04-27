# outputs is important or else we'd have to go to AWS console to check for
# the created resoruces and their properties (like ARNs, names, etc.) which is a pain

output "dynamodb_table_names" {
  description = "DynamoDB table names for each student"
  value       = { for k, v in aws_dynamodb_table.student_tables : k => v.name }
}

output "practice_set_lambda_names" {
  description = "Practice set Lambda function name"
  value       = aws_lambda_function.practice_set.function_name
}

output "reminder_lambda_names" {
  description = "Reminder Lambda function name"
  value       = aws_lambda_function.reminder.function_name
}

output "eventbridge_practice_rules" {
  description = "EventBridge rule names for practice set schedules for each student"
  value       = { for k, v in aws_cloudwatch_event_rule.practice_set_schedule : k => v.name }
}

output "eventbridge_reminder_rules" {
  description = "EventBridge rule names for reminder schedules for each student"
  value       = { for k, v in aws_cloudwatch_event_rule.reminder_schedule : k => v.name }
}

output "deployment_summary" {
  description = "Summary of deployed resources"
  value       = "Deployed successfully - ${length(var.students)} students onboarded"
}

output "api_url" {
    description = "API Gateway URL for frontend to call"
    value       = aws_api_gateway_stage.prod.invoke_url
}