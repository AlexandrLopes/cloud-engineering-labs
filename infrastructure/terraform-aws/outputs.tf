output "server_public_ip" {
  value       = aws_instance.web_server.public_ip
  description = "Public IP of the EC2 instance"
}

output "s3_bucket_name" {
  value       = aws_s3_bucket.project_bucket.id
  description = "Name of the created S3 bucket"
}