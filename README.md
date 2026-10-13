# Pixel Strike (pygame)

Port de Pixel Strike de Wollok Game a Python + pygame.

## Cómo correrlo

```bash
pip install -r requirements.txt
python main.py
```

Los assets (`.png` y `.mp3`) tienen que estar en `./assets`, junto a `main.py`,
con los mismos nombres que usaba el proyecto Wollok. Si falta alguno el juego no
se rompe: dibuja un recuadro magenta y avisa por consola cuál faltó.

## Controles

| Tecla | Acción |
|---|---|
| W A S D | Moverse (mantener apretado repite el movimiento) |
| P | Disparar (en el selector de niveles abre el selector de personajes) |
| M | Pausa (no se puede con un power up activo) |
| R / T | Reiniciar nivel / volver al selector (en pausa o al morir) |
| Enter | Avanzar el tutorial / elegir personaje / saltar créditos |
| F11 | Pantalla completa |

Las teclas y varias constantes de juego están en `pixelstrike/ajustes.py`.

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
  escenas_menu.py          selector de niveles, selector de personajes, créditos
  progreso.py              niveles y personajes desbloqueados
  juego.py                 ventana, bucle principal, cambio de escenas
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

- **Pausa real**: los temporizadores del juego (spawns, ataques del jefe, power ups) se congelan en pausa.
- **Música en loop** (en Wollok sonaba una sola vez).
- **Mantener apretado** mueve y dispara (desactivable en `ajustes.py`).
- **Jefe invulnerable durante su intro** (antes se le podía pegar antes de que arrancara la barra de vida).
- **Power ups**: re-agarrar uno renueva el tiempo en vez de apilar el efecto. El daño de una bala se fija al disparar.
- El jefe esquiva si **cualquier** bala del jugador viene por su fila (antes solo miraba la más antigua).
- El latido y el parpadeo de poca vida se disparan al **cruzar** los 20 puntos (antes solo si quedaba exactamente en 20).
- Un enemigo con power up que se escapa de la pantalla ya no suelta el ítem fuera del mapa.
- La ventana se escala si la pantalla no alcanza para 1600x900.
