/*
output "webhook_url" {
  description = "Webhook URL to add to workspace notifications"
  value       = aws_api_gateway_deployment.webhook.invoke_url
}
*/

output "webhook_url" {
  description = "for Run Task config"
  value       = aws_lambda_function_url.lambda-url.function_url
}