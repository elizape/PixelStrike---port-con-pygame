"""Constantes del juego. Todo lo que se quiera "tunear" vive acá."""
from pathlib import Path

import pygame

TITULO = "Pixel Strike"

# --- Pantalla (grilla de 32x18 celdas de 50px, igual que en Wollok) ---------
CELDA = 50
ANCHO_GRILLA = 32
ALTO_GRILLA = 18
ANCHO = ANCHO_GRILLA * CELDA
ALTO = ALTO_GRILLA * CELDA
FPS = 60

DIR_ASSETS = Path(__file__).resolve().parent.parent / "assets"

# --- Audio -------------------------------------------------------------------
VOLUMEN_MUSICA = 0.4
VOLUMEN_MUSICA_CREDITOS = 0.6

# --- Mundo -------------------------------------------------------------------
FILA_MAX = 3                  # el campo de batalla tiene las filas 0..3
COLUMNA_MAX = 30              # columna máxima a la que puede llegar el jugador
JUGADOR_INICIO = (2, 2)
SELECTOR_INICIO = (15, 1)     # posición inicial en el selector de niveles
ENEMIGO_X_INICIAL = 30
ENEMIGO_X_LIMITE = -3         # si un enemigo llega acá, escapó y daña al jugador
DANIO_ENEMIGO_ESCAPADO = 15
VIDA_POR_CORAZON = 10
VIDA_CRITICA = 20             # por debajo suena el latido y parpadea el jugador

# Velocidades en celdas por segundo
VELOCIDAD_BALA = 42.0
VELOCIDAD_GOTA = 30.0

DURACION_ITEM_POWERUP = 5.5   # segundos que un power up queda en el piso
PARPADEO_ICONO = 0.3          # parpadeo del ícono cuando se acaba un power up
PARPADEO_ICONO_REPS = 7

# --- Entrada -----------------------------------------------------------------
# Mejora respecto al original: mantener apretada una tecla repite la acción.
MANTENER_PARA_MOVER = False
MANTENER_PARA_DISPARAR = False
REPETICION_RETARDO = 0.22     # segundos hasta empezar a repetir
REPETICION_INTERVALO = 0.09   # segundos entre repeticiones

TECLA_ARRIBA = pygame.K_w
TECLA_IZQUIERDA = pygame.K_a
TECLA_ABAJO = pygame.K_s
TECLA_DERECHA = pygame.K_d
TECLA_DISPARO = pygame.K_p
TECLA_PAUSA = pygame.K_m
TECLA_REINICIAR = pygame.K_r
TECLA_SELECTOR = pygame.K_t
TECLAS_ENTER = (pygame.K_RETURN, pygame.K_KP_ENTER)
