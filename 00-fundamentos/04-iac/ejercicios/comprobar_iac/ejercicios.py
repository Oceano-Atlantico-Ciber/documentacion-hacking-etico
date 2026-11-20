"""Comprobaciones de cada ejercicio de Terraform y AWS, en el orden de «El corrector marca fallo si».

Las usan el corrector y pruebas.py. Cada una recibe el árbol del repositorio del alumno (una copia: se
puede escribir en ella) y produce sus fallos uno a uno; lanza Fallo cuando lo entregado no permite
seguir. Lo esperado sale de preparar.py. Todo se comprueba contra una Floci nueva, con los permisos de
IAM aplicados, y nunca se ejecuta código del alumno fuera de Terraform y de las órdenes aws admitidas.
"""

from __future__ import annotations

import base64
import json
import re
import shlex
from dataclasses import dataclass
from pathlib import Path
from typing import Callable, Iterator

import preparar as p

from .floci import Fallo, Floci, Salida

Comprobacion = Callable[["Caso"], Iterator[str]]


@dataclass(frozen=True)
class Caso:
    usuario: str
    raiz: Path  # el repositorio del alumno, extraído del commit evaluado (una copia)
    ej: str

    @property
    def carpeta(self) -> Path:
        return self.raiz / p.RAIZ / self.ej

    def de(self, ej: str) -> Path:
        return self.raiz / p.RAIZ / ej

    def leer(self, nombre: str, carpeta: Path | None = None) -> str:
        f = (carpeta or self.carpeta) / nombre
        if not f.is_file():
            return ""
        datos = f.read_bytes()
        codificacion = "utf-16" if datos[:2] in (b"\xff\xfe", b"\xfe\xff") else "utf-8-sig"
        return datos.decode(codificacion, "replace").replace("\r\n", "\n")

    def exigir(self, *nombres: str, carpeta: Path | None = None) -> None:
        base = carpeta or self.carpeta
        if faltan := [n for n in nombres if not (base / n).is_file()]:
            raise Fallo(f"falta {', '.join((base / n).relative_to(self.raiz).as_posix() for n in faltan)}")


def _sin_estado(carpeta: Path) -> None:
    """El corrector empieza de cero: fuera el estado y lo descargado, aunque se hayan subido por error."""
    for f in carpeta.rglob("*"):
        if f.is_file() and (f.name.endswith((".tfstate", ".tfstate.backup")) or ".terraform" in f.parts):
            f.unlink()


def _tf(floci: Floci, carpeta: Path, *args: str, que: str) -> Salida:
    r = floci.terraform(carpeta, *args)
    if r.codigo not in (0, 2) or (r.codigo == 2 and "-detailed-exitcode" not in args):
        raise Fallo(f"terraform {que} falla: {r.motivo}")
    return r


def _init(floci: Floci, carpeta: Path) -> None:
    _sin_estado(carpeta)
    _tf(floci, carpeta, "init", "-no-color", que="init")


def _apply(floci: Floci, carpeta: Path) -> None:
    _tf(floci, carpeta, "apply", "-auto-approve", "-no-color", que="apply")


def _plan_vacio(floci: Floci, carpeta: Path) -> str | None:
    """None si el plan no cambia nada; si no, el resumen del plan."""
    r = floci.terraform(carpeta, "plan", "-detailed-exitcode", "-no-color")
    if r.codigo == 1:
        raise Fallo(f"terraform plan falla: {r.motivo}")
    if r.codigo == 0:
        return None
    m = re.search(r"Plan: .*", r.salida)
    return m.group(0) if m else "el plan quiere cambiar algo"


def _salidas(floci: Floci, carpeta: Path) -> dict:
    r = floci.terraform(carpeta, "output", "-json")
    return {k: v.get("value") for k, v in (r.json or {}).items()} if r.codigo == 0 else {}


def _denegado(r: Salida) -> bool:
    return r.codigo != 0 and re.search(r"AccessDenied|not authorized|Forbidden|403", r.error, re.I) is not None


# --- Las órdenes aws de ordenes.sh, sin shell -------------------------------------------------

SERVICIOS = {"s3", "s3api", "iam", "sts"}
SIN_VALOR = {"--no-cli-pager", "--debug"}
FUERA = {"--endpoint-url", "--profile", "--region", "--output"}  # las pone el corrector


