# Comprobación opcional: ¿arranca Floci una instancia EC2 como contenedor en este portátil?
#   docker compose -f ../docker-compose.yml run --rm -v "$PWD:/work" -w /work terraform init
#   docker compose -f ../docker-compose.yml run --rm -v "$PWD:/work" -w /work terraform apply
#   docker ps --filter label=io.floci.service=ec2      # debe aparecer el contenedor de la instancia
resource "aws_security_group" "intranet" {
  name        = "intranet"
  description = "Servidor de intranet"

  ingress {
    description = "Web interna"
    from_port   = 80
    to_port     = 80
    protocol    = "tcp"
    cidr_blocks = ["172.16.0.0/12"]
  }
}

resource "aws_instance" "intranet" {
  ami                    = "ami-ubuntu2204"
  instance_type          = "t3.micro"
  vpc_security_group_ids = [aws_security_group.intranet.id]
  user_data              = <<-SH
    #!/bin/sh
    echo "intranet de la empresa ficticia" > /tmp/intranet.txt
  SH
  tags = { Name = "intranet" }
}

output "ip_privada" {
  value = aws_instance.intranet.private_ip
}
