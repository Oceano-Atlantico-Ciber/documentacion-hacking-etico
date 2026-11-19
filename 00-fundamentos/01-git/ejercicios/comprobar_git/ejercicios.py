"""Comprobaciones de cada ejercicio. Cada una recibe la ref a evaluar y devuelve los fallos (vacío = superado).

Cada fallo dice qué se ha encontrado y por qué no vale, para que el alumno pueda arreglarlo sin adivinar.
Lo esperado se calcula con preparar.py, el mismo módulo que genera el escenario del alumno.
"""

from __future__ import annotations

import re
from collections import Counter
from dataclasses import dataclass
from typing import Callable, Protocol

import preparar as p

from .repo import Repo


class Api(Protocol):
    def commit(self, repo: str, sha: str) -> dict | None:
        """El commit tal como lo da GET /repos/{repo}/commits/{sha}; None si GitHub no lo tiene."""


@dataclass(frozen=True)
class Contexto:
    repo: Repo
    nombre: str  # Org/entregas-<usuario>
    usuario: str
    api: Api | None  # None: sin acceso a GitHub (pruebas.py sin gh); lo que depende de GitHub no se comprueba

NO_SUBIDO = "no está en GitHub: súbelo con git push antes de comprobar lo que depende de GitHub"


MARCADORES = re.compile(r"^(<{7}|={7}|>{7}).*", re.MULTILINE)
SHA = re.compile(r"\b[0-9a-f]{40}\b")
TIPOS = "feat, fix, docs, style, refactor, test o chore"


def _lineas(texto: str) -> list[str]:
    """Las líneas con contenido, con los espacios normalizados: lo que el editor cambia sin que se vea no cuenta."""
    return [" ".join(linea.split()) for linea in texto.splitlines() if linea.strip()]


def _diferencia(real: str, esperado: str) -> str | None:
    """La primera diferencia entre dos textos, explicada; None si son iguales."""
    r, e = _lineas(real), _lineas(esperado)
    for n, (a, b) in enumerate(zip(r, e), 1):
        if a != b:
            return f"la línea {n} es «{a}» y debería ser «{b}»"
    if len(r) < len(e):
        return f"falta la línea «{e[len(r)]}»"
    if len(r) > len(e):
        return f"sobra la línea «{r[len(e)]}»"
    return None


def _commit(ctx: Contexto, sha: str) -> str:
    return f"{sha[:7]} «{ctx.repo.asunto(sha)}»"


def _unico(ctx: Contexto, ref: str, mensaje: str) -> tuple[str | None, list[str]]:
    shas = ctx.repo.con_mensaje(ref, mensaje)
    if len(shas) == 1:
        return shas[0], []
    if not shas:
        return None, [f"se esperaba un commit «{mensaje}» y no está en la historia: o falta integrar su rama, "
                      "o se borró al reescribir la historia"]
    return None, [f"se esperaba un commit «{mensaje}» y hay {len(shas)} ({', '.join(s[:7] for s in shas)}): "
                  "se copió en lugar de integrarse una sola vez"]


def _contenido(ctx: Contexto, ref: str, ej: str, nombre: str, esperado: str) -> list[str]:
    real = ctx.repo.fichero(ref, p.ruta(ej, nombre))
    if real is None:
        return [f"falta {p.ruta(ej, nombre)}: no está en el commit evaluado"]
    diferencia = _diferencia(real, esperado)
    return [f"{p.ruta(ej, nombre)} no tiene el contenido esperado: {diferencia}"] if diferencia else []