def ordenes_aws(texto: str) -> list[list[str]]:
    """Las órdenes de ordenes.sh, ya validadas: solo aws de s3, s3api, iam y sts, sin variables ni
    redirecciones, y con los ficheros dentro de la carpeta del ejercicio. Si no, Fallo con la línea."""
    resultado = []
    for n, linea in enumerate(re.sub(r"\\\n", " ", texto).split("\n"), 1):
        try:
            t = shlex.split(linea, comments=True)
        except ValueError:
            raise Fallo(f"ordenes.sh, línea {n}: comillas sin cerrar") from None
        if not t or t[0] in ("set", "#!/bin/sh", "#!/bin/bash") or t[:1] == ["export"] and "AWS_" in linea:
            continue
        if t[0] != "aws" or len(t) < 3 or t[1] not in SERVICIOS:
            raise Fallo(f"ordenes.sh, línea {n} («{linea.strip()}»): solo se admiten órdenes aws de s3, s3api, iam o sts, una por línea")
        if any(set(x) & set("$;|&`<>") for x in t):
            raise Fallo(f"ordenes.sh, línea {n}: lleva variables o caracteres de la shell; escribe los valores tal cual")
        limpio, i = [], 1
        while i < len(t):
            if t[i] in FUERA:
                i += 2
            elif t[i].split("=", 1)[0] in FUERA:
                i += 1
            elif t[i] in SIN_VALOR:
                i += 1
            else:
                limpio.append(t[i])
                i += 1
        for x in limpio:
            ruta = x.removeprefix("file://").removeprefix("fileb://")
            if (x.startswith(("file://", "fileb://")) or not x.startswith(("s3://", "-", "arn:"))) and (
                    ruta.startswith(("/", "\\")) or ".." in Path(ruta).parts or re.match(r"[A-Za-z]:", ruta)):
                raise Fallo(f"ordenes.sh, línea {n}: {x} está fuera de la carpeta del ejercicio")
        resultado.append(limpio)
    if not resultado:
        raise Fallo("ordenes.sh no tiene ninguna orden aws")
    return resultado


def _repetir_e1(caso: Caso, floci: Floci) -> None:
    carpeta = caso.de("e1")
    caso.exigir("ordenes.sh", carpeta=carpeta)
    for orden in ordenes_aws(caso.leer("ordenes.sh", carpeta)):
        if (r := floci.aws(*orden, carpeta=carpeta)).codigo:
            raise Fallo(f"ordenes.sh falla en una cuenta nueva, en «aws {shlex.join(orden)}»: {r.motivo}")


def _clave_nueva(floci: Floci, usuario: str) -> tuple[str, str] | None:
    r = floci.aws("iam", "create-access-key", "--user-name", usuario)
    k = (r.json or {}).get("AccessKey") if r.codigo == 0 else None
    return (k["AccessKeyId"], k["SecretAccessKey"]) if k else None


# --- E1 · A mano, una vez ------------------------------------------------------------------

def e1(caso: Caso) -> Iterator[str]:
    n = p.e1_nombres(caso.usuario)
    with Floci() as floci:
        _repetir_e1(caso, floci)
        r = floci.aws("s3", "cp", f"s3://{n['bucket']}/{n['objeto']}", "-")
        if r.codigo:
            yield f"no hay s3://{n['bucket']}/{n['objeto']}: {r.motivo}"
        elif r.salida.replace("\r\n", "\n").strip() != p.e1_notas(caso.usuario).strip():
            yield f"s3://{n['bucket']}/{n['objeto']} no tiene el contenido de notas.txt: súbelo tal cual"
        if floci.aws("iam", "get-user", "--user-name", n["usuario"]).codigo:
            yield f"no existe el usuario {n['usuario']}"
            return
        if floci.aws("iam", "get-user-policy", "--user-name", n["usuario"], "--policy-name", "lectura-notas").codigo:
            yield f"{n['usuario']} no tiene una política en línea llamada lectura-notas"
        if not (clave := _clave_nueva(floci, n["usuario"])):
            yield f"no se puede crear una clave para {n['usuario']}"
            return
        if (r := floci.aws("s3api", "get-object", "--bucket", n["bucket"], "--key", n["objeto"], "/tmp/x", clave=clave)).codigo:
            yield f"con su clave, {n['usuario']} no puede leer {n['objeto']}: {r.motivo}. Le falta s3:GetObject sobre el bucket"
        if not _denegado(floci.aws("s3api", "delete-object", "--bucket", n["bucket"], "--key", n["objeto"], clave=clave)):
            yield f"con su clave, {n['usuario']} puede borrar {n['objeto']}: la política solo debe dejarle leer"
        if not _denegado(floci.aws("iam", "list-users", clave=clave)):
            yield f"con su clave, {n['usuario']} puede listar usuarios de IAM: la política solo debe darle lectura del bucket"


# --- E2 · Inventario de una cuenta -------------------------------------------------------

def _apartados(markdown: str) -> int:
    return sum(1 for l in markdown.splitlines() if re.match(r"\s*([-*]|\d+[.)])\s+\S", l))


def e2(caso: Caso) -> Iterator[str]:
    caso.exigir("inventario.md")
    texto = caso.leer("inventario.md")
    nombres = p.empresa(caso.usuario)
    if faltan := [v for k, v in nombres.items() if v not in texto]:
        yield f"inventario.md no tiene todos los recursos de la cuenta: faltan {', '.join(faltan)}"
    if "0.0.0.0/0" not in texto or not re.search(r"\b22\b", texto):
        yield "inventario.md no dice qué puertos del grupo de seguridad están abiertos y a quién (0.0.0.0/0, 22, 80)"
    if not re.search(r"(?i)atacante", texto) or _apartados(texto) < 3:
        yield "inventario.md no señala, en una lista, al menos tres cosas que un atacante miraría primero"


# --- E3 · De la CLI al código --------------------------------------------------------------

def _con_import(caso: Caso) -> Iterator[str]:
    codigo = "\n".join(caso.leer(f.name) for f in caso.carpeta.glob("*.tf"))
    for recurso in ("aws_s3_bucket", "aws_iam_user", "aws_iam_user_policy"):
        if not re.search(rf'resource\s+"{recurso}"', codigo):
            yield f"falta un resource {recurso} con lo que creaste en el E1"
    if not re.search(r"^\s*import\s*\{", codigo, re.M):
        yield "no hay ningún bloque import: el ejercicio es adoptar lo que ya existe, no crearlo de nuevo"


def e3(caso: Caso) -> Iterator[str]:
    caso.exigir("main.tf", "proveedor.tf")
    yield from _con_import(caso)
    with Floci() as floci:
        _repetir_e1(caso, floci)
        _init(floci, caso.carpeta)
        plan = floci.terraform(caso.carpeta, "plan", "-no-color")
        if plan.codigo:
            raise Fallo(f"terraform plan falla: {plan.motivo}")
        resumen = re.search(r"Plan: (\d+) to import, (\d+) to add, (\d+) to change, (\d+) to destroy", plan.salida)
        if not resumen:
            yield "el primer plan no importa nada: con lo del E1 creado, tiene que decir «N to import»"
        elif resumen.groups()[1:] != ("0", "0", "0"):
            yield (f"el primer plan no solo importa: {resumen.group(0)}. Ajusta el código a lo que creaste hasta "
                   "que sea «0 to add, 0 to change, 0 to destroy»")
        _apply(floci, caso.carpeta)
        if cambio := _plan_vacio(floci, caso.carpeta):
            yield f"después de apply, el plan aún quiere cambiar algo ({cambio}): un segundo apply no debe hacer nada"


# --- E4 · Variables y deriva ----------------------------------------------------------------

def e4(caso: Caso) -> Iterator[str]:
    caso.exigir("main.tf", "proveedor.tf", "deriva.md")
    codigo = "\n".join(caso.leer(f.name) for f in caso.carpeta.glob("*.tf"))
    if len(re.findall(r'^\s*variable\s+"(?!floci")', codigo, re.M)) < 1:
        yield "no hay ninguna variable propia: saca al menos los nombres a variables"
    n = p.e1_nombres(caso.usuario)
    with Floci() as floci:
        _repetir_e1(caso, floci)
        _init(floci, caso.carpeta)
        _apply(floci, caso.carpeta)
        salidas = _salidas(floci, caso.carpeta)
        if n["bucket"] not in json.dumps(salidas) or n["usuario"] not in json.dumps(salidas):
            yield f"los outputs no dan el nombre del bucket y del usuario: terraform output da {salidas or 'nada'}"
        if cambio := _plan_vacio(floci, caso.carpeta):
            yield f"recién aplicado, el plan aún quiere cambiar algo ({cambio})"
        floci.aws(*shlex.split(p.e4_deriva(caso.usuario))[1:])
        if not _plan_vacio(floci, caso.carpeta):
            yield "tras borrar a mano la política lectura-notas, el plan no lo ve: ¿la gestiona tu código?"
        _apply(floci, caso.carpeta)
        if floci.aws("iam", "get-user-policy", "--user-name", n["usuario"], "--policy-name", "lectura-notas").codigo:
            yield "después de apply, la política lectura-notas no ha vuelto"
    if "lectura-notas" not in caso.leer("deriva.md"):
        yield "deriva.md no dice qué cambió a mano: nombra la política que desapareció y cómo lo viste en el plan"


