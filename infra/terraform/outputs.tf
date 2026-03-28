output "ecs_cluster_name" {
  value       = aws_ecs_cluster.overbuild.name
  description = "Name of ECS cluster"
}

output "ecs_service_name" {
  value       = aws_ecs_service.overbuild.name
  description = "Name of ECS service"
}

output "task_definition_arn" {
  value       = aws_ecs_task_definition.overbuild.arn
  description = "ECS task definition ARN"
}

