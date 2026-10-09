# Noche americana
**Dirección final · Serendipity x Zamna Tulum 2027 · para aprobación**

## La idea en 3 líneas
1. El deck es una película de 18 planos sobre una noche en Tulum, en formato anamórfico. La "noche americana" es la técnica de cine que filma de día y gradúa la imagen como noche: es justo lo que hacemos con las fotos reales de la flota.
2. Sus colores enmarcan cada plano. Las láminas de noche llevan bandas Dark Teal #00272B y las de día bandas Teal #046567. El dorado es la luz.
3. Serendipity aparece en los créditos. Cada promesa se presenta como un crédito de cine (rol + nombre) y el lineup es una secuencia de créditos proyectada desde Grupo Mandala.

## Recursos firma (3, con disciplina)
| Recurso | Regla |
|---|---|
| **Letterbox de marca** | Bandas de 136 px arriba y abajo (cuadro de y 136 a 944). La banda superior lleva la etiqueta de sección y la inferior el pie, una **tira de película de 18 fotogramas** como indicador de avance (vistos llenos y el actual con anillo, sin texto) y el número. En la portada las bandas se cierran al entrar. **Se abre dos veces**: en la 07 (dorado a sangre, clímax) y en la 18 (cierre). |
| **Destello anamórfico** | Una línea de luz dorada con fantasma Teal cuyo núcleo cae sobre el eje de la lámina: el faro de la Suburban (01), el lente de Mandala que proyecta el haz Teal (05), el tronco que se abre en tres niveles (07), el núcleo del que salen las 4 funciones (12), la ruta de rastreo que avanza (13), la línea de tiempo (17) y el horizonte (18). En claro se vuelve un filete Teal con chispa dorada. **8 láminas no lo llevan** (03, 06, 08, 09, 11, 14, 15, 16), para que nunca sea fórmula. |
| **Créditos** | Rol en DM Sans 600, 24 px, versalitas con tracking .16em (dorado en noche, Teal en día) y "nombre" en Cormorant o DM Sans. Hay cuatro formatos: eje central (lineup 05), tabla sobre eje (02, 04), fila de créditos (03, 10, 12, 13, 17) y tarjeta de título (07). El subtítulo centrado en Cormorant itálica 44 solo aparece en 10, 11 y 17. En 02 y 13 el cierre va dentro de un campo Teal. |

Atmósfera sin texto: grano de película, sombras de palma (gobo) en día, siluetas de palma de coco y palma chit en noche, halos Teal, iris de anillos alrededor del marco de Mandala y la carta de la Riviera Maya sin rótulos (06).

## Paleta
| Token | Hex | Uso |
|---|---|---|
| Dark Teal (marca) | #00272B | Bandas de noche, fondo, texto sobre Arena y sobre dorado |
| Teal (marca) | #046567 | Bandas de día, campos de color (02, 06, 13), haz de luz (05), acentos de texto en claro |
| Arena | #F3EEE4 | Cuadro de día, texto sobre oscuro y sobre Teal |
| Dorado | #C9A55C | Luz, roles y cifras en noche, fondo de la 07 |
| Bruma / Pizarra | #C8CFC4 / #4A544E | Texto secundario sobre oscuro / sobre Arena |
| Derivado · cuadro noche | #002024 | Fondo de la imagen en noche (Dark Teal con 18 % menos luz) |
| Derivado · sombra | #00181B | Solo viñeta y siluetas, nunca como campo |
| Derivado · Teal profundo | #035A5C | Parte baja de los campos Teal |
| Derivado · oro claro / oro borde | #DDBF7B / #B38E48 | Degradado metálico de la 07 |

Contrastes WCAG: Arena sobre Dark Teal 13.7 · Arena sobre cuadro noche 14.7 · Dorado sobre Dark Teal 6.8 (7.3 sobre cuadro) · Bruma sobre cuadro 10.7 · Arena sobre Teal 5.9 (6.9 sobre Teal profundo) · Teal sobre Arena 5.9 · Dark Teal sobre Dorado 6.8 (8.9 en el centro claro, 5.2 en el borde) · Pizarra sobre Arena 6.8.
**Prohibido para texto:** Dorado sobre Teal (2.95), Bruma sobre Teal (4.3), Teal sobre Dark Teal (2.3).
Linter con píxeles reales: **0 errores, 0 avisos**. El contraste mínimo por lámina va de 4.97 (07) a 6.81.

