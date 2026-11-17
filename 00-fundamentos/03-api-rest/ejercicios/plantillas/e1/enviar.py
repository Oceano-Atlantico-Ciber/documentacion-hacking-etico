"""Envía un fichero de texto tal cual por una conexión TCP y enseña lo que vuelve.

Uso: py enviar.py peticion-get.txt [equipo] [puerto]      (por defecto, localhost 8080)

Es lo mismo que hacen el navegador, curl o cualquier lenguaje: escribir una petición HTTP en
una conexión y leer la respuesta. Lo único que añade este programa es cambiar cada salto de
línea por CRLF (\\r\\n), que es el que pide HTTP; tu editor guarda solo \\n. No cuenta los bytes
del cuerpo por ti: si Content-Length no cuadra, lo verás.
"""

import socket
import sys


def main(argv):
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    except AttributeError:
        pass
    if not 1 <= len(argv) <= 3:
        print(__doc__.strip().splitlines()[2], file=sys.stderr)
        return 2
    fichero, equipo, puerto = argv[0], (argv[1:2] or ["localhost"])[0], int((argv[2:3] or ["8080"])[0])
    with open(fichero, encoding="utf-8", newline="") as f:
        texto = f.read().replace("\r\n", "\n")
    cabecera, separador, cuerpo = texto.partition("\n\n")
    if not separador:
        print("Aviso: no hay línea en blanco. Toda petición HTTP termina sus cabeceras con una.", file=sys.stderr)
    peticion = cabecera.replace("\n", "\r\n").encode() + b"\r\n\r\n" + cuerpo.rstrip("\n").encode()
    print(f"--- Enviando {len(peticion)} bytes a {equipo}:{puerto} ---")
    print(peticion.decode().replace("\r\n", "\n"))
    print("--- Respuesta ---")
    # localhost puede resolver primero a ::1 y tardar en caer a IPv4: se va directo.
    with socket.create_connection(("127.0.0.1" if equipo == "localhost" else equipo, puerto), timeout=5) as s:
        s.sendall(peticion)
        respuesta = b""
        try:
            while True:
                trozo = s.recv(65536)
                if not trozo:
                    break
                respuesta += trozo
                if b"\r\n\r\n" in respuesta:
                    cab, _, resto = respuesta.partition(b"\r\n\r\n")
                    largo = next((int(l.split(b":", 1)[1]) for l in cab.split(b"\r\n")
                                  if l.lower().startswith(b"content-length:")), 0)
                    if len(resto) >= largo:
                        break
        except socket.timeout:
            print("(el servidor no ha respondido en 5 s: ¿falta la línea en blanco o sobra Content-Length?)")
    print(respuesta.decode(errors="replace").replace("\r\n", "\n"))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
