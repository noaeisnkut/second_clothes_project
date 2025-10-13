# 1️⃣ שולף את ה-VPC וה-Subnet ברירת המחדל
data "aws_vpc" "default" {
  default = true
}

data "aws_subnet_ids" "default" {
  vpc_id = data.aws_vpc.default.id
}

# 2️⃣ Security Group שמאפשר HTTP
resource "aws_security_group" "docker_sg" {
  name        = "docker_sg"
  description = "Allow HTTP traffic"
  vpc_id      = data.aws_vpc.default.id

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

  tags = {
    Name = "docker_sg"
  }
}

# 3️⃣ Internet Gateway
resource "aws_internet_gateway" "igw" {
  vpc_id = data.aws_vpc.default.id

  tags = {
    Name = "default-igw"
  }
}

# 4️⃣ Route Table + Route
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

# 5️⃣ EC2 Instance עם Docker + Git
resource "aws_instance" "docker_instance" {
  ami           = "ami-052064a798f08f0d3"
  instance_type = "t2.micro"
  key_name      = "my-key-pair"
  subnet_id     = data.aws_subnet_ids.default.ids[0]
  security_groups = [aws_security_group.docker_sg.name]

  user_data = <<-EOF
#!/bin/bash
sudo apt update -y
sudo apt install -y docker.io git -y
sudo systemctl enable docker
sudo systemctl start docker

mkdir -p /home/ubuntu/docker
cd /home/ubuntu/docker

# משיכת הקבצים מ-GitHub
git clone https://github.com/<your-username>/<repo>.git .

sudo docker build -t my-nginx .
sudo docker run -d -p 80:80 my-nginx
EOF

  tags = {
    Name = "DockerNginx"
  }
}

# 6️⃣ Elastic IP + Association
resource "aws_eip" "docker_eip" {
}

resource "aws_eip_association" "docker_eip_assoc" {
  instance_id   = aws_instance.docker_instance.id
  allocation_id = aws_eip.docker_eip.id

  depends_on = [
    aws_internet_gateway.igw,
    aws_route_table_association.a
  ]
}

# 7️⃣ Output: כתובת ה-IP הציבורית
output "docker_instance_ip" {
  value = aws_eip.docker_eip.public_ip
}