## Tipografía y retícula
- **Cormorant Garamond 500/600** para títulos y **DM Sans 400 a 600** para texto. Son archivos de Google Fonts alojados también en `assets/fonts`, así que el deck se proyecta sin internet y el PDF sale idéntico.
- Escala única: **120 / 72 / 44 / 32 / 24**. Las cifras grandes (45,000+ · 2020 · 4 · 5) van a 120 con numerales lining, los headliners a 72 y los cierres en itálica 44. `text-wrap: balance` en títulos, cortes semánticos y la cursiva solo en el giro de cada frase.
- Canvas de 1920 x 1080, márgenes laterales de 128 px y 12 columnas de 102 + 40. Los títulos siempre arrancan en x 128 / y 216 y el ritmo vertical va en múltiplos de 8.
- **A declarar:** la etiqueta (y 52) y el pie (y 996) viven dentro del margen vertical de 128 px porque son contenido de banda, no del cuadro.

## Tratamiento de imagen
Las derivadas salen de `tools/grade.py` (PIL), nunca se amplían por encima de su tamaño nativo y pesan de 61 a 221 KB:
- **Noche** (01, 10, 11 Sprinter, 12, 14): sombras Dark Teal, luz Teal, prácticas en oro y arena. En la 01 (Suburban High Country del cliente) se hace una noche americana real: un solo grading sobre toda la foto, sin recortar la camioneta, para conservar sus reflejos, su sombra en el piso y los árboles detrás. La escena cae a la oscuridad hacia la izquierda, la placa está neutralizada y el destello nace en el faro. En la 10 las ventanas pasan a noche con máscara suave, hay bokeh desenfocado, luz clave en cada rostro, retoque local en la piel de la invitada de la derecha y la foto se cierra en Dark Teal sólido antes de los créditos.
- **Día dorado** (08, 09, 11, 15): sombras Dark Teal, medios cálidos, altas luces arena. El cielo azul se vuelve bruma arena.
- La 16 usa a los invitados reales de noche totalmente desenfocados como fondo del testimonio. Los placeholders de la 03, 06, 12 y 18 son atmósfera generada (arboleda, carta, copas, proscenio de palmas). Cada lámina tiene un comentario HTML donde iría la foto de stock.
- No usamos `economy-avanza.jpg` ni `logo.png` (Ride Luxe).

## Movimiento
Fade + 12 px de subida en 520 ms, escalonado cada 80 ms. Las líneas (ruta, ramas, línea de tiempo) se dibujan en 0.9 s y el punto de rastreo de la 13 late. Las bandas se cierran en la 01 y se abren en la 18. Se respeta `prefers-reduced-motion`. El visor tiene canvas fijo escalado, flechas, espacio, clic (mitad izquierda retrocede), F para pantalla completa, `#n` en la URL y contador discreto. El modo `?render` muestra el estado final.

## Co-branding con Zamna
- Los logos de Serendipity y Zamna ya están integrados en la portada, la 15 (Zamna) y el cierre. El sello Travelers' Choice 2025 está en la 04. Falta solo el logo de Grupo Mandala (05).
- **Lockup**: sin marco ni esquinas: logo de Serendipity, la x dorada y el logo de ZAMNA, separados por 40 px. La **x es la misma Cormorant itálica dorada del título**: hay una sola grafía de co-branding. En todo el deck no hay esquinas decorativas; los marcos que quedan (Mandala, placa de Zamna, reseñas) llevan solo un filete fino.
- Aparece en la portada (arriba a la izquierda, en el cuadro) y en el cierre (centrado). Los logos entran en monocromo arena con 24 px de aire. Si el wordmark de Zamna es muy fino, se ajusta el ancho de celda por peso óptico.
- Zamna también aparece "a bordo" en la 15 (placa sobre la cabina). Mandala va en un marco de 528 x 220 como fuente del haz de la 05. El sello Travelers' Choice va en un marco horizontal de 386 x 208. No se dibuja ni se imita ningún logo.

