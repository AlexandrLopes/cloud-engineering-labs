resource "aws_key_pair" "main" {
  key_name   = "lab-key"
  public_key = file("/Users/alexandrewilliam/.ssh/three-tier-key.pub")
}
