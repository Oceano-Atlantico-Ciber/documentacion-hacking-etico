// Lo genera docente-hacking-etico/tablero/generar.py tras cada corrección. No se edita a mano.
window.ENTREGAS = {
 "actualizado": "2026-11-26T17:32+00:00",
 "bloques": [
  {
   "nombre": "Git",
   "ejercicios": [
    "e1",
    "e2",
    "e3",
    "e4",
    "e5",
    "e6",
    "e7",
    "e8"
   ],
   "alumnos": {
    "adrian47gg": {
     "e1": "bien",
     "e2": "bien",
     "e3": "bien",
     "e4": "bien",
     "e5": "bien",
     "e6": "bien",
     "e7": "bien",
     "e8": "bien"
    },
    "agracia90": {
     "e1": "bien",
     "e2": "bien",
     "e3": "bien",
     "e4": "bien",
     "e5": "bien",
     "e6": "bien",
     "e7": "bien",
     "e8": "bien"
    },
    "alfaro-cmd": {
     "e1": "bien",
     "e2": "bien",
     "e3": "bien",
     "e4": "bien",
     "e5": "bien",
     "e6": "bien",
     "e7": "bien",
     "e8": "bien"
    },
    "dayx33": {
     "e1": "mal",
     "e2": "bien",
     "e3": "bien",
     "e4": "mal",
     "e5": "bien",
     "e6": "bien",
     "e7": "bien",
     "e8": "bien"
    },
    "hugocampos646": {
     "e1": "bien",
     "e2": "bien",
     "e3": "bien",
     "e4": "bien",
     "e5": "bien",
     "e6": "bien",
     "e7": "bien",
     "e8": "bien"
    },
    "igormillan": {
     "e1": "bien",
     "e2": "bien",
     "e3": "bien",
     "e4": "mal",
     "e5": "bien",
     "e6": "mal",
     "e7": "bien",
     "e8": "mal"
    },
    "jancand": {
     "e1": "bien",
     "e2": "bien",
     "e3": "bien",
     "e4": "bien",
     "e5": "bien",
     "e6": "bien",
     "e7": "bien",
     "e8": "bien"
    },
    "juanadiego": {
     "e1": "bien",
     "e2": "bien",
     "e3": "bien",
     "e4": "mal",
     "e5": "bien",
     "e6": "mal",
     "e7": "mal",
     "e8": "mal"
    },
    "lord999w": {
     "e1": "bien",
     "e2": "bien",
     "e3": "sin",
     "e4": "sin",
     "e5": "sin",
     "e6": "sin",
     "e7": "sin",
     "e8": "sin"
    },
    "manuelciordiamartinez-glitch": {
     "e1": "bien",
     "e2": "bien",
     "e3": "bien",
     "e4": "bien",
     "e5": "bien",
     "e6": "bien",
     "e7": "bien",
     "e8": "bien"
    },
    "pabloba1710": {
     "e1": "mal",
     "e2": "bien",
     "e3": "bien",
     "e4": "bien",
     "e5": "bien",
     "e6": "bien",
     "e7": "bien",
     "e8": "bien"
    },
    "robertoespiago-jpg": {
     "e1": "bien",
     "e2": "bien",
     "e3": "bien",
     "e4": "bien",
     "e5": "bien",
     "e6": "bien",
     "e7": "bien",
     "e8": "bien"
    },
    "rubenalondiaz2-hash": {
     "e1": "bien",
     "e2": "sin",
     "e3": "sin",
     "e4": "sin",
     "e5": "sin",
     "e6": "sin",
     "e7": "sin",
     "e8": "sin"
    },
    "umbreon0197": {
     "e1": "mal",
     "e2": "bien",
     "e3": "mal",
     "e4": "mal",
     "e5": "bien",
     "e6": "bien",
     "e7": "bien",
     "e8": "mal"
    },
    "vladukrisp-ctrl": {
     "e1": "bien",
     "e2": "bien",
     "e3": "bien",
     "e4": "bien",
     "e5": "bien",
     "e6": "bien",
     "e7": "bien",
     "e8": "bien"
    }
   },
   "detalle": {
    "dayx33": {
     "e1": [
      {
       "resumen": "se esperaban 3 commits en e1/ y hay 7 (40a1545 «docs(e1): objetivo de la auditoría», 7ec6453 «docs(e1): herramientas de la auditoría», 74e209b «docs(e1): notas de la auditoría», b04a5fe «Eliminar ficheros mal hechos», 7cd0561 «docs(e1): objetivo de la auditoría», 1966037 «docs(e1): notas de la audi…"
      },
      {
       "resumen": "b04a5fe debe cambiar un solo fichero de e1/ y cambia 3: e1/herramientas.md, e1/notas.md, e1/objetivo.md"
      },
      {
       "resumen": "b04a5fe: el mensaje «Eliminar ficheros mal hechos» no sigue Conventional Commits, tipo(ámbito): descripción, con tipo feat, fix, docs, style, refactor, test o chore"
      }
     ],
     "e4": [
      {
       "resumen": "puertos.txt no sigue la regla: no está ordenado por número de puerto: «53 dns» debe ir antes que «5432 postgresql»"
      }
     ]
    },
    "igormillan": {
     "e4": [
      {
       "resumen": "puertos.txt no sigue la regla: faltan líneas: «110 pop3», «5432 postgresql»"
      }
     ],
     "e6": [
      {
       "resumen": "el último commit debe llamarse «docs(e6): informe de alcance» y se llama «wip(e6): paso 4»"
      },
      {
       "resumen": "quedan commits wip en la historia (4): fúndelos con squash o fixup en git rebase -i"
      },
      {
       "resumen": "debe quedar un único commit que cree fundamentos/git/e6/informe.md y nada más: fundamentos/git/e6/informe.md ya existía en el commit anterior, 5d43787 «wip(e6): paso 3»"
      }
     ],
     "e8": [
      {
       "resumen": "hallazgo.txt debe contener el SHA completo del commit que filtró la clave: no hay ningún SHA de 40 caracteres"
      }
     ]
    },
    "juanadiego": {
     "e4": [
      {
       "resumen": "se esperaba un commit «feat(e4): puerto encontrado por B» y no está en la historia: o falta integrar su rama, o se borró al reescribir la historia"
      },
      {
       "resumen": "puertos.txt no sigue la regla: faltan líneas: «9200 elasticsearch»"
      }
     ],
     "e6": [
      {
       "resumen": "el último commit debe llamarse «docs(e6): informe de alcance» y se llama «Merge branch 'git/e6-wip' of https://github.com/Oceano-Atlantico-Ciber/entregas-juanadiego into git/e6-wip»"
      },
      {
       "resumen": "quedan commits wip en la historia (1): fúndelos con squash o fixup en git rebase -i"
      },
      {
       "resumen": "debe quedar un único commit que cree fundamentos/git/e6/informe.md y nada más: el último commit es un merge"
      }
     ],
     "e7": [
      {
       "resumen": "no hay un commit que deshaga exactamente «feat(e7): activar modo depuración»: un arreglo a mano no deja el mismo cambio inverso, hazlo con git revert a6ff69c"
      },
      {
       "resumen": "fundamentos/git/e7/config.ini no tiene el contenido esperado: la línea 3 es «debug = true» y debería ser «debug = false»"
      }
     ],
     "e8": [
      {
       "resumen": "la clave sigue en la historia de la rama, en 2112693, 106cc2e: repite la purga con git-filter-repo"
      },
      {
       "resumen": "hallazgo.txt debe contener el SHA completo del commit que filtró la clave: no hay ningún SHA de 40 caracteres"
      }
     ]
    },
    "pabloba1710": {
     "e1": [
      {
       "resumen": "se esperaban 3 commits en e1/ y hay 1 (8cf0951 «Añadir archivos del ejercicio 1 de fundamentos»): cada fichero va en su propio commit"
      },
      {
       "resumen": "8cf0951 debe cambiar un solo fichero de e1/ y cambia 3: e1/herramientas.md, e1/notas.md, e1/objetivo.md"
      },
      {
       "resumen": "8cf0951: el mensaje «Añadir archivos del ejercicio 1 de fundamentos» no sigue Conventional Commits, tipo(ámbito): descripción, con tipo feat, fix, docs, style, refactor, test o chore"
      }
     ]
    },
    "umbreon0197": {
     "e1": [
      {
       "resumen": "se esperaban 3 commits en e1/ y hay 1 (3d357fd «docs(e1): objetivo de la auditoría»): cada fichero va en su propio commit"
      },
      {
       "resumen": "sin commit: fundamentos/git/e1/herramientas.md, fundamentos/git/e1/notas.md: ningún commit lo añade"
      },
      {
       "resumen": "falta fundamentos/git/e1/herramientas.md: no está en el commit evaluado"
      },
      {
       "resumen": "falta fundamentos/git/e1/notas.md: no está en el commit evaluado"
      }
     ],
     "e3": [
      {
       "resumen": "se esperaba un commit «feat(e3): rama para merge con commit» y no está en la historia: o falta integrar su rama, o se borró al reescribir la historia"
      },
      {
       "resumen": "falta fundamentos/git/e3/noff.txt: no está en el commit evaluado"
      }
     ],
     "e4": [
      {
       "resumen": "puertos.txt no sigue la regla: no está ordenado por número de puerto: «22 ssh» debe ir antes que «9200 elasticsearch»"
      }
     ],
     "e8": [
      {
       "resumen": "ca71c0e sigue en la historia de la rama: al purgar, el commit que filtró la clave cambia de SHA"
      },
      {
       "resumen": "ca71c0e no es el commit que subió la clave a GitHub: no añade la clave en fundamentos/git/e8/.env. Búscalo con git log -p -S API_KEY="
      }
     ]
    }
   }
  },
  {
   "nombre": "Docker",
   "ejercicios": [
    "e1",
    "e2",
    "e3",
    "e4",
    "e5",
    "e6",
    "e7",
    "e8"
   ],
   "alumnos": {
    "adrian47gg": {
     "e1": "bien",
     "e2": "mal",
     "e3": "mal",
     "e4": "bien",
     "e5": "mal",
     "e6": "bien",
     "e7": "bien",
     "e8": "mal"
    },
    "agracia90": {
     "e1": "bien",
     "e2": "bien",
     "e3": "bien",
     "e4": "bien",
     "e5": "bien",
     "e6": "bien",
     "e7": "bien",
     "e8": "bien"
    },
    "alfaro-cmd": {
     "e1": "bien",
     "e2": "bien",
     "e3": "bien",
     "e4": "bien",
     "e5": "bien",
     "e6": "bien",
     "e7": "bien",
     "e8": "bien"
    },
    "dayx33": {
     "e1": "bien",
     "e2": "bien",
     "e3": "bien",
     "e4": "bien",
     "e5": "bien",
     "e6": "bien",
     "e7": "bien",
     "e8": "bien"
    },
    "hugocampos646": {
     "e1": "bien",
     "e2": "bien",
     "e3": "bien",
     "e4": "bien",
     "e5": "bien",
     "e6": "bien",
     "e7": "bien",
     "e8": "bien"
    },
    "igormillan": {
     "e1": "bien",
     "e2": "bien",
     "e3": "bien",
     "e4": "mal",
     "e5": "mal",
     "e6": "bien",
     "e7": "sin",
     "e8": "sin"
    },
    "jancand": {
     "e1": "bien",
     "e2": "bien",
     "e3": "bien",
     "e4": "bien",
     "e5": "bien",
     "e6": "bien",
     "e7": "bien",
     "e8": "bien"
    },
    "juanadiego": {
     "e1": "bien",
     "e2": "bien",
     "e3": "bien",
     "e4": "bien",
     "e5": "bien",
     "e6": "bien",
     "e7": "bien",
     "e8": "mal"
    },
    "lord999w": {
     "e1": "bien",
     "e2": "bien",
     "e3": "bien",
     "e4": "bien",
     "e5": "bien",
     "e6": "bien",
     "e7": "bien",
     "e8": "bien"
    },
    "manuelciordiamartinez-glitch": {
     "e1": "sin",
     "e2": "bien",
     "e3": "bien",
     "e4": "bien",
     "e5": "bien",
     "e6": "bien",
     "e7": "bien",
     "e8": "bien"
    },
    "pabloba1710": {
     "e1": "mal",
     "e2": "provisional",
     "e3": "bien",
     "e4": "mal",
     "e5": "bien",
     "e6": "bien",
     "e7": "bien",
     "e8": "bien"
    },
    "robertoespiago-jpg": {
     "e1": "bien",
     "e2": "bien",
     "e3": "bien",
     "e4": "bien",
     "e5": "bien",
     "e6": "bien",
     "e7": "bien",
     "e8": "bien"
    },
    "rubenalondiaz2-hash": {
     "e1": "bien",
     "e2": "bien",
     "e3": "bien",
     "e4": "bien",
     "e5": "bien",
     "e6": "bien",
     "e7": "bien",
     "e8": "bien"
    },
    "umbreon0197": {
     "e1": "bien",
     "e2": "bien",
     "e3": "bien",
     "e4": "bien",
     "e5": "bien",
     "e6": "mal",
     "e7": "bien",
     "e8": "bien"
    },
    "vladukrisp-ctrl": {
     "e1": "bien",
     "e2": "bien",
     "e3": "bien",
     "e4": "bien",
     "e5": "bien",
     "e6": "bien",
     "e7": "bien",
     "e8": "bien"
    }
   },
   "detalle": {
    "adrian47gg": {
     "e2": [
      {
       "resumen": "falta fundamentos/docker/e2/Dockerfile, fundamentos/docker/e2/sondeo.txt"
      }
     ],
     "e3": [
      {
       "resumen": "falta fundamentos/docker/e3/.dockerignore"
      }
     ],
     "e5": [
      {
       "resumen": "La etiqueta no es anotada: bórrala y créala con git tag -a"
      }
     ],
     "e8": [
      {
       "resumen": "informe.md tiene 0 filas y hay al menos 10 fallos: una fila por fallo"
      }
     ]
    },
    "igormillan": {
     "e4": [
      {
       "resumen": "falta fundamentos/docker/e4/Dockerfile, fundamentos/docker/e4/hallazgo.txt, fundamentos/docker/e4/.dockerignore"
      }
     ],
     "e5": [
      {
       "resumen": "falta fundamentos/docker/e5/levantar.sh, fundamentos/docker/e5/consulta.txt, fundamentos/docker/e5/web/index.html"
      }
     ]
    },
    "juanadiego": {
     "e8": [
      {
       "resumen": "queda alguna puerta abierta: panel: privileged; panel: monta el socket de Docker"
      }
     ]
    },
    "pabloba1710": {
     "e1": [
      {
       "resumen": "el contenedor salía de nginx:alpine y debía salir de nginx:1.27-alpine"
      },
      {
       "resumen": "el contenedor no publicaba 127.0.0.1:8080->80/tcp: no publicaba ningún puerto"
      },
      {
       "resumen": "el contenedor no llegó a pararse y volver a arrancar: según inspect.json no se paró nunca"
      },
      {
       "resumen": "en logs.txt no hay ninguna petición servida con tu página: no hay ningún GET / con código 200"
      }
     ],
     "e4": [
      {
       "resumen": "la construcción no ejecuta informe.py --comprobar con el secreto: no aparece «clave de la API válida». Usa RUN --mount=type=secret,id=api"
      }
     ]
    },
    "umbreon0197": {
     "e6": [
      {
       "resumen": "sondeo.txt no tiene las cuatro líneas, con 80 y 5432 abiertos: tiene 2 líneas y debe tener 4, una por puerto sondeado"
      }
     ]
    }
   }
  },
  {
   "nombre": "API REST",
   "ejercicios": [
    "e1",
    "e2",
    "e3",
    "e4",
    "e5",
    "e6",
    "e7",
    "e8"
   ],
   "alumnos": {
    "adrian47gg": {
     "e1": "sin",
     "e2": "sin",
     "e3": "sin",
     "e4": "sin",
     "e5": "sin",
     "e6": "sin",
     "e7": "sin",
     "e8": "sin"
    },
    "agracia90": {
     "e1": "bien",
     "e2": "bien",
     "e3": "bien",
     "e4": "bien",
     "e5": "bien",
     "e6": "bien",
     "e7": "bien",
     "e8": "bien"
    },
    "alfaro-cmd": {
     "e1": "sin",
     "e2": "sin",
     "e3": "sin",
     "e4": "sin",
     "e5": "sin",
     "e6": "sin",
     "e7": "sin",
     "e8": "sin"
    },
    "dayx33": {
     "e1": "bien",
     "e2": "bien",
     "e3": "sin",
     "e4": "sin",
     "e5": "sin",
     "e6": "sin",
     "e7": "sin",
     "e8": "sin"
    },
    "hugocampos646": {
     "e1": "bien",
     "e2": "sin",
     "e3": "sin",
     "e4": "sin",
     "e5": "sin",
     "e6": "sin",
     "e7": "sin",
     "e8": "sin"
    },
    "igormillan": {
     "e1": "sin",
     "e2": "sin",
     "e3": "sin",
     "e4": "sin",
     "e5": "sin",
     "e6": "sin",
     "e7": "sin",
     "e8": "sin"
    },
    "jancand": {
     "e1": "bien",
     "e2": "bien",
     "e3": "bien",
     "e4": "bien",
     "e5": "bien",
     "e6": "bien",
     "e7": "bien",
     "e8": "bien"
    },
    "juanadiego": {
     "e1": "sin",
     "e2": "sin",
     "e3": "sin",
     "e4": "sin",
     "e5": "sin",
     "e6": "sin",
     "e7": "sin",
     "e8": "sin"
    },
    "lord999w": {
     "e1": "sin",
     "e2": "sin",
     "e3": "sin",
     "e4": "sin",
     "e5": "sin",
     "e6": "sin",
     "e7": "sin",
     "e8": "sin"
    },
    "manuelciordiamartinez-glitch": {
     "e1": "bien",
     "e2": "sin",
     "e3": "sin",
     "e4": "sin",
     "e5": "sin",
     "e6": "sin",
     "e7": "sin",
     "e8": "sin"
    },
    "pabloba1710": {
     "e1": "bien",
     "e2": "sin",
     "e3": "sin",
     "e4": "sin",
     "e5": "sin",
     "e6": "sin",
     "e7": "sin",
     "e8": "sin"
    },
    "robertoespiago-jpg": {
     "e1": "sin",
     "e2": "sin",
     "e3": "sin",
     "e4": "sin",
     "e5": "sin",
     "e6": "sin",
     "e7": "sin",
     "e8": "sin"
    },
    "rubenalondiaz2-hash": {
     "e1": "bien",
     "e2": "bien",
     "e3": "sin",
     "e4": "sin",
     "e5": "sin",
     "e6": "sin",
     "e7": "sin",
     "e8": "sin"
    },
    "umbreon0197": {
     "e1": "sin",
     "e2": "sin",
     "e3": "sin",
     "e4": "sin",
     "e5": "sin",
     "e6": "sin",
     "e7": "sin",
     "e8": "sin"
    },
    "vladukrisp-ctrl": {
     "e1": "bien",
     "e2": "bien",
     "e3": "bien",
     "e4": "bien",
     "e5": "bien",
     "e6": "bien",
     "e7": "bien",
     "e8": "bien"
    }
   },
   "detalle": {}
  },
  {
   "nombre": "Terraform y AWS",
   "ejercicios": [
    "e1",
    "e2",
    "e3",
    "e4",
    "e5",
    "e6",
    "e7",
    "e8"
   ],
   "alumnos": {
    "adrian47gg": {
     "e1": "sin",
     "e2": "sin",
     "e3": "sin",
     "e4": "sin",
     "e5": "sin",
     "e6": "sin",
     "e7": "sin",
     "e8": "sin"
    },
    "agracia90": {
     "e1": "sin",
     "e2": "sin",
     "e3": "sin",
     "e4": "sin",
     "e5": "sin",
     "e6": "sin",
     "e7": "sin",
     "e8": "sin"
    },
    "alfaro-cmd": {
     "e1": "sin",
     "e2": "sin",
     "e3": "sin",
     "e4": "sin",
     "e5": "sin",
     "e6": "sin",
     "e7": "sin",
     "e8": "sin"
    },
    "dayx33": {
     "e1": "sin",
     "e2": "sin",
     "e3": "sin",
     "e4": "sin",
     "e5": "sin",
     "e6": "sin",
     "e7": "sin",
     "e8": "sin"
    },
    "hugocampos646": {
     "e1": "sin",
     "e2": "sin",
     "e3": "sin",
     "e4": "sin",
     "e5": "sin",
     "e6": "sin",
     "e7": "sin",
     "e8": "sin"
    },
    "igormillan": {
     "e1": "sin",
     "e2": "sin",
     "e3": "sin",
     "e4": "sin",
     "e5": "sin",
     "e6": "sin",
     "e7": "sin",
     "e8": "sin"
    },
    "jancand": {
     "e1": "sin",
     "e2": "sin",
     "e3": "sin",
     "e4": "sin",
     "e5": "sin",
     "e6": "sin",
     "e7": "sin",
     "e8": "sin"
    },
    "juanadiego": {
     "e1": "sin",
     "e2": "sin",
     "e3": "sin",
     "e4": "sin",
     "e5": "sin",
     "e6": "sin",
     "e7": "sin",
     "e8": "sin"
    },
    "lord999w": {
     "e1": "sin",
     "e2": "sin",
     "e3": "sin",
     "e4": "sin",
     "e5": "sin",
     "e6": "sin",
     "e7": "sin",
     "e8": "sin"
    },
    "manuelciordiamartinez-glitch": {
     "e1": "sin",
     "e2": "sin",
     "e3": "sin",
     "e4": "sin",
     "e5": "sin",
     "e6": "sin",
     "e7": "sin",
     "e8": "sin"
    },
    "pabloba1710": {
     "e1": "sin",
     "e2": "sin",
     "e3": "sin",
     "e4": "sin",
     "e5": "sin",
     "e6": "sin",
     "e7": "sin",
     "e8": "sin"
    },
    "robertoespiago-jpg": {
     "e1": "sin",
     "e2": "sin",
     "e3": "sin",
     "e4": "sin",
     "e5": "sin",
     "e6": "sin",
     "e7": "sin",
     "e8": "sin"
    },
    "rubenalondiaz2-hash": {
     "e1": "sin",
     "e2": "sin",
     "e3": "sin",
     "e4": "sin",
     "e5": "sin",
     "e6": "sin",
     "e7": "sin",
     "e8": "sin"
    },
    "umbreon0197": {
     "e1": "sin",
     "e2": "sin",
     "e3": "sin",
     "e4": "sin",
     "e5": "sin",
     "e6": "sin",
     "e7": "sin",
     "e8": "sin"
    },
    "vladukrisp-ctrl": {
     "e1": "sin",
     "e2": "sin",
     "e3": "sin",
     "e4": "sin",
     "e5": "sin",
     "e6": "sin",
     "e7": "sin",
     "e8": "sin"
    }
   },
   "detalle": {}
  },
  {
   "nombre": "RA1 · Hacking ético",
   "ejercicios": [
    "u1-e1",
    "u1-e2",
    "u2-e1",
    "u2-e2",
    "u3-e1",
    "u3-e2",
    "u3-e3",
    "u4-e1",
    "u4-e2",
    "u4-e3"
   ],
   "alumnos": {
    "adrian47gg": {
     "u1-e1": "sin",
     "u1-e2": "sin",
     "u2-e1": "sin",
     "u2-e2": "sin",
     "u3-e1": "sin",
     "u3-e2": "sin",
     "u3-e3": "sin",
     "u4-e1": "sin",
     "u4-e2": "sin",
     "u4-e3": "sin"
    },
    "agracia90": {
     "u1-e1": "sin",
     "u1-e2": "sin",
     "u2-e1": "sin",
     "u2-e2": "sin",
     "u3-e1": "sin",
     "u3-e2": "sin",
     "u3-e3": "sin",
     "u4-e1": "sin",
     "u4-e2": "sin",
     "u4-e3": "sin"
    },
    "alfaro-cmd": {
     "u1-e1": "sin",
     "u1-e2": "sin",
     "u2-e1": "sin",
     "u2-e2": "sin",
     "u3-e1": "sin",
     "u3-e2": "sin",
     "u3-e3": "sin",
     "u4-e1": "sin",
     "u4-e2": "sin",
     "u4-e3": "sin"
    },
    "dayx33": {
     "u1-e1": "sin",
     "u1-e2": "sin",
     "u2-e1": "sin",
     "u2-e2": "sin",
     "u3-e1": "sin",
     "u3-e2": "sin",
     "u3-e3": "sin",
     "u4-e1": "sin",
     "u4-e2": "sin",
     "u4-e3": "sin"
    },
    "hugocampos646": {
     "u1-e1": "sin",
     "u1-e2": "sin",
     "u2-e1": "sin",
     "u2-e2": "sin",
     "u3-e1": "sin",
     "u3-e2": "sin",
     "u3-e3": "sin",
     "u4-e1": "sin",
     "u4-e2": "sin",
     "u4-e3": "sin"
    },
    "igormillan": {
     "u1-e1": "sin",
     "u1-e2": "sin",
     "u2-e1": "sin",
     "u2-e2": "sin",
     "u3-e1": "sin",
     "u3-e2": "sin",
     "u3-e3": "sin",
     "u4-e1": "sin",
     "u4-e2": "sin",
     "u4-e3": "sin"
    },
    "jancand": {
     "u1-e1": "sin",
     "u1-e2": "sin",
     "u2-e1": "sin",
     "u2-e2": "sin",
     "u3-e1": "sin",
     "u3-e2": "sin",
     "u3-e3": "sin",
     "u4-e1": "sin",
     "u4-e2": "sin",
     "u4-e3": "sin"
    },
    "juanadiego": {
     "u1-e1": "sin",
     "u1-e2": "sin",
     "u2-e1": "sin",
     "u2-e2": "sin",
     "u3-e1": "sin",
     "u3-e2": "sin",
     "u3-e3": "sin",
     "u4-e1": "sin",
     "u4-e2": "sin",
     "u4-e3": "sin"
    },
    "lord999w": {
     "u1-e1": "sin",
     "u1-e2": "sin",
     "u2-e1": "sin",
     "u2-e2": "sin",
     "u3-e1": "sin",
     "u3-e2": "sin",
     "u3-e3": "sin",
     "u4-e1": "sin",
     "u4-e2": "sin",
     "u4-e3": "sin"
    },
    "manuelciordiamartinez-glitch": {
     "u1-e1": "sin",
     "u1-e2": "sin",
     "u2-e1": "sin",
     "u2-e2": "sin",
     "u3-e1": "sin",
     "u3-e2": "sin",
     "u3-e3": "sin",
     "u4-e1": "sin",
     "u4-e2": "sin",
     "u4-e3": "sin"
    },
    "pabloba1710": {
     "u1-e1": "sin",
     "u1-e2": "sin",
     "u2-e1": "sin",
     "u2-e2": "sin",
     "u3-e1": "sin",
     "u3-e2": "sin",
     "u3-e3": "sin",
     "u4-e1": "sin",
     "u4-e2": "sin",
     "u4-e3": "sin"
    },
    "robertoespiago-jpg": {
     "u1-e1": "sin",
     "u1-e2": "sin",
     "u2-e1": "sin",
     "u2-e2": "sin",
     "u3-e1": "sin",
     "u3-e2": "sin",
     "u3-e3": "sin",
     "u4-e1": "sin",
     "u4-e2": "sin",
     "u4-e3": "sin"
    },
    "rubenalondiaz2-hash": {
     "u1-e1": "sin",
     "u1-e2": "sin",
     "u2-e1": "sin",
     "u2-e2": "sin",
     "u3-e1": "sin",
     "u3-e2": "sin",
     "u3-e3": "sin",
     "u4-e1": "sin",
     "u4-e2": "sin",
     "u4-e3": "sin"
    },
    "umbreon0197": {
     "u1-e1": "sin",
     "u1-e2": "sin",
     "u2-e1": "sin",
     "u2-e2": "sin",
     "u3-e1": "sin",
     "u3-e2": "sin",
     "u3-e3": "sin",
     "u4-e1": "sin",
     "u4-e2": "sin",
     "u4-e3": "sin"
    },
    "vladukrisp-ctrl": {
     "u1-e1": "sin",
     "u1-e2": "sin",
     "u2-e1": "sin",
     "u2-e2": "sin",
     "u3-e1": "sin",
     "u3-e2": "sin",
     "u3-e3": "sin",
     "u4-e1": "sin",
     "u4-e2": "sin",
     "u4-e3": "sin"
    }
   },
   "detalle": {}
  }
 ]
};
