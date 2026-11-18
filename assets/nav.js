// Índice lateral con el árbol de todo el sitio. Cada página lo carga con una ruta relativa
// (<script src="../assets/nav.js" defer>), así que funciona igual en Pages que abriendo el repo
// descargado. Su aspecto está en estilo.css. Recuerda las ramas abiertas, el scroll y si la barra está plegada. Para añadir una página, añade su nodo a ARBOL: [título, ruta desde la raíz, hijos].
(() => {
  const ARBOL = [
    ["Inicio", "index.html"],
    ["Presentación", "00-presentacion/index.html", [
      ["01 · Quién soy", "00-presentacion/temas/01-quien-soy.html"],
      ["02 · Cómo funciona la asignatura", "00-presentacion/temas/02-como-funciona-la-asignatura.html"],
      ["03 · Git y GitHub", "00-presentacion/temas/03-git-y-github.html"],
      ["04 · Docker", "00-presentacion/temas/04-docker.html"],
      ["05 · IA: local o en la nube", "00-presentacion/temas/05-ia.html"],
      ["06 · Primer commit", "00-presentacion/temas/06-primer-commit.html"],
      ["07 · Hackea el ranking", "00-presentacion/temas/07-hackea-el-ranking.html"],
      ["Hackea el ranking · Solución", "00-presentacion/hackea-el-ranking/solucion.html"],
    ]],
    ["Fundamentos", "00-fundamentos/index.html", [
      ["01 · Git", "00-fundamentos/01-git/index.html", [
        ["Temas", "00-fundamentos/01-git/index.html#temas", [
          ["Git 1 · Modelo y commits", "00-fundamentos/01-git/temas/01-modelo-y-commits.html"],
          ["Git 2 · Ramas y fusiones", "00-fundamentos/01-git/temas/02-ramas-y-fusiones.html"],
          ["Git 3 · Remotos y reescribir historia", "00-fundamentos/01-git/temas/03-remotos-y-reescribir-historia.html"],
          ["Git 4 · Deshacer y seguridad", "00-fundamentos/01-git/temas/04-deshacer-y-seguridad.html"],
        ]],
        ["Ejercicios", "00-fundamentos/01-git/index.html#ejercicios", [
          ["E1 · Identidad y commits atómicos", "00-fundamentos/01-git/ejercicios/e1.html"],
          ["E2 · .gitignore", "00-fundamentos/01-git/ejercicios/e2.html"],
          ["E3 · Fusiones", "00-fundamentos/01-git/ejercicios/e3.html"],
          ["E4 · Conflicto", "00-fundamentos/01-git/ejercicios/e4.html"],
          ["E5 · Rebase", "00-fundamentos/01-git/ejercicios/e5.html"],
          ["E6 · Rebase interactivo", "00-fundamentos/01-git/ejercicios/e6.html"],
          ["E7 · Revert", "00-fundamentos/01-git/ejercicios/e7.html"],
          ["E8 · Secreto filtrado", "00-fundamentos/01-git/ejercicios/e8.html"],
        ]],
      ]],
      ["02 · Docker", "00-fundamentos/02-docker/index.html", [
        ["Temas", "00-fundamentos/02-docker/index.html#temas", [
          ["Docker 1 · Imágenes y contenedores", "00-fundamentos/02-docker/temas/01-imagenes-y-contenedores.html"],
          ["Docker 2 · Construir imágenes", "00-fundamentos/02-docker/temas/02-construir-imagenes.html"],
          ["Docker 3 · Datos y redes", "00-fundamentos/02-docker/temas/03-datos-y-redes.html"],
          ["Docker 4 · Compose y seguridad", "00-fundamentos/02-docker/temas/04-compose-y-seguridad.html"],
        ]],
        ["Ejercicios", "00-fundamentos/02-docker/index.html#ejercicios", [
          ["E1 · Ciclo de vida", "00-fundamentos/02-docker/ejercicios/e1.html"],
          ["E2 · Tu primera imagen", "00-fundamentos/02-docker/ejercicios/e2.html"],
          ["E3 · Capas, caché y .dockerignore", "00-fundamentos/02-docker/ejercicios/e3.html"],
          ["E4 · El secreto de la capa", "00-fundamentos/02-docker/ejercicios/e4.html"],
          ["E5 · Datos que sobreviven", "00-fundamentos/02-docker/ejercicios/e5.html"],
          ["E6 · Red y puertos", "00-fundamentos/02-docker/ejercicios/e6.html"],
          ["E7 · Tu primer compose", "00-fundamentos/02-docker/ejercicios/e7.html"],
          ["E8 · Auditar un compose", "00-fundamentos/02-docker/ejercicios/e8.html"],
        ]],
      ]],
      ["03 · API REST", "00-fundamentos/03-api-rest/index.html", [
        ["Temas", "00-fundamentos/03-api-rest/index.html#temas", [
          ["API 1 · REST es HTTP", "00-fundamentos/03-api-rest/temas/01-rest-es-http.html"],
          ["API 2 · Diseñar y construir", "00-fundamentos/03-api-rest/temas/02-disenar-y-construir.html"],
          ["API 3 · Buenas prácticas", "00-fundamentos/03-api-rest/temas/03-buenas-practicas.html"],
          ["API 4 · Seguridad", "00-fundamentos/03-api-rest/temas/04-seguridad.html"],
        ]],
        ["Ejercicios", "00-fundamentos/03-api-rest/index.html#ejercicios", [
          ["E1 · HTTP a mano", "00-fundamentos/03-api-rest/ejercicios/e1.html"],
          ["E2 · Diseña el contrato", "00-fundamentos/03-api-rest/ejercicios/e2.html"],
          ["E3 · Primera implementación", "00-fundamentos/03-api-rest/ejercicios/e3.html"],
          ["E4 · Escribir bien", "00-fundamentos/03-api-rest/ejercicios/e4.html"],
          ["E5 · Tres lenguajes, una API", "00-fundamentos/03-api-rest/ejercicios/e5.html"],
          ["E6 · Errores que ayudan", "00-fundamentos/03-api-rest/ejercicios/e6.html"],
          ["E7 · Listas grandes y escrituras a la vez", "00-fundamentos/03-api-rest/ejercicios/e7.html"],
          ["E8 · Una API que se defiende", "00-fundamentos/03-api-rest/ejercicios/e8.html"],
        ]],
      ]],
      ["04 · Terraform y AWS", "00-fundamentos/04-iac/index.html", [
        ["Temas", "00-fundamentos/04-iac/index.html#temas", [
          ["IaC 1 · La nube en tu portátil", "00-fundamentos/04-iac/temas/01-la-nube-en-tu-portatil.html"],
          ["IaC 2 · Terraform", "00-fundamentos/04-iac/temas/02-terraform.html"],
          ["IaC 3 · Redes y servidores", "00-fundamentos/04-iac/temas/03-redes-y-servidores.html"],
          ["IaC 4 · Seguridad de la infraestructura", "00-fundamentos/04-iac/temas/04-seguridad-de-la-infraestructura.html"],
        ]],
        ["Ejercicios", "00-fundamentos/04-iac/index.html#ejercicios", [
          ["E1 · A mano, una vez", "00-fundamentos/04-iac/ejercicios/e1.html"],
          ["E2 · Inventario de una cuenta", "00-fundamentos/04-iac/ejercicios/e2.html"],
          ["E3 · Del clic al código", "00-fundamentos/04-iac/ejercicios/e3.html"],
          ["E4 · Variables y deriva", "00-fundamentos/04-iac/ejercicios/e4.html"],
          ["E5 · Un laboratorio completo", "00-fundamentos/04-iac/ejercicios/e5.html"],
          ["E6 · Un módulo, dos laboratorios", "00-fundamentos/04-iac/ejercicios/e6.html"],
          ["E7 · Auditar los permisos", "00-fundamentos/04-iac/ejercicios/e7.html"],
          ["E8 · Corregir en el código", "00-fundamentos/04-iac/ejercicios/e8.html"],
        ]],
      ]],
    ]],
    ["RA1 · Hacking ético", "01-hacking-etico/index.html", [
      ["01 · Qué es el hacking ético", "01-hacking-etico/01-que-es-el-hacking-etico/index.html", [
        ["Temas", "01-hacking-etico/01-que-es-el-hacking-etico/index.html#temas", [
          ["1.1 · Terminología", "01-hacking-etico/01-que-es-el-hacking-etico/temas/01-terminologia.html"],
          ["1.2 · Ética y ley", "01-hacking-etico/01-que-es-el-hacking-etico/temas/02-etica-y-ley.html"],
        ]],
        ["Ejercicios", "01-hacking-etico/01-que-es-el-hacking-etico/index.html#ejercicios", [
          ["U1·E1 · ¿Hacking ético o delito?", "01-hacking-etico/01-que-es-el-hacking-etico/ejercicios/e1.html"],
          ["U1·E2 · El security.txt de la empresa", "01-hacking-etico/01-que-es-el-hacking-etico/ejercicios/e2.html"],
        ]],
      ]],
      ["02 · Permisos y alcance", "01-hacking-etico/02-permisos-y-alcance/index.html", [
        ["Temas", "01-hacking-etico/02-permisos-y-alcance/index.html#temas", [
          ["2.1 · Tipos de auditoría", "01-hacking-etico/02-permisos-y-alcance/temas/01-tipos-de-auditoria.html"],
          ["2.2 · Autorización y alcance", "01-hacking-etico/02-permisos-y-alcance/temas/02-autorizacion-y-alcance.html"],
        ]],
        ["Ejercicios", "01-hacking-etico/02-permisos-y-alcance/index.html#ejercicios", [
          ["U2·E1 · El alcance de la clínica", "01-hacking-etico/02-permisos-y-alcance/ejercicios/e1.html"],
          ["U2·E2 · Un alcance con fallos", "01-hacking-etico/02-permisos-y-alcance/ejercicios/e2.html"],
        ]],
      ]],
      ["03 · Vulnerabilidades y ataques", "01-hacking-etico/03-vulnerabilidades-y-ataques/index.html", [
        ["Temas", "01-hacking-etico/03-vulnerabilidades-y-ataques/index.html#temas", [
          ["3.1 · Las propiedades de la seguridad", "01-hacking-etico/03-vulnerabilidades-y-ataques/temas/01-propiedades.html"],
          ["3.2 · Fases de un ataque", "01-hacking-etico/03-vulnerabilidades-y-ataques/temas/02-fases-de-un-ataque.html"],
          ["3.3 · Tipos de vulnerabilidades", "01-hacking-etico/03-vulnerabilidades-y-ataques/temas/03-tipos-de-vulnerabilidades.html"],
          ["3.4 · Tipos de ataques", "01-hacking-etico/03-vulnerabilidades-y-ataques/temas/04-tipos-de-ataques.html"],
          ["3.5 · Documentar una vulnerabilidad", "01-hacking-etico/03-vulnerabilidades-y-ataques/temas/05-documentar-una-vulnerabilidad.html"],
        ]],
        ["Ejercicios", "01-hacking-etico/03-vulnerabilidades-y-ataques/index.html#ejercicios", [
          ["Ejemplo resuelto · PHP2Shell", "01-hacking-etico/03-vulnerabilidades-y-ataques/ejercicios/php2shell.html"],
          ["U3·E1 · Ficha de Hackea el ranking", "01-hacking-etico/03-vulnerabilidades-y-ataques/ejercicios/e1.html"],
          ["U3·E2 · Ficha de un CVE real", "01-hacking-etico/03-vulnerabilidades-y-ataques/ejercicios/e2.html"],
          ["U3·E3 · El registro de un incidente", "01-hacking-etico/03-vulnerabilidades-y-ataques/ejercicios/e3.html"],
        ]],
      ]],
      ["04 · Herramientas y monitorización", "01-hacking-etico/04-herramientas-y-monitorizacion/index.html", [
        ["Temas", "01-hacking-etico/04-herramientas-y-monitorizacion/index.html#temas", [
          ["4.1 · Clasificación de herramientas", "01-hacking-etico/04-herramientas-y-monitorizacion/temas/01-clasificacion-de-herramientas.html"],
          ["4.2 · Monitorización según la organización", "01-hacking-etico/04-herramientas-y-monitorizacion/temas/02-monitorizacion-segun-organizacion.html"],
          ["4.3 · ClearNet, Deep Web y Dark Web", "01-hacking-etico/04-herramientas-y-monitorizacion/temas/03-clearnet-deep-dark-web.html"],
        ]],
        ["Ejercicios", "01-hacking-etico/04-herramientas-y-monitorizacion/index.html#ejercicios", [
          ["U4·E1 · Elige su monitorización", "01-hacking-etico/04-herramientas-y-monitorizacion/ejercicios/e1.html"],
          ["U4·E2 · Un sensor vigilando la web", "01-hacking-etico/04-herramientas-y-monitorizacion/ejercicios/e2.html"],
          ["U4·E3 · Cuatro darknets", "01-hacking-etico/04-herramientas-y-monitorizacion/ejercicios/e3.html"],
        ]],
      ]],
      ["Entrega del RA1", "01-hacking-etico/index.html#entrega"],
    ]],
    ["RA2 · Redes inalámbricas", "02-redes-inalambricas/index.html", [
      ["Guía del laboratorio", "02-redes-inalambricas/temas/guia-laboratorio.html"],
      ["Temas", "02-redes-inalambricas/index.html#temas", [
        ["Tema 1 · Cómo funciona y cómo se protege una Wi-Fi", "02-redes-inalambricas/temas/01-wifi-funciona-y-se-protege.html"],
        ["Tema 2 · Qué ve y hace un atacante", "02-redes-inalambricas/temas/02-atacante-y-deteccion.html"],
        ["Tema 3 · Otros inalámbricos e informe", "02-redes-inalambricas/temas/03-otros-inalambricos-e-informe.html"],
      ]],
      ["Prácticas", "02-redes-inalambricas/ejercicios/index.html", [
        ["P1 · Modos de la tarjeta y reconocimiento", "02-redes-inalambricas/ejercicios/p1.html"],
        ["P2 · Acceso a red vulnerable", "02-redes-inalambricas/ejercicios/p2.html"],
        ["P3 · Equipo azul con nzyme", "02-redes-inalambricas/ejercicios/p3.html"],
        ["P4 · Informe de auditoría", "02-redes-inalambricas/ejercicios/p4.html"],
      ]],
    ]],
    ["RA3 · Redes y sistemas", "03-redes-y-sistemas/index.html"],
    ["RA4 · Sistemas comprometidos", "04-sistemas-comprometidos/index.html"],
    ["RA5 · Aplicaciones web", "05-aplicaciones-web/index.html"],
    ["Estado de las entregas", "entregas/index.html"],
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
        details.dataset.ruta = ruta;
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
  // En el cajón, un enlace lo cierra (importa con las anclas de la misma página, que no recargan).
  nav.addEventListener("click", (e) => e.target.closest("a") && abrir(false));

  // Lo que se recuerda: ramas abiertas y scroll del índice durante la pestaña (sessionStorage),
  // y si la barra está plegada, también entre visitas (localStorage). Sin almacenamiento, el
  // índice funciona igual pero sin recordar nada.
  const leer = (almacen, clave) => { try { return window[almacen].getItem(clave); } catch { return null; } };
  const escribir = (almacen, clave, valor) => { try { window[almacen].setItem(clave, valor); } catch {} };

  // Plegar la barra fija (solo se ve con pantalla ancha; en estrecha el índice ya es un cajón).
  const plegar = document.createElement("button");
  plegar.id = "arbol-plegar";
  plegar.type = "button";
  plegar.setAttribute("aria-controls", nav.id);
  const plegado = (si) => {
    document.documentElement.classList.toggle("arbol-plegado", si);
    plegar.textContent = si ? "»" : "«";
    plegar.title = si ? "Desplegar el índice" : "Plegar el índice";
    plegar.setAttribute("aria-label", plegar.title);
    plegar.setAttribute("aria-expanded", String(!si));
  };
  plegado(leer("localStorage", "arbol-plegado") === "1");
  plegar.addEventListener("click", () => {
    const si = !document.documentElement.classList.contains("arbol-plegado");
    plegado(si);
    escribir("localStorage", "arbol-plegado", si ? "1" : "0");
  });

  document.body.append(nav, plegar, boton);

  let abiertas = [];
  try { abiertas = JSON.parse(leer("sessionStorage", "arbol-abiertas")) ?? []; } catch {}
  for (const d of nav.querySelectorAll("details")) if (abiertas.includes(d.dataset.ruta)) d.open = true;
  nav.scrollTop = Number(leer("sessionStorage", "arbol-scroll")) || 0;
  nav.addEventListener("toggle", () => escribir("sessionStorage", "arbol-abiertas",
    JSON.stringify([...nav.querySelectorAll("details[open]")].map((d) => d.dataset.ruta))), true);
  addEventListener("pagehide", () => escribir("sessionStorage", "arbol-scroll", String(nav.scrollTop)));
  // Las transiciones se activan después de colocar todo, para que nada se anime al cargar.
  requestAnimationFrame(() => requestAnimationFrame(() => document.documentElement.classList.add("arbol-listo")));

  // Marca el enlace de la página actual: el de su ancla si lo hay, si no el de la página sin
  // ancla. Abre sus ramas y, solo si el scroll recuperado lo deja fuera de la vista, lo centra.
  // Se repite al navegar entre anclas.
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
