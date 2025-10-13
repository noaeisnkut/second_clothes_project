provider "aws" {
  region = "us-east-1"
}

# 1️⃣ Use default VPC
data "aws_vpc" "default" {
  default = true
}

data "aws_subnet_ids" "default" {
  vpc_id = data.aws_vpc.default.id
}

# 2️⃣ Security Group allowing HTTP and SSH
resource "aws_security_group" "web_sg" {
  name        = "web_sg"
  description = "Allow HTTP and SSH"
  vpc_id      = data.aws_vpc.default.id

  ingress {
    from_port   = 22
    to_port     = 22
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]
  }

  ingress {
    from_port   = 80
    to_port     = 80
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]
  }

  egress {
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }
}

# 3️⃣ Internet Gateway + Route Table
resource "aws_internet_gateway" "igw" {
  vpc_id = data.aws_vpc.default.id
}

resource "aws_route_table" "rt" {
  vpc_id = data.aws_vpc.default.id
}

resource "aws_route" "default_route" {
  route_table_id         = aws_route_table.rt.id
  destination_cidr_block = "0.0.0.0/0"
  gateway_id             = aws_internet_gateway.igw.id
}

resource "aws_route_table_association" "a" {
  subnet_id      = data.aws_subnet_ids.default.ids[0]
  route_table_id = aws_route_table.rt.id
}

# 4️⃣ EC2 Instance
resource "aws_instance" "web_instance" {
  ami           = "ami-052064a798f08f0d3" # Ubuntu 22.04 LTS in us-east-1 (update per region)
  instance_type = "t2.micro"
  key_name      = "my-key-pair"           # Must match the manually created key
  subnet_id     = data.aws_subnet_ids.default.ids[0]
  security_groups = [aws_security_group.web_sg.name]

  user_data = <<-EOF
#!/bin/bash
sudo apt update -y
sudo apt install -y nginx
sudo systemctl enable nginx
sudo systemctl start nginx
echo "<h1>Hello from Terraform EC2!</h1>" | sudo tee /var/www/html/index.html
EOF

  tags = {
    Name = "WebServer"
  }
}

# 5️⃣ Elastic IP
resource "aws_eip" "web_eip" {}

resource "aws_eip_association" "web_eip_assoc" {
  instance_id   = aws_instance.web_instance.id
  allocation_id = aws_eip.web_eip.id
  depends_on    = [aws_internet_gateway.igw, aws_route_table_association.a]
}

# 6️⃣ Output public IP
output "web_instance_ip" {
  value = aws_eip.web_eip.public_ip
}