## Las 18 láminas
| # | Lámina | Layout | Imagen | Recurso |
|---|---|---|---|---|
| 01 | Portada | Lockup, título 120 y subtítulo a la izquierda; la camioneta a la derecha | Suburban High Country del cliente en noche americana | Bandas que cierran, destello desde el faro |
| 02 | La oportunidad | Título 72 en 3 líneas, tabla de créditos sobre eje y campo Teal a la derecha con el cierre | Gobo de palma en el campo | Destello claro, campo Teal |
| 03 | Quiénes somos | Título 120, párrafo y fila de 3 cifras a 120 | Arboleda nocturna generada | Créditos (cifras) |
| 04 | Credenciales | Tabla de 4 créditos sobre eje y marco del sello | Gobo de palma | Destello claro |
| 05 | Escena musical | Mandala como lente, haz Teal sobre el lineup en cartel 72 / 44 / 24 | Haz, iris y chit | Destello como proyector |
| 06 | Cero curva | Campo Teal con título y carta; 4 créditos en lista | Carta de la Riviera Maya, ruta dorada | Campo Teal |
| 07 | Nuestra propuesta | Letterbox abierto, título 120 centrado y diagrama 1 → 1 → 3 | Oro metálico | El destello entra, núcleo, tres ramas a 72 |
| 08 | Segmento 01 | Título y lista a la izquierda, foto a sangre a la derecha | Chofer de Serendipity en la zona de ascenso de CUN, día dorado | Créditos en lista |
| 09 | Segmento 02 | Mismo layout (contraplano) | Invitada a bordo de la Suburban, puerta abierta (foto del cliente) | Créditos en lista |
| 10 | Mesas VIP | "Mesas VIP:" 120, foto cerrada en Dark Teal, fila de 3 créditos y subtítulo | Trío en V-Class, noche | Destello a través de la cabina |
| 11 | Flota | Cuatro fotogramas con nombre 44, capacidad y uso, subtítulo: SUV ejecutiva 6, Van de lujo 5, Sprinter 13 a 18, Van estándar 11 (servicios internos) | Suburban, V-Class, la Sprinter real de noche y la van estándar con chofer de Serendipity | Fotogramas |
| 12 | Operación en sitio | Título centrado, núcleo dorado que irradia a 4 columnas 01 a 04 | Sprinter real en un acceso de noche, desenfocada como bokeh, con copas de palma | Destello como centro de operación |
| 13 | Tecnología | Ruta de rastreo (recorrido sólido, pendiente punteado, punto vivo) y 4 funciones; frase en barra Teal | Gobo en la barra | Destello que avanza, campo Teal |
| 14 | Seguridad | Título 72 en 3 líneas y 4 créditos 2 x 2; foto a la derecha | Chofer de Serendipity al volante (uniforme con logo), noche | Créditos |
| 15 | Experiencia de marca | Foto a la izquierda con placa del logo de Zamna; título y 3 créditos | Cabina Suburban, día dorado | Placa de marca a bordo |
| 16 | Referencias | Composición simétrica: testimonio de Grupo Mandala en 72 itálica y firma; abajo dos tarjetas: Sam Gordon (Kan Hotel) y Maceo P (Tripadvisor) | Invitados desenfocados (bokeh) | Créditos finales |
| 17 | Cómo trabajamos | Línea de tiempo a todo el ancho con 5 nodos, pasos y subtítulo | Gobo | Destello como línea de tiempo |
| 18 | Siguiente paso | Letterbox abierto y composición simétrica: título, contacto como créditos, lockup | Proscenio de palmas generado | Bandas que se abren, horizonte de luz |

Alternancia: noche 01 03 05 10 12 14 16 18 · día 02 04 06 08 09 11 13 15 17 · oro 07.

## Lo que necesitamos del cliente
1. **Logos:** ~~Serendipity, Zamna y sello Travelers' Choice 2025~~ (recibidos). Falta el logo de Grupo Mandala (05).
2. ~~Capacidades de la flota~~ (recibidas: SUV 6, Van de lujo 5, Sprinter 13 a 18, Van estándar 11).
3. **Validar el billing del lineup** de la 05 con Grupo Mandala: 6 nombres en el primer nivel (72) y 10 en el segundo (44), en el orden del brief. Si no se valida, pasamos todo a un solo nivel.
4. **Testimonio y referencias** (16): Grupo Mandala (confirmar aprobación de la redacción; faltan nombre y cargo de quien firma), Sam Gordon de Kan Hotel (extracto traducido al español) y la reseña de Maceo P en Tripadvisor (enero 2026).
5. **Número de WhatsApp** (18).
6. **Fotos de stock** (si se habilitan Unsplash o Pexels): carretera en la selva de noche con faros (01 y 18), vista aérea de la selva de Tulum (03), escenario entre árboles sin artistas reconocibles (05), jet privado en FBO (06 y 08), zona de ascenso de un venue de noche (12), cenote o playa a la hora azul (16). Todas pasarán por el mismo grading. Idealmente también una toma nocturna real de la Suburban.
7. Opcional: una captura real de la app Ride Luxe con rastreo en vivo para la 13.

## Notas técnicas
`index.html` es la única fuente editable: no hay build, las rutas SVG van en línea y las imágenes son relativas a `assets/`. La exportación de prueba a PDF con Playwright salió de 13.8 MB en 18 páginas y el grano, los degradados y el haz coinciden con la pantalla (el grano es PNG con alfa, sin blend mode). Las imágenes se regeneran con `python3 tools/grade.py`.

## Cambios de contenido pedidos por el cliente
- 06: camionetas en disposición de 12 y 24 horas (antes 18).
- 09: servicio por hora solo para afters (sin cenas ni beach clubs).
- 11: capacidades reales y Van estándar para servicios internos.
- 12 y 17: sin coordinador en el venue; en su lugar, equipo de operaciones en turno.