# --- E5 y E6 · Laboratorios ------------------------------------------------------------------

def _describir(floci: Floci, *args: str) -> dict:
    r = floci.aws(*args)
    return r.json or {} if r.codigo == 0 else {}


def _laboratorio(floci: Floci, vpc: dict, pagina: str | None) -> Iterator[str]:
    """Lo que tiene que cumplir un laboratorio dentro de su VPC."""
    vid = vpc["VpcId"]
    nombre = next((t["Value"] for t in vpc.get("Tags", []) if t["Key"] == "Name"), vid)
    subredes = _describir(floci, "ec2", "describe-subnets", "--filters", f"Name=vpc-id,Values={vid}").get("Subnets", [])
    if len(subredes) < 3:
        yield f"{nombre}: tiene {len(subredes)} subredes y necesita al menos tres: una pública y dos privadas"
    instancias = [i for r in _describir(floci, "ec2", "describe-instances", "--filters", f"Name=vpc-id,Values={vid}")
                  .get("Reservations", []) for i in r.get("Instances", [])]
    if not instancias:
        yield f"{nombre}: no hay ningún servidor EC2 en la VPC"
        return
    grupos = {g["GroupId"]: g for g in _describir(floci, "ec2", "describe-security-groups", "--filters",
                                                   f"Name=vpc-id,Values={vid}").get("SecurityGroups", [])}
    web = instancias[0]
    sg_web = {g["GroupId"] for g in web.get("SecurityGroups", [])}
    if pagina is not None:
        datos = _describir(floci, "ec2", "describe-instance-attribute", "--instance-id", web["InstanceId"], "--attribute", "userData")
        try:
            script = base64.b64decode((datos.get("UserData") or {}).get("Value", "")).decode("utf-8", "replace")
        except ValueError:
            script = ""
        if pagina not in script:
            yield f"{nombre}: el user_data del servidor web no escribe tu página («{pagina}»)"
    abiertos = [(perm.get("FromPort"), r.get("CidrIp")) for gid in sg_web for perm in grupos.get(gid, {}).get("IpPermissions", [])
                for r in perm.get("IpRanges", [])]
    if (80, "0.0.0.0/0") not in abiertos:
        yield f"{nombre}: el grupo de seguridad del servidor web no abre el 80 a todo el mundo"
    if any(puerto not in (80, 443) and cidr == "0.0.0.0/0" for puerto, cidr in abiertos):
        yield f"{nombre}: el servidor web abre a todo el mundo algo más que la web: {abiertos}"
    bases = [d for d in _describir(floci, "rds", "describe-db-instances").get("DBInstances", [])
             if d.get("DBSubnetGroup", {}).get("VpcId") == vid]
    if not bases:
        yield f"{nombre}: no hay ninguna base de datos RDS en la VPC"
        return
    db = bases[0]
    if db.get("PubliclyAccessible"):
        yield f"{nombre}: la base de datos es accesible desde fuera (publicly_accessible)"
    for g in db.get("VpcSecurityGroups", []):
        for perm in grupos.get(g["VpcSecurityGroupId"], {}).get("IpPermissions", []):
            if perm.get("IpRanges"):
                yield f"{nombre}: el grupo de la base de datos admite direcciones ({perm['IpRanges'][0].get('CidrIp')}); solo debe admitir el grupo del servidor web"
            if perm.get("UserIdGroupPairs") and not {x["GroupId"] for x in perm["UserIdGroupPairs"]} <= sg_web:
                yield f"{nombre}: el grupo de la base de datos admite otro grupo que no es el del servidor web"
    if not any(perm.get("UserIdGroupPairs") for g in db.get("VpcSecurityGroups", [])
               for perm in grupos.get(g["VpcSecurityGroupId"], {}).get("IpPermissions", [])):
        yield f"{nombre}: el grupo de la base de datos no deja entrar al servidor web"


def _vpcs_propias(floci: Floci) -> list[dict]:
    return [v for v in _describir(floci, "ec2", "describe-vpcs").get("Vpcs", []) if not v.get("IsDefault")]


def e5(caso: Caso) -> Iterator[str]:
    caso.exigir("proveedor.tf")
    pagina = p.e5_pagina(caso.usuario)
    with Floci() as floci:
        _init(floci, caso.carpeta)
        _apply(floci, caso.carpeta)
        vpcs = _vpcs_propias(floci)
        if len(vpcs) != 1:
            raise Fallo(f"el laboratorio tiene que crear una VPC y ha creado {len(vpcs)}")
        yield from _laboratorio(floci, vpcs[0], pagina)
        salidas = json.dumps(_salidas(floci, caso.carpeta))
        if not re.search(r"\d+\.\d+\.\d+\.\d+", salidas):
            yield "los outputs no dan la IP del servidor web"
        if (r := floci.terraform(caso.carpeta, "destroy", "-auto-approve", "-no-color")).codigo:
            yield f"terraform destroy falla: {r.motivo}"
        elif _vpcs_propias(floci):
            yield "después de destroy queda alguna VPC: el laboratorio no se borra entero"


def e6(caso: Caso) -> Iterator[str]:
    caso.exigir("proveedor.tf")
    modulos = [d for d in (caso.carpeta / "modulos").glob("*") if d.is_dir()] if (caso.carpeta / "modulos").is_dir() else []
    if not modulos:
        raise Fallo("no hay ningún módulo en modulos/: el laboratorio va en modulos/lab/")
    raiz = "\n".join(caso.leer(f.name) for f in caso.carpeta.glob("*.tf"))
    if len(re.findall(r'^\s*module\s+"', raiz, re.M)) < 2:
        yield "la raíz no usa el módulo dos veces: levanta dos laboratorios con él"
    if re.search(r'resource\s+"aws_(vpc|instance|db_instance)"', raiz):
        yield "la raíz crea recursos del laboratorio directamente: todo tiene que ir dentro del módulo"
    with Floci() as floci:
        _init(floci, caso.carpeta)
        _apply(floci, caso.carpeta)
        vpcs = _vpcs_propias(floci)
        if len(vpcs) < 2:
            yield f"los dos laboratorios tienen que tener su propia VPC y hay {len(vpcs)}"
        nombres = [next((t["Value"] for t in v.get("Tags", []) if t["Key"] == "Name"), "") for v in vpcs]
        if len(set(nombres)) != len(nombres) or "" in nombres:
            yield f"las VPC no tienen nombres distintos (etiqueta Name): {nombres}"
        if len({v["CidrBlock"] for v in vpcs}) != len(vpcs):
            yield "las VPC de los dos laboratorios usan el mismo rango: pásalo como variable"
        for vpc in vpcs:
            yield from _laboratorio(floci, vpc, None)
        if (r := floci.terraform(caso.carpeta, "destroy", "-auto-approve", "-no-color")).codigo:
            yield f"terraform destroy falla: {r.motivo}"


# --- E7 y E8 · Los permisos de la empresa ---------------------------------------------------

ESCALADA = ("iam:PutUserPolicy", "iam:AttachUserPolicy", "iam:CreateAccessKey", "iam:CreatePolicyVersion")


def _arn(floci: Floci, usuario: str) -> str | None:
    r = floci.aws("iam", "get-user", "--user-name", usuario)
    return ((r.json or {}).get("User") or {}).get("Arn") if r.codigo == 0 else None


def _permitidas(floci: Floci, arn: str, acciones: tuple[str, ...], recurso: str) -> list[str]:
    """Las acciones que las políticas del usuario le permiten sobre el recurso, según simulate-principal-policy.
    Para los permisos de IAM se simula sobre su propio usuario: es lo que el becario tenía permitido."""
    r = floci.aws("iam", "simulate-principal-policy", "--policy-source-arn", arn,
                  "--action-names", *acciones, "--resource-arns", recurso)
    if r.codigo:
        raise RuntimeError(f"simulate-principal-policy: {r.motivo}")
    return [x["EvalActionName"] for x in (r.json or {}).get("EvaluationResults", []) if x.get("EvalDecision") == "allowed"]


def _simulacion(texto: str) -> dict:
    try:
        datos = json.loads(texto)
    except ValueError:
        return {}
    if not isinstance(datos, dict):
        return {}
    return {x.get("EvalActionName"): x.get("EvalDecision") for x in datos.get("EvaluationResults", [])}


def e7(caso: Caso) -> Iterator[str]:
    caso.exigir("auditoria.md", "simulacion.json")
    nombres = p.empresa(caso.usuario)
    simulado = _simulacion(caso.leer("simulacion.json"))
    if not simulado:
        yield "simulacion.json no es la salida JSON de aws iam simulate-principal-policy"
    elif simulado.get("iam:PutUserPolicy") != "allowed":
        yield ("simulacion.json no muestra el riesgo: simula al becario con la acción iam:PutUserPolicy "
               "sobre su propio usuario, y tiene que salir «allowed»")
    texto = caso.leer("auditoria.md")
    for que, patron in ((f"la política del becario ({nombres['becario']}, becario-trabajo)", r"becario-trabajo"),
                        ("la acción que le deja cambiarse los permisos", r"iam:PutUserPolicy"),
                        (f"la política de operaciones ({nombres['operaciones']}, operaciones-todo)", r"operaciones-todo"),
                        ("la clave del becario que acabó en un repositorio público", r"(?i)clave"),
                        ("el CWE de la gestión de privilegios (CWE-269)", r"CWE-269")):
        if not re.search(patron, texto):
            yield f"auditoria.md no habla de {que}"
    for pregunta, patron in (("dónde está", r"(?i)d[oó]nde"), ("qué riesgo tiene", r"(?i)riesgo"),
                             ("cómo se corrige", r"(?i)corrig|correcci")):
        if not re.search(patron, texto):
            yield f"auditoria.md no responde a «{pregunta}» en cada hallazgo"
    if len(set(re.findall(r"CWE-\d+", texto))) < 2:
        yield "auditoria.md no da el CWE de cada hallazgo: hay al menos dos distintos"


def e8(caso: Caso) -> Iterator[str]:
    carpeta = caso.carpeta / "empresa"
    caso.exigir("empresa.tf", "proveedor.tf", carpeta=carpeta)
    nombres = p.empresa(caso.usuario)
    secretos = f"arn:aws:s3:::{nombres['secretos']}/*"
    with Floci() as floci:
        _init(floci, carpeta)
        _apply(floci, carpeta)
        for clave in ("copias", "informes", "secretos"):
            if floci.aws("s3api", "head-bucket", "--bucket", nombres[clave]).codigo:
                yield f"el bucket {nombres[clave]} ya no existe: corregir no es borrar"
        becario, operaciones = _arn(floci, nombres["becario"]), _arn(floci, nombres["operaciones"])
        if not becario or not operaciones:
            raise Fallo(f"faltan los usuarios {nombres['becario']} y {nombres['operaciones']}: corregir no es borrar")
        claves = floci.aws("iam", "list-access-keys", "--user-name", nombres["becario"])
        if (claves.json or {}).get("AccessKeyMetadata"):
            yield "el becario sigue teniendo una clave de acceso: la que se filtró hay que revocarla (quítala del código)"
        if escalada := _permitidas(floci, becario, ESCALADA, becario):
            yield f"el becario todavía puede tocar permisos de IAM ({', '.join(escalada)}): quítale AjustarseLosPermisos"
        if _permitidas(floci, becario, ("s3:GetObject",), secretos):
            yield f"el becario puede leer {nombres['secretos']}"
        if not (clave := _clave_nueva(floci, nombres["becario"])):
            yield f"no se puede crear una clave para {nombres['becario']}"
        elif floci.aws("s3api", "get-object", "--bucket", nombres["informes"], "--key", "informe-semanal.txt",
                       "/tmp/x", clave=clave).codigo:
            yield "el becario ya no puede leer los informes: tiene que seguir haciendo su trabajo"
        if escalada := _permitidas(floci, operaciones, ESCALADA, operaciones):
            yield f"operaciones todavía puede tocar permisos de IAM ({', '.join(escalada)}): dale solo lo que necesita"
        if _permitidas(floci, operaciones, ("s3:GetObject",), secretos):
            yield f"operaciones puede leer {nombres['secretos']}: dale solo lo que necesita"
        if not _permitidas(floci, operaciones, ("ec2:DescribeInstances",), "*"):
            yield "operaciones ya no puede ver los servidores (ec2:DescribeInstances): tiene que seguir administrándolos"


COMPROBACIONES: dict[str, Comprobacion] = {"e1": e1, "e2": e2, "e3": e3, "e4": e4, "e5": e5, "e6": e6, "e7": e7, "e8": e8}
