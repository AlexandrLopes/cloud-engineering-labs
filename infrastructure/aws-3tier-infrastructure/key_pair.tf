resource "aws_key_pair" "main" {
  key_name   = "lab-key"
  public_key = file(var.ssh_public_key_path)
}
