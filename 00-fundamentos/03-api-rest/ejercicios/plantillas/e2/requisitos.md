# Lo que pide el equipo de sistemas

Queremos dejar la hoja de cálculo y registrar las incidencias de los puestos de trabajo en una API,
para que la web interna, la app del móvil y los scripts de los técnicos usen todos lo mismo.

Una incidencia tiene un título (máximo 120 caracteres), una prioridad (baja, media, alta o crítica),
un estado (abierta, en curso o cerrada) y el técnico que la lleva, que puede no haber todavía.
Cada incidencia puede tener comentarios: solo texto, hasta 500 caracteres.

Necesitamos poder:

1. Ver todas las incidencias.
2. Ver una incidencia concreta.
3. Abrir una incidencia nueva. Si no se dice otra cosa, nace abierta y sin técnico.
4. Cambiar la prioridad o el técnico de una incidencia sin tener que mandar el resto de datos.
5. Corregir una incidencia entera de una vez.
6. Cerrar una incidencia.
7. Borrar las incidencias duplicadas.
8. Ver los comentarios de una incidencia y añadir uno nuevo.
9. Saber si la API está en marcha, para el sistema de monitorización.

Queremos poder cambiar la API en el futuro sin romper a los clientes que ya la usan.
