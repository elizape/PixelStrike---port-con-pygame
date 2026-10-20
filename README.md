# Pixel Strike (pygame)

Port de Pixel Strike de Wollok Game a Python + pygame.

## Cómo correrlo

```bash
python3 -m venv .venv
source .venv/bin/activate        # en Windows: .venv\Scripts\activate
pip install -r requirements.txt
python main.py
```

El entorno virtual (`.venv/`) no se sube al repo: está en el `.gitignore`.

Los assets (`.png` y `.mp3`) tienen que estar en `./assets`, junto a `main.py`,
con los mismos nombres que usaba el proyecto Wollok. Si falta alguno el juego no
se rompe: dibuja un recuadro magenta y avisa por consola cuál faltó.

## Controles

| Tecla | Acción |
|---|---|
| W A S D | Moverse: un paso por pulsación, sin límite de rapidez (mantener apretado no repite, como en el original) |
| P | Disparar (en el selector de niveles abre el selector de personajes) |
| M | Pausa (no se puede con un power up activo) |
| R / T | Reiniciar nivel / volver al selector (en pausa o al morir) |
| Enter | Confirmar dificultad / avanzar el tutorial / elegir personaje / saltar créditos |
| Esc | En el selector de niveles: volver al selector de dificultad |
| F11 | Pantalla completa |

En el selector de dificultad se elige con W/S (o A/D) y Enter.

Las teclas y varias constantes de juego están en `pixelstrike/ajustes.py`. Si preferís que mantener apretado repita el movimiento o el disparo, activá `MANTENER_PARA_MOVER` / `MANTENER_PARA_DISPARAR` en ese mismo archivo (vienen desactivadas).

## Dificultad

Al abrir el juego se elige entre **Fácil**, **Normal** y **Difícil**. Normal es el juego original. Se puede cambiar en cualquier momento con Esc desde el selector de niveles, sin perder niveles ni personajes desbloqueados. El tutorial (nivel 0) siempre se juega en Normal.

| | Fácil | Normal | Difícil |
|---|---|---|---|
| Vida de los enemigos | ×0,5 | ×1 | ×1,5 |
| Velocidad de los enemigos | ×0,8 | ×1 | ×1,25 |
| Tiempo entre disparos enemigos | ×1,25 | ×1 | ×0,8 |
| Daño de balas y fuego enemigos | ×0,5 | ×1 | ×1,5 |
| Tiempo entre apariciones | ×1,25 | ×1 | ×0,75 |
| Daño si un enemigo se escapa | 10 | 15 | 20 |
| Vida de Kratos | 100 | 150 | 225 |
| Tiempo entre ataques de Kratos | 1,4 s | 1,1 s | 0,8 s |
| XP ganada (enemigos, racha, jefe, bono perfecto) | ×0,8 (-20%) | ×1 | ×1,2 (+20%) |
| XP perdida (disparo recibido) | ×1 (fijo) | ×1 | ×1,2 (+20%) |

Los valores están en `pixelstrike/datos.py` (`FACIL`, `NORMAL`, `DIFICIL`). El diseño completo está en [`docs/DISENO_DIFICULTAD.md`](docs/DISENO_DIFICULTAD.md).

### Título y triángulos del selector (opcionales)

El selector de dificultad usa dos imágenes si están en `assets/`; si faltan, muestra el texto y el recuadro dorado de siempre:

| Archivo | Qué es |
|---|---|
| `assets/tituloPixelStrike.png` | Título, centrado arriba. Si es más grande que 1400x230 px se reduce solo, conservando la proporción. |
| `assets/selectorTriangulos.png` | **Un solo PNG** con los dos triángulos enfrentados (izquierdo y derecho). Se parte por la mitad y a cada mitad se le recorta el borde transparente, así que quedan siempre a 30 px del texto de la opción elegida, sin importar el espacio vacío del PNG. |

Los nombres están en `pixelstrike/datos.py` (`TITULO_JUEGO`, `TRIANGULOS_SELECTOR`) y las medidas en `escenas_menu.py`.

La pantalla usa la fuente por defecto de pygame. Si querés una fuente píxel, copiala como `assets/fuente.ttf` y se usa sola.

## Tests

```bash
python -m unittest discover -s tests -v
```

Corren sin ventana ni audio.

## Estructura

```
main.py                    punto de entrada (reemplaza a mainprogram.wpgm)
pixelstrike/
  ajustes.py               constantes y teclas
  datos.py                 armas, personajes, enemigos, niveles, imágenes y sonidos
  recursos.py              carga de imágenes / sonidos / música (con placeholders)
  temporizador.py          Planificador: reemplaza game.schedule / game.onTick
  entrada.py               teclas con repetición
  entidades.py             Jugador, Enemigo, balas, ítems de power up
  jefe.py                  Kratos y sus ataques
  interfaz.py              barras de vida y de power ups
  escena.py                clase base de pantallas
  escena_nivel.py          tutorial, hordas y nivel del jefe
  escenas_menu.py          selector de dificultad, de niveles, de personajes, créditos
  particulas.py            partículas de muerte
  temblor.py               screen shake según el daño recibido
  progreso.py              niveles, personajes desbloqueados y dificultad elegida
  juego.py                 ventana, bucle principal, cambio de escenas
tests/                     tests sin ventana (unittest)
docs/                      documentos de diseño
```

## Equivalencias con el proyecto Wollok

| Wollok | Python |
|---|---|
| `armas.wlk`, `enemigos.wlk` (clases) | `entidades.py`, `jefe.py` |
| constantes de armas / niveles / imágenes | `datos.py` |
| `claseNivel.wlk`, `nivelFinal.wlk`, `TutorialManager` | `escena_nivel.py` |
| `selectorDeNiveles.wlk`, `selectorDePersonajes.wlk`, `creditos` | `escenas_menu.py` |
| `nivelManager`, `characterManager` | `Progreso` + estados de `EscenaNivel` |
| `game.onTick` / `game.schedule` | `Planificador` (con generadores para las secuencias) |
| `game.clear()` + `iniciar()` | crear una escena nueva |

## Cambios respecto al original

- **Partículas de muerte** con el color de cada personaje (Byte Hunter azul, Jade verde claro, Kratos rojo, Alien Raptor rosa, Crawler verde oscuro). Los colores están en `datos.py` (`color_muerte`).
- **Screen shake** cuando una bala enemiga te pega o un enemigo se escapa: sacude el juego (no la interfaz), con más fuerza y duración cuanto más daño, y se congela en pausa. Los valores están en `pixelstrike/temblor.py`.
- **Selector de dificultad** al iniciar (Fácil / Normal / Difícil), que no existía en el original.
- **Pausa real**: los temporizadores del juego (spawns, ataques del jefe, power ups) se congelan en pausa.
- **Música en loop** (en Wollok sonaba una sola vez).
- **Mantener apretado** puede repetir el movimiento y el disparo, pero es opcional y viene **desactivado** para conservar el comportamiento original (ver `ajustes.py`).
- **Jefe invulnerable durante su intro** (antes se le podía pegar antes de que arrancara la barra de vida).
- **Power ups**: re-agarrar uno renueva el tiempo en vez de apilar el efecto. El daño de una bala se fija al disparar.
- El jefe esquiva si **cualquier** bala del jugador viene por su fila (antes solo miraba la más antigua).
- El latido y el parpadeo de poca vida se disparan al **cruzar** los 20 puntos (antes solo si quedaba exactamente en 20).
- Un enemigo con power up que se escapa de la pantalla ya no suelta el ítem fuera del mapa.
- La ventana se escala si la pantalla no alcanza para 1600x900.
