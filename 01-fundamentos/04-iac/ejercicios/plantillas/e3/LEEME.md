# E3 · Del clic al código

Lo que tienes que adoptar con import, tal como lo creaste en el E1:

- aws_s3_bucket con el bucket {bucket}
- aws_iam_user con el usuario {usuario}
- aws_iam_user_policy con la política lectura-notas de ese usuario (su id es {usuario}:lectura-notas)

proveedor.tf ya apunta a Floci. Escribe main.tf con los recursos y un bloque import por cada uno.
