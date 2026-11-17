# E7 · Auditar los permisos de la empresa

empresa/ es la misma cuenta del E2. Despliégala en tu Floci y revisa sus permisos de IAM como
administrador (la clave test), sin usar la clave de nadie más:

- Usuario {becario}, con la política becario-trabajo
- Usuario {operaciones}, con la política operaciones-todo
- Buckets {informes} (trabajo del becario) y {secretos} (solo dirección)

Guarda en simulacion.json la salida de aws iam simulate-principal-policy y escribe auditoria.md.
El enunciado completo está en la web del curso, en Ejercicios de Terraform y AWS, E7.
