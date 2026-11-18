# U1 · E2 · El security.txt de la empresa

Tu empresa ficticia es **{dominio}**. Escribe su `security.txt` en `web/.well-known/security.txt` con:

- Contact: {contacto}
- Policy: {politica}
- Canonical: {canonica}
- Preferred-Languages: es
- Expires: una fecha de dentro de menos de un año, en formato RFC 3339 (como 2027-10-31T23:59:59Z)

Sírvelo con `docker compose up -d` y comprueba que responde en http://localhost:8081/.well-known/security.txt
