# La cuenta AWS de la empresa ficticia, tal como la dejó «el equipo anterior».
# En el E2 la inventarías, en el E7 auditas sus permisos y en el E8 los corriges. Tiene fallos a propósito.

# --- Almacenamiento ---------------------------------------------------------------------

# Copias de seguridad de la empresa.
resource "aws_s3_bucket" "copias" {
  bucket = "{copias}"
}

resource "aws_s3_bucket_public_access_block" "copias" {
  bucket                  = aws_s3_bucket.copias.id
  block_public_acls       = false
  block_public_policy     = false
  ignore_public_acls      = false
  restrict_public_buckets = false
}

# Informes que prepara el becario.
resource "aws_s3_bucket" "informes" {
  bucket = "{informes}"
}

resource "aws_s3_object" "informe" {
  bucket  = aws_s3_bucket.informes.id
  key     = "informe-semanal.txt"
  content = "Informe semanal: sin incidencias graves.\n"
}

# Lo que nadie más que dirección debería leer.
resource "aws_s3_bucket" "secretos" {
  bucket = "{secretos}"
}

resource "aws_s3_object" "nominas" {
  bucket  = aws_s3_bucket.secretos.id
  key     = "nominas.txt"
  content = "Nóminas del trimestre: confidencial.\n"
}

# --- Identidades ------------------------------------------------------------------------

# Operaciones administra el servidor web (EC2). Puede hacerlo todo «para no perder tiempo».
resource "aws_iam_user" "operaciones" {
  name = "{operaciones}"
}

resource "aws_iam_user_policy" "operaciones" {
  name = "operaciones-todo"
  user = aws_iam_user.operaciones.name
  policy = jsonencode({
    Version   = "2012-10-17"
    Statement = [{ Effect = "Allow", Action = "*", Resource = "*" }]
  })
}

# El becario lee los informes y «puede ajustarse sus propios permisos si le falta algo».
resource "aws_iam_user" "becario" {
  name = "{becario}"
}

resource "aws_iam_user_policy" "becario" {
  name = "becario-trabajo"
  user = aws_iam_user.becario.name
  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Sid      = "LeerInformes"
        Effect   = "Allow"
        Action   = ["s3:ListBucket", "s3:GetObject"]
        Resource = [aws_s3_bucket.informes.arn, "${aws_s3_bucket.informes.arn}/*"]
      },
      {
        Sid      = "AjustarseLosPermisos"
        Effect   = "Allow"
        Action   = ["iam:GetUser", "iam:ListUserPolicies", "iam:GetUserPolicy", "iam:PutUserPolicy"]
        Resource = aws_iam_user.becario.arn
      },
    ]
  })
}

# La clave del becario. Acabó copiada en un repositorio público.
resource "aws_iam_access_key" "becario" {
  user = aws_iam_user.becario.name
}

output "becario_clave" {
  value = aws_iam_access_key.becario.id
}

output "becario_secreto" {
  value     = aws_iam_access_key.becario.secret
  sensitive = true
}

# --- Red y servidor web -----------------------------------------------------------------

resource "aws_security_group" "web" {
  name        = "{web}"
  description = "Servidor web de la empresa"

  ingress {
    description = "Web"
    from_port   = 80
    to_port     = 80
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]
  }

  ingress {
    description = "Administracion"
    from_port   = 22
    to_port     = 22
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]
  }

  egress {
    description = "Todo"
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }
}

resource "aws_instance" "web" {
  ami                    = "ami-ubuntu2204"
  instance_type          = "t3.micro"
  vpc_security_group_ids = [aws_security_group.web.id]
  user_data              = <<-SH
    #!/bin/sh
    echo "DB_PASSWORD=Empresa2026!" > /etc/web.env
  SH
  tags                   = { Name = "{web}" }
}
