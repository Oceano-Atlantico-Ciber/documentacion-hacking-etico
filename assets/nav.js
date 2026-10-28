// Índice lateral con el árbol de todo el sitio. Cada página lo carga con una ruta relativa
// (<script src="../assets/nav.js" defer>), así que funciona igual en Pages que abriendo el repo
// descargado. Su aspecto está en estilo.css. Para añadir una página, añade su nodo a ARBOL: [título, ruta desde la raíz, hijos].
(() => {
  const ARBOL = [
    ["Inicio", "index.html"],
    ["Presentación", "00-presentacion/index.html", [
      ["01 · Quién soy", "00-presentacion/docs/01-quien-soy.html"],
      ["02 · Cómo funciona la asignatura", "00-presentacion/docs/02-como-funciona-la-asignatura.html"],
      ["03 · Git y GitHub", "00-presentacion/docs/03-git-y-github.html"],
      ["04 · Docker", "00-presentacion/docs/04-docker.html"],
      ["05 · IA: local o en la nube", "00-presentacion/docs/05-ia.html"],
      ["06 · Primer commit", "00-presentacion/docs/06-primer-commit.html"],
    ]],
    ["Fundamentos", "01-fundamentos/index.html", [
      ["Temas", "01-fundamentos/index.html#temas", [
        ["01 · Git", "01-fundamentos/index.html#01-git", [
          ["Git 1 · Modelo y commits", "01-fundamentos/docs/01-git/01-modelo-y-commits.html"],
          ["Git 2 · Ramas y fusiones", "01-fundamentos/docs/01-git/02-ramas-y-fusiones.html"],
          ["Git 3 · Remotos y reescribir historia", "01-fundamentos/docs/01-git/03-remotos-y-reescribir-historia.html"],
          ["Git 4 · Deshacer y seguridad", "01-fundamentos/docs/01-git/04-deshacer-y-seguridad.html"],
        ]],
        ["02 · Docker", "01-fundamentos/index.html#02-docker", [
          ["Docker 1 · Imágenes y contenedores", "01-fundamentos/docs/02-docker/01-imagenes-y-contenedores.html"],
          ["Docker 2 · Construir imágenes", "01-fundamentos/docs/02-docker/02-construir-imagenes.html"],
          ["Docker 3 · Datos y redes", "01-fundamentos/docs/02-docker/03-datos-y-redes.html"],
          ["Docker 4 · Compose y seguridad", "01-fundamentos/docs/02-docker/04-compose-y-seguridad.html"],
        ]],
        ["API REST", "01-fundamentos/index.html#api-rest", [
          ["API REST 1 · Cliente, servidor y HTTP", "01-fundamentos/docs/api-rest/01-cliente-servidor-y-http.html"],
          ["API REST 2 · Métodos, códigos y cabeceras", "01-fundamentos/docs/api-rest/02-metodos-codigos-y-cabeceras.html"],
          ["API REST 3 · F12, curl y seguridad", "01-fundamentos/docs/api-rest/03-f12-curl-y-seguridad.html"],
          ["API REST 4 · Hackea el ranking", "01-fundamentos/docs/api-rest/04-hackea-el-ranking.html"],
        ]],
        ["Ética y seguridad", "01-fundamentos/index.html#etica-y-seguridad", [
          ["Ética, ley y alcance", "01-fundamentos/docs/etica-y-seguridad/01-etica-ley-y-alcance.html"],
          ["Seguridad, vulnerabilidades y ataques", "01-fundamentos/docs/etica-y-seguridad/02-seguridad-y-vulnerabilidades.html"],
        ]],
        ["Empresa con Terraform", "01-fundamentos/index.html#empresa-con-terraform", [
          ["La empresa en Floci", "01-fundamentos/docs/empresa-con-terraform/01-la-empresa-en-floci.html"],
        ]],
        ["Mini auditoría", "01-fundamentos/index.html#mini-auditoria", [
          ["Fases de un ataque y auditoría vigilada", "01-fundamentos/docs/mini-auditoria/01-fases-y-auditoria.html"],
          ["Herramientas y darknets", "01-fundamentos/docs/mini-auditoria/02-herramientas-y-darknets.html"],
        ]],
      ]],
      ["Ejercicios", "01-fundamentos/ejercicios/index.html", [
        ["01 · Git", "01-fundamentos/ejercicios/index.html#01-git", [
          ["E1 · Identidad y commits atómicos", "01-fundamentos/ejercicios/01-git/e1.html"],
          ["E2 · .gitignore", "01-fundamentos/ejercicios/01-git/e2.html"],
          ["E3 · Fusiones", "01-fundamentos/ejercicios/01-git/e3.html"],
          ["E4 · Conflicto", "01-fundamentos/ejercicios/01-git/e4.html"],
          ["E5 · Rebase", "01-fundamentos/ejercicios/01-git/e5.html"],
          ["E6 · Rebase interactivo", "01-fundamentos/ejercicios/01-git/e6.html"],
          ["E7 · Revert", "01-fundamentos/ejercicios/01-git/e7.html"],
          ["E8 · Secreto filtrado", "01-fundamentos/ejercicios/01-git/e8.html"],
        ]],
        ["02 · Docker", "01-fundamentos/ejercicios/index.html#02-docker", [
          ["E1 · Ciclo de vida", "01-fundamentos/ejercicios/02-docker/e1.html"],
          ["E2 · Tu primera imagen", "01-fundamentos/ejercicios/02-docker/e2.html"],
          ["E3 · Capas, caché y .dockerignore", "01-fundamentos/ejercicios/02-docker/e3.html"],
          ["E4 · El secreto de la capa", "01-fundamentos/ejercicios/02-docker/e4.html"],
          ["E5 · Datos que sobreviven", "01-fundamentos/ejercicios/02-docker/e5.html"],
          ["E6 · Red y puertos", "01-fundamentos/ejercicios/02-docker/e6.html"],
          ["E7 · Tu primer compose", "01-fundamentos/ejercicios/02-docker/e7.html"],
          ["E8 · Auditar un compose", "01-fundamentos/ejercicios/02-docker/e8.html"],
        ]],
        ["API REST", "01-fundamentos/ejercicios/index.html#api-rest", [
          ["Hackea el ranking · Solución", "01-fundamentos/ejercicios/api-rest/hackea-el-ranking/solucion.html"],
        ]],
        ["Empresa con Terraform", "01-fundamentos/ejercicios/index.html#empresa-con-terraform", [
          ["Puesta en marcha del laboratorio", "01-fundamentos/ejercicios/empresa-con-terraform/puesta-en-marcha.html"],
        ]],
        ["Mini auditoría", "01-fundamentos/ejercicios/index.html#mini-auditoria"],
      ]],
      ["Casos analizados", "01-fundamentos/casos-analizados/index.html", [
        ["Hackea el ranking", "01-fundamentos/docs/api-rest/04-hackea-el-ranking.html#documentar"],
        ["PHP2Shell", "01-fundamentos/casos-analizados/cve-2026-109618-php2shell.html"],
      ]],
    ]],
    ["Redes inalámbricas", "02-redes-inalambricas/index.html"],
    ["Redes y sistemas", "03-redes-y-sistemas/index.html"],
    ["Sistemas comprometidos", "04-sistemas-comprometidos/index.html"],
    ["Aplicaciones web", "05-aplicaciones-web/index.html"],
    ["Glosario", "glosario/index.html"],
  ];

  const raiz = new URL("../", document.currentScript.src);
  // Pages sirve «carpeta/» como «carpeta/index.html»: las dos formas son la misma página.
  const pagina = (url) => url.origin + url.pathname.replace(/\/$/, "/index.html");

  const enlaces = [];
  const lista = (nodos) => {
    const ul = document.createElement("ul");
    for (const [titulo, ruta, hijos] of nodos) {
      const li = document.createElement("li");
      const a = document.createElement("a");
      a.href = new URL(ruta, raiz).href;
      a.textContent = titulo;
      enlaces.push(a);
      if (hijos) {
        const details = document.createElement("details");
        const summary = document.createElement("summary");
        summary.append(a);
        details.append(summary, lista(hijos));
        li.append(details);
      } else {
        li.append(a);
      }
      ul.append(li);
    }
    return ul;
  };
  const nav = document.createElement("nav");
  nav.id = "arbol";
  nav.setAttribute("aria-label", "Índice del curso");
  nav.append(lista(ARBOL));

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

  document.body.append(nav, boton);

  // Marca el enlace de la página actual: el de su ancla si lo hay, si no el de la página sin
  // ancla. Abre sus ramas y lo deja a la vista. Se repite al navegar entre anclas.
  const marcar = () => {
    const aqui = new URL(location.href);
    const candidatos = enlaces.filter((a) => pagina(new URL(a.href)) === pagina(aqui));
    const elegido = candidatos.find((a) => a.hash && a.hash === aqui.hash)
      ?? candidatos.find((a) => !a.hash) ?? candidatos[0];
    for (const a of enlaces) a.removeAttribute("aria-current");
    if (!elegido) return;
    elegido.setAttribute("aria-current", "page");
    for (let d = elegido.closest("details"); d; d = d.parentElement.closest("details")) d.open = true;
    const caja = nav.getBoundingClientRect(), fila = elegido.getBoundingClientRect();
    if (fila.top < caja.top || fila.bottom > caja.bottom) nav.scrollTop += fila.top - caja.top - caja.height / 2;
  };
  marcar();
  addEventListener("hashchange", marcar);
})();