def e1(ctx: Contexto, ref: str) -> list[str]:
    esperados = p.e1(ctx.usuario).sueltos
    rutas = {p.ruta("e1", n) for n in esperados}
    commits = ctx.repo.commits(ref, rutas=(f"{p.RAIZ}/e1",))
    fallos = []
    if len(commits) != 3:
        lista = ", ".join(_commit(ctx, s) for s in reversed(commits))
        porque = ("cada commit que tocó e1/ sigue en la historia aunque después lo deshagas" if len(commits) > 3
                  else "cada fichero va en su propio commit")
        fallos.append(f"se esperaban 3 commits en e1/ y hay {len(commits)}" + (f" ({lista})" if lista else "") + f": {porque}")
    tocados = set()
    for sha in commits:
        corto, cambiados = sha[:7], ctx.repo.cambiados(sha)
        if len(cambiados) != 1 or not cambiados <= rutas:
            nombres = ", ".join(sorted(c.removeprefix(f"{p.RAIZ}/") for c in cambiados))
            fallos.append(f"{corto} debe cambiar un solo fichero de e1/ y cambia {len(cambiados)}: {nombres}")
        tocados |= cambiados
        if not p.CONVENTIONAL.match(asunto := ctx.repo.asunto(sha)):
            fallos.append(f"{corto}: el mensaje «{asunto}» no sigue Conventional Commits, tipo(ámbito): descripción, "
                          f"con tipo {TIPOS}")
        if ctx.api is None:
            continue
        if (datos := ctx.api.commit(ctx.nombre, sha)) is None:
            fallos.append(f"{corto} {NO_SUBIDO}")
            continue
        autor = (datos.get("author") or {}).get("login")
        if autor is None or autor.lower() != ctx.usuario:
            correo = ctx.repo.git("log", "-1", "--format=%ae", sha)
            donde = "ninguna cuenta" if autor is None else f"la cuenta {autor}"
            fallos.append(f"{corto}: GitHub no asocia el correo del autor a tu cuenta: {correo} pertenece a {donde}. "
                          "Verifícalo en Settings → Emails o usa tu correo …@users.noreply.github.com")
    if faltan := rutas - tocados:
        fallos.append(f"sin commit: {', '.join(sorted(faltan))}: ningún commit lo añade")
    for nombre, contenido in esperados.items():
        fallos += _contenido(ctx, ref, "e1", nombre, contenido)
    return fallos


def e2(ctx: Contexto, ref: str) -> list[str]:
    fallos = _contenido(ctx, ref, "e2", "app.py", p.e2(ctx.usuario).sueltos["app.py"])
    rutas = [p.ruta("e2", n) for n in p.E2_IGNORAR]
    if subidos := ctx.repo.git("log", "--format=", "--name-only", ref, "--", *rutas):
        fallos.append(f"llegaron a subirse: {', '.join(sorted(set(subidos.split())))}: siguen en la historia "
                      "aunque los borres después")
    gitignore = p.ruta("e2", ".gitignore")
    if ctx.repo.fichero(ref, gitignore) is None:
        fallos.append(f"falta {gitignore}: no está en el commit evaluado")
    elif no_ignorados := set(rutas) - ctx.repo.ignorados(ref, rutas, gitignore):
        fallos.append(f"{gitignore} no ignora: {', '.join(sorted(no_ignorados))}. Tiene que ignorarlos él solo, "
                      "sin contar el .gitignore de la raíz: compruébalo con git check-ignore -v")
    return fallos


def e3(ctx: Contexto, ref: str) -> list[str]:
    ff, fallos = _unico(ctx, ref, p.E3_FF)
    noff, f = _unico(ctx, ref, p.E3_NOFF)
    fallos += f
    principal = set(ctx.repo.commits(ref, "--first-parent"))
    merges = {m: ctx.repo.padres(m) for m in ctx.repo.commits(ref, "--merges")}
    if ff:
        if traido := next((m for m, padres in merges.items() if ff in padres[1:]), None):
            fallos.append(f"git/e3-ff no se integró con fast-forward: lo trajo el merge {_commit(ctx, traido)}. "
                          "Usa git merge --ff-only antes que el otro merge")
        elif ff not in principal:
            fallos.append("git/e3-ff no se integró con fast-forward: su commit no está en la línea principal de main")
    if noff and not any(padres[1:] == [noff] and padres[0] in principal for padres in merges.values()):
        como = "entró con fast-forward" if noff in principal else "ningún merge lo trae a main"
        fallos.append(f"git/e3-noff no se integró con un commit de merge (--no-ff): {como}")
    escenario = p.e3(ctx.usuario)
    for rama in escenario.ramas:
        for nombre, contenido in rama.commits[0].cambios.items():
            fallos += _contenido(ctx, ref, "e3", nombre, contenido)
    return fallos


