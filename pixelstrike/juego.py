"""Ventana, bucle principal y cambio de escenas."""
import pygame

from . import ajustes as aj
from .escena_nivel import EscenaNivel
from .escenas_menu import Creditos, SelectorDificultad, SelectorNiveles, SelectorPersonajes
from .progreso import Progreso
from .recursos import recursos


class Juego:
    def __init__(self):
        pygame.init()
        recursos.iniciar_audio()
        pygame.display.set_caption(aj.TITULO)

        # Se dibuja siempre en un lienzo de 1600x900 y se escala a la ventana
        self.lienzo = pygame.Surface((aj.ANCHO, aj.ALTO))
        info = pygame.display.Info()
        escala = min(1.0, info.current_w * 0.95 / aj.ANCHO, info.current_h * 0.90 / aj.ALTO)
        pygame.display.set_mode((int(aj.ANCHO * escala), int(aj.ALTO * escala)), pygame.RESIZABLE)
        self.reloj = pygame.time.Clock()
        self.progreso = Progreso()
        self.escena = None
        self._escena_pendiente = None
        self.corriendo = True
        self.ir_a_selector_dificultad()
        self._aplicar_cambio_de_escena()

    # --- navegación entre escenas (el cambio real se aplica al final del cuadro) ---
    def ir_a_selector_dificultad(self):
        self._escena_pendiente = SelectorDificultad(self)

    def ir_a_selector_niveles(self):
        self._escena_pendiente = SelectorNiveles(self)

    def ir_a_selector_personajes(self):
        self._escena_pendiente = SelectorPersonajes(self)

    def ir_a_nivel(self, clave):
        self._escena_pendiente = EscenaNivel(self, clave)

    def ir_a_creditos(self):
        self._escena_pendiente = Creditos(self)

    def _aplicar_cambio_de_escena(self):
        if self._escena_pendiente is not None:
            self.escena = self._escena_pendiente
            self._escena_pendiente = None
            self.escena.al_entrar()

    # --- bucle ---------------------------------------------------------------
    def procesar_eventos(self):
        for evento in pygame.event.get():
            if evento.type == pygame.QUIT:
                self.corriendo = False
            elif evento.type == pygame.KEYDOWN and evento.key == pygame.K_F11:
                pygame.display.toggle_fullscreen()
            else:
                self.escena.manejar_evento(evento)

    def actualizar(self, dt):
        self.escena.actualizar(dt)
        self._aplicar_cambio_de_escena()

    def dibujar(self):
        self.escena.dibujar(self.lienzo)
        ventana = pygame.display.get_surface()     # puede cambiar al redimensionar
        ancho, alto = ventana.get_size()
        escala = min(ancho / aj.ANCHO, alto / aj.ALTO)
        tam = (int(aj.ANCHO * escala), int(aj.ALTO * escala))
        ventana.fill((0, 0, 0))
        if tam == (aj.ANCHO, aj.ALTO):
            ventana.blit(self.lienzo, (0, 0))
        else:
            ventana.blit(pygame.transform.scale(self.lienzo, tam),
                         ((ancho - tam[0]) // 2, (alto - tam[1]) // 2))
        pygame.display.flip()

    def ejecutar(self):
        while self.corriendo:
            dt = min(self.reloj.tick(aj.FPS) / 1000.0, 0.05)   # tope para no "saltar" tras un lag
            self.procesar_eventos()
            self.actualizar(dt)
            self.dibujar()
        pygame.quit()
