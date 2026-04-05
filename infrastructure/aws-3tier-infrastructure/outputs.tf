# outputs.tf

output "vpc_id" {
  description = "ID da VPC criada"
  value       = aws_vpc.main.id
}

output "public_subnet_id" {
  description = "ID da subnet pública"
  value       = aws_subnet.public.id
}

output "private_app_subnet_id" {
  description = "ID da subnet privada do app"
  value       = aws_subnet.private_app.id
}

output "private_db_subnet_id" {
  description = "ID da subnet privada do banco"
  value       = aws_subnet.private_db.id
}

output "nat_gateway_id" {
  description = "ID do NAT Gateway"
  value       = aws_nat_gateway.main.id
}

output "bastion_public_ip" {
  description = "Public IP of the Bastion Host"
  value       = aws_instance.bastion.public_ip
}

output "backend_private_ip" {
  description = "Private IP of the Backend EC2"
  value       = aws_instance.backend.private_ip
}