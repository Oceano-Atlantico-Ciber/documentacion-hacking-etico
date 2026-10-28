// Índice lateral con el árbol de todo el sitio. Cada página lo carga con una ruta relativa
// (<script src="../assets/nav.js" defer>), así que funciona igual en Pages que abriendo el repo
// descargado. Para añadir una página, añade su nodo a ARBOL: [título, ruta desde la raíz, hijos].
(() => {
  const ARBOL = [
    ["Inicio", "index.html"],
    ["Presentación", "00-presentacion/index.html", [
      ["01 · Quién soy", "00-presentacion/docs/01-quien-soy.html"],
      ["02 · Cómo funciona la asignatura", "00-presentacion/docs/02-como-funciona-la-asignatura.html"],
      ["03 · Git y GitHub", "00-presentacion/docs/03-git-y-github.html"],
      ["04 · Docker", "00-presentacion/docs/04-docker.html"],
      ["05 · IA: local o en la nube", "00-presentacion/docs/05-ia.html"],
      ["06 · Hackea el ranking", "00-presentacion/docs/06-hackea-el-ranking.html"],
      ["07 · Primer commit", "00-presentacion/docs/07-primer-commit.html"],
      ["08 · Qué es una API REST", "00-presentacion/docs/08-api-rest.html"],
      ["Ejercicios", "00-presentacion/ejercicios/index.html"],
    ]],
    ["Fundamentos", "01-fundamentos/index.html", [
      ["01 · Git", "01-fundamentos/ejercicios/index.html#01-git", [
        ["Git 1 · Modelo y commits", "01-fundamentos/docs/01-git/01-modelo-y-commits.html"],
        ["Git 2 · Ramas y fusiones", "01-fundamentos/docs/01-git/02-ramas-y-fusiones.html"],
        ["Git 3 · Remotos y reescribir historia", "01-fundamentos/docs/01-git/03-remotos-y-reescribir-historia.html"],
        ["Git 4 · Deshacer y seguridad", "01-fundamentos/docs/01-git/04-deshacer-y-seguridad.html"],
        ["E1 · Identidad y commits atómicos", "01-fundamentos/ejercicios/01-git/e1.html"],
        ["E2 · .gitignore", "01-fundamentos/ejercicios/01-git/e2.html"],
        ["E3 · Fusiones", "01-fundamentos/ejercicios/01-git/e3.html"],
        ["E4 · Conflicto", "01-fundamentos/ejercicios/01-git/e4.html"],
        ["E5 · Rebase", "01-fundamentos/ejercicios/01-git/e5.html"],
        ["E6 · Rebase interactivo", "01-fundamentos/ejercicios/01-git/e6.html"],
        ["E7 · Revert", "01-fundamentos/ejercicios/01-git/e7.html"],
        ["E8 · Secreto filtrado", "01-fundamentos/ejercicios/01-git/e8.html"],
      ]],
      ["Ética, ley y alcance", "01-fundamentos/docs/etica-ley-y-alcance.html"],
      ["Seguridad, vulnerabilidades y ataques", "01-fundamentos/docs/seguridad-y-vulnerabilidades.html"],
      ["La empresa en Floci", "01-fundamentos/docs/la-empresa-en-floci.html"],
      ["Fases de un ataque y auditoría vigilada", "01-fundamentos/docs/fases-y-auditoria.html"],
      ["Herramientas y darknets", "01-fundamentos/docs/herramientas-y-darknets.html"],
      ["Ejercicios", "01-fundamentos/ejercicios/index.html", [
        ["Empresa con Terraform", "01-fundamentos/ejercicios/index.html#empresa-con-terraform"],
        ["Puesta en marcha del laboratorio", "01-fundamentos/ejercicios/empresa-con-terraform/puesta-en-marcha.html"],
        ["Mini auditoría", "01-fundamentos/ejercicios/index.html#mini-auditoria"],
      ]],
      ["CVE analizados", "01-fundamentos/cve/index.html", [
        ["PHP2Shell", "01-fundamentos/cve/cve-2026-109618-php2shell.html"],
      ]],
    ]],
    ["Redes inalámbricas", "02-redes-inalambricas/index.html"],
    ["Redes y sistemas", "03-redes-y-sistemas/index.html"],
    ["Sistemas comprometidos", "04-sistemas-comprometidos/index.html"],
    ["Aplicaciones web", "05-aplicaciones-web/index.html"],
    ["Glosario", "glosario.html"],
  ];

  const raiz = new URL("../", document.currentScript.src);
  // Pages sirve «carpeta/» como «carpeta/index.html»: las dos formas son la misma página.
  const pagina = (url) => url.origin + url.pathname.replace(/\/$/, "/index.html");
  const actual = pagina(new URL(location.href));

  // La página actual es el primer nodo con su ruta, prefiriendo el que no lleva ancla.
  const coincidencias = [];
  const recorrer = (nodos) => nodos.forEach((nodo) => {
    nodo.url = new URL(nodo[1], raiz);
    if (pagina(nodo.url) === actual) coincidencias.push(nodo);
    if (nodo[2]) recorrer(nodo[2]);
  });
  recorrer(ARBOL);
  const marcado = coincidencias.find((n) => !n.url.hash) ?? coincidencias[0];

  const enlace = (nodo) => {
    const a = document.createElement("a");
    a.href = nodo.url.href;
    a.textContent = nodo[0];
    if (nodo === marcado) a.setAttribute("aria-current", "page");
    return a;
  };
  // Devuelve la lista y si contiene la página actual, para abrir sus ramas.
  const lista = (nodos) => {
    const ul = document.createElement("ul");
    let contiene = false;
    for (const nodo of nodos) {
      const li = document.createElement("li");
      if (nodo[2]) {
        const [hijos, dentro] = lista(nodo[2]);
        const details = document.createElement("details");
        const summary = document.createElement("summary");
        summary.append(enlace(nodo));
        details.append(summary, hijos);
        details.open = dentro || nodo === marcado;
        li.append(details);
        contiene ||= details.open;
      } else {
        li.append(enlace(nodo));
        contiene ||= nodo === marcado;
      }
      ul.append(li);
    }
    return [ul, contiene];
  };

  const nav = document.createElement("nav");
  nav.id = "arbol";
  nav.setAttribute("aria-label", "Índice del curso");
  nav.append(lista(ARBOL)[0]);

  const boton = document.createElement("button");
  boton.id = "arbol-boton";
  boton.type = "button";
  boton.textContent = "Índice";
  boton.setAttribute("aria-controls", nav.id);
  boton.setAttribute("aria-expanded", "false");
  const abrir = (si) => {
    document.documentElement.classList.toggle("arbol-abierto", si);
    boton.setAttribute("aria-expanded", String(si));
  };
  boton.addEventListener("click", () => abrir(boton.getAttribute("aria-expanded") === "false"));
  document.addEventListener("keydown", (e) => e.key === "Escape" && abrir(false));
  document.addEventListener("click", (e) => !nav.contains(e.target) && e.target !== boton && abrir(false));

  const estilo = document.createElement("style");
  estilo.textContent = `
#arbol { --arbol-fondo: var(--surface, var(--card, Canvas)); --arbol-texto: var(--ink, var(--fg, CanvasText));
  position: fixed; inset: 0 auto 0 0; width: 280px; overflow-y: auto; z-index: 20; padding: 20px 14px 40px;
  background: var(--arbol-fondo); border-right: 1px solid var(--line); font: 14px/1.4 system-ui, sans-serif; }
#arbol ul { list-style: none; margin: 0; padding: 0 0 0 12px; display: grid; gap: 2px; }
#arbol > ul { padding: 0; }
#arbol a { display: block; padding: 4px 8px; border-radius: 6px; color: var(--arbol-texto); text-decoration: none; }
#arbol a:hover { background: var(--bg); }
#arbol a[aria-current="page"] { color: var(--accent); font-weight: 600; background: var(--bg); }
#arbol summary { display: flex; align-items: center; cursor: pointer; color: var(--muted); }
#arbol summary::marker { content: ""; }
#arbol summary::before { content: "▸"; width: 12px; flex: none; transition: transform .15s; }
#arbol details[open] > summary::before { transform: rotate(90deg); }
#arbol summary a { flex: 1; }
#arbol-boton { position: fixed; right: 16px; bottom: 16px; z-index: 21; padding: 10px 16px; border-radius: 999px;
  border: 1px solid var(--line); background: var(--accent); color: var(--bg); font: 600 14px system-ui, sans-serif; cursor: pointer; }
@media (min-width: 1200px) {
  body { margin-left: 280px; }
  #arbol-boton { display: none; }
}
@media (max-width: 1199px) {
  #arbol { width: min(320px, 85vw); transform: translateX(-100%); visibility: hidden;
    transition: transform .2s, visibility .2s; box-shadow: 0 0 24px rgb(0 0 0 / .2); }
  .arbol-abierto #arbol { transform: none; visibility: visible; }
}
@media print { #arbol, #arbol-boton { display: none; } body { margin-left: 0; } }`;

  document.head.append(estilo);
  document.body.append(nav, boton);
  const elegido = nav.querySelector('[aria-current="page"]');
  if (elegido) nav.scrollTop = elegido.offsetTop - nav.clientHeight / 2;
})();
