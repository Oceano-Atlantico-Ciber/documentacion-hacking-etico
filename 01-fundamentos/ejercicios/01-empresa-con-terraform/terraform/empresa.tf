# Infraestructura de la empresa ficticia del curso, tal como la dejó "el equipo anterior".
# Contiene fallos de configuración. Trivy los señala; tu trabajo es corregirlos aquí,
# volver a pasar Trivy hasta que no quede ningún aviso alto o crítico y desplegar en Floci.

# --- Almacenamiento: copias de seguridad de la empresa ---
resource "aws_s3_bucket" "copias" {
  bucket = "copias-empresa"
}

resource "aws_s3_bucket_public_access_block" "copias" {
  bucket                  = aws_s3_bucket.copias.id
  block_public_acls       = false
  block_public_policy     = false
  ignore_public_acls      = false
  restrict_public_buckets = false
}

# --- Identidad: permisos del equipo de operaciones ---
resource "aws_iam_user" "operaciones" {
  name = "operaciones"
}

resource "aws_iam_policy" "operaciones" {
  name = "operaciones-todo"
  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [{
      Effect   = "Allow"
      Action   = "*"
      Resource = "*"
    }]
  })
}

resource "aws_iam_user_policy_attachment" "operaciones" {
  user       = aws_iam_user.operaciones.name
  policy_arn = aws_iam_policy.operaciones.arn
}

# --- Red: cortafuegos del servidor web ---
resource "aws_security_group" "web" {
  name        = "web"
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