def _regla_e4(real: str, esperado: str) -> str | None:
    """Por qué el inventario no sigue la regla; None si la sigue."""
    r, e = _lineas(real), _lineas(esperado)
    if faltan := list((Counter(e) - Counter(r)).elements()):
        return f"faltan líneas: {', '.join(f'«{x}»' for x in faltan)}"
    if sobran := list((Counter(r) - Counter(e)).elements()):
        return f"sobran líneas: {', '.join(f'«{x}»' for x in sobran)}"
    for a, b in zip(r, r[1:]):
        if e.index(a) > e.index(b):
            return f"no está ordenado por número de puerto: «{b}» debe ir antes que «{a}»"
    return None


def e4(ctx: Contexto, ref: str) -> list[str]:
    a, fallos = _unico(ctx, ref, p.E4_A)
    b, f = _unico(ctx, ref, p.E4_B)
    fallos += f
    if a and b:
        def resuelve(merge: str) -> bool:
            x, y = ctx.repo.padres(merge)[:2]
            lados = {(ctx.repo.ancestro(a, x), ctx.repo.ancestro(b, y)), (ctx.repo.ancestro(b, x), ctx.repo.ancestro(a, y))}
            return (True, True) in lados and ctx.repo.conflicto(x, y)
        if not any(resuelve(m) for m in ctx.repo.commits(ref, "--merges")):
            fallos.append("no hay un merge que una git/e4-a y git/e4-b resolviendo su conflicto: "
                          "el conflicto se resuelve dentro de git merge, no copiando el fichero")
    real = ctx.repo.fichero(ref, p.ruta("e4", p.E4_FICHERO)) or ""
    if marcador := MARCADORES.search(real):
        fallos.append(f"{p.E4_FICHERO} conserva marcadores de conflicto, como «{marcador.group().strip()}»: "
                      "bórralos antes de git add")
    elif motivo := _regla_e4(real, p.e4_resuelto(ctx.usuario)):
        fallos.append(f"{p.E4_FICHERO} no sigue la regla: {motivo}")
    return fallos


def e5(ctx: Contexto, ref: str) -> list[str]:
    fallos = []
    punta = ctx.repo.sha(ref)
    f2, f1 = punta, (ctx.repo.padres(punta) or [None])[0]
    if f1 is None or [ctx.repo.asunto(f1), ctx.repo.asunto(f2)] != [p.E5_F1, p.E5_F2]:
        final = ", ".join(f"«{ctx.repo.asunto(s)}»" for s in (f1, f2) if s)
        return fallos + [f"la rama debe terminar en «{p.E5_F1}» y «{p.E5_F2}», en ese orden, y termina en {final}"]
    if merge := next((s for s in (f1, f2) if len(ctx.repo.padres(s)) != 1), None):
        fallos.append(f"la rama no es lineal: hay un merge en lugar de un rebase ({_commit(ctx, merge)} tiene dos padres)")
    elif not any(ctx.repo.ancestro(m, ctx.repo.padres(f1)[0]) for m in ctx.repo.con_mensaje(ref, p.E5_MAIN)):
        base = ctx.repo.padres(f1)[0]
        fallos.append(f"la rama no está rebasada sobre «{p.E5_MAIN}»: tus commits parten de {_commit(ctx, base)}. "
                      "Haz git rebase main desde git/e5-feature")
    for commit in p.e5(ctx.usuario).ramas[0].commits:
        for nombre, contenido in commit.cambios.items():
            fallos += _contenido(ctx, ref, "e5", nombre, contenido)
    return fallos


