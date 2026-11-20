"""Envía tu petición HTTP por una conexión TCP y enseña lo que vuelve.

Uso: py enviar.py peticion-get.txt [equipo] [puerto]      (por defecto, localhost 8080)

Es lo mismo que hacen el navegador, curl o cualquier lenguaje: escribir una petición HTTP en
una conexión y leer la respuesta. Da igual con qué editor guardes el fichero: este programa lo
deja en el formato que pide HTTP antes de enviarlo. Lo que no hace es escribir la petición por
ti: si falta la línea en blanco o Content-Length no cuadra con el cuerpo, te avisa.
"""

import ctypes
import socket
import sys


def texto_de(datos: bytes) -> str:
    """El texto del fichero, lo guarde como lo guarde el editor, con los saltos de línea normalizados.

    Mismo criterio que el corrector, para que los dos envíen exactamente la misma petición."""
    if datos[:2] in (b"\xff\xfe", b"\xfe\xff"):
        texto = datos.decode("utf-16")
    else:
        try:
            texto = datos.decode("utf-8-sig")
        except UnicodeDecodeError:
            texto = datos.decode("cp1252", "replace")
    return texto.replace("\r\n", "\n").replace("\r", "\n")


def preparar_salida():
    """En Windows, si la salida va a Tee-Object, se escribe como la lee PowerShell: así las tildes
    se ven bien en pantalla y quedan bien en el fichero, sin configurar nada."""
    for salida in (sys.stdout, sys.stderr):
        try:
            pagina = 0
            if sys.platform == "win32" and not salida.isatty():
                pagina = ctypes.windll.kernel32.GetConsoleOutputCP()
            salida.reconfigure(encoding=f"cp{pagina}" if pagina else "utf-8", errors="replace")
        except (AttributeError, LookupError, OSError):
            pass


def main(argv):
    preparar_salida()
    if not 1 <= len(argv) <= 3:
        print(__doc__.strip().splitlines()[2], file=sys.stderr)
        return 2
    fichero, equipo, puerto = argv[0], (argv[1:2] or ["localhost"])[0], int((argv[2:3] or ["8080"])[0])
    with open(fichero, "rb") as f:
        texto = texto_de(f.read())
    cabecera, separador, cuerpo = texto.partition("\n\n")
    if not separador:
        print("Aviso: no hay línea en blanco. Toda petición HTTP termina sus cabeceras con una.", file=sys.stderr)
    cuerpo = cuerpo.rstrip("\n").encode()
    dice = next((l.split(":", 1)[1].strip() for l in cabecera.split("\n") if l.lower().startswith("content-length:")), None)
    if dice is not None and dice != str(len(cuerpo)):
        print(f"Aviso: Content-Length dice {dice}, pero el cuerpo mide {len(cuerpo)}. "
              "Recuerda que cada tilde o ñ cuenta como dos.", file=sys.stderr)
    peticion = cabecera.replace("\n", "\r\n").encode() + b"\r\n\r\n" + cuerpo
    print(f"--- Enviando a {equipo}:{puerto} ---")
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
            print("(el servidor no ha respondido en 5 s: ¿falta la línea en blanco o Content-Length dice más de lo que hay?)")
    print(respuesta.decode(errors="replace").replace("\r\n", "\n"))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