def e6(ctx: Contexto, ref: str) -> list[str]:
    punta = ctx.repo.sha(ref)
    fichero = p.ruta("e6", p.E6_FICHERO)
    fallos = []
    if (asunto := ctx.repo.asunto(punta)) != p.E6_MENSAJE:
        fallos.append(f"el último commit debe llamarse «{p.E6_MENSAJE}» y se llama «{asunto}»")
    if wip := [a for a in ctx.repo.asuntos(ref) if a.startswith(p.E6_WIP)]:
        fallos.append(f"quedan commits wip en la historia ({len(wip)}): fúndelos con squash o fixup en git rebase -i")
    padres = ctx.repo.padres(punta)
    if len(padres) != 1:
        fallos.append(f"debe quedar un único commit que cree {fichero} y nada más: el último commit es un merge")
    elif ctx.repo.fichero(padres[0], fichero) is not None:
        fallos.append(f"debe quedar un único commit que cree {fichero} y nada más: {fichero} ya existía en el commit "
                      f"anterior, {_commit(ctx, padres[0])}")
    elif (cambiados := ctx.repo.cambiados(punta)) != {fichero}:
        fallos.append(f"debe quedar un único commit que cree {fichero} y nada más: también cambia "
                      f"{', '.join(sorted(cambiados - {fichero}))}")
    return fallos + _contenido(ctx, ref, "e6", p.E6_FICHERO, p.e6_final(ctx.usuario))


def e7(ctx: Contexto, ref: str) -> list[str]:
    erroneo, fallos = _unico(ctx, ref, p.E7_C2)
    fallos += _unico(ctx, ref, p.E7_C3)[1]
    if erroneo:
        inverso = ctx.repo.patch_id(erroneo, f"{erroneo}^")
        candidatos = ctx.repo.commits(ref, f"^{erroneo}", "--no-merges", rutas=(p.ruta("e7", p.E7_FICHERO),))
        if not any(ctx.repo.patch_id(f"{c}^", c) == inverso for c in candidatos):
            fallos.append(f"no hay un commit que deshaga exactamente «{p.E7_C2}»: un arreglo a mano no deja el mismo "
                          f"cambio inverso, hazlo con git revert {erroneo[:7]}")
    return fallos + _contenido(ctx, ref, "e7", p.E7_FICHERO, p.e7_config(ctx.usuario))


def e8(ctx: Contexto, ref: str) -> list[str]:
    fallos = [f"falta el commit «{m}»: purga el fichero, no los commits (--path … --invert-paths)"
              for m in (p.E8_A1, p.E8_A2, p.E8_A3, p.E8_A4) if not ctx.repo.con_mensaje(ref, m)]
    clave, env = p.e8_clave(ctx.usuario), p.ruta("e8", ".env")
    if con_clave := ctx.repo.git("log", "--format=%h", f"-S{clave}", ref):
        fallos.append(f"la clave sigue en la historia de la rama, en {', '.join(con_clave.split())}: "
                      "repite la purga con git-filter-repo")
    fallos += _contenido(ctx, ref, "e8", "app.py", p.E8_APP)
    hallazgo = SHA.search(ctx.repo.fichero(ref, p.ruta("e8", p.E8_HALLAZGO)) or "")
    if not hallazgo:
        return fallos + [f"{p.E8_HALLAZGO} debe contener el SHA completo del commit que filtró la clave: "
                         "no hay ningún SHA de 40 caracteres"]
    sha = hallazgo.group()
    if sha in ctx.repo.commits(ref):
        fallos.append(f"{sha[:7]} sigue en la historia de la rama: al purgar, el commit que filtró la clave cambia de SHA")
    if ctx.api is None:
        return fallos
    commit = ctx.api.commit(ctx.nombre, sha)
    if not commit:
        fallos.append(f"{sha[:7]} no es el commit que subió la clave a GitHub: GitHub no lo conoce, "
                      "¿subiste la rama antes de purgar (paso 2)?")
    elif not any(f["filename"] == env and clave in f.get("patch", "") for f in commit.get("files", [])):
        fallos.append(f"{sha[:7]} no es el commit que subió la clave a GitHub: no añade la clave en {env}. "
                      "Búscalo con git log -p -S API_KEY=")
    return fallos


COMPROBACIONES: dict[str, Callable[[Contexto, str], list[str]]] = {
    "e1": e1, "e2": e2, "e3": e3, "e4": e4, "e5": e5, "e6": e6, "e7": e7, "e8": e8,
}
# Dónde se evalúa cada ejercicio mientras no tiene etiqueta.
RAMAS = {"e1": "main", "e2": "main", "e3": "main", "e4": "main",
         "e5": "git/e5-feature", "e6": "git/e6-wip", "e7": "main", "e8": "git/e8-app"}
