"""Carga y cache de imágenes y sonidos. Si falta un asset no se rompe: usa un placeholder."""
import random
import sys

import pygame

from . import ajustes as aj


class _SonidoNulo:
    def play(self, *args, **kwargs):
        return None

    def set_volume(self, *args, **kwargs):
        return None


class Recursos:
    def __init__(self):
        self._imagenes = {}
        self._sonidos = {}
        self._fuentes = {}
        self._musica_actual = None
        self.faltantes = set()
        self.audio_ok = False

    # --- audio ----------------------------------------------------------
    def iniciar_audio(self):
        try:
            pygame.mixer.init()
            pygame.mixer.set_num_channels(32)
            self.audio_ok = True
        except pygame.error as error:
            print(f"[audio] Sin audio disponible: {error}", file=sys.stderr)

    def sonido(self, nombre):
        sonido = self._sonidos.get(nombre)
        if sonido is None:
            sonido = _SonidoNulo()
            if self.audio_ok:
                try:
                    sonido = pygame.mixer.Sound(str(aj.DIR_ASSETS / nombre))
                except (FileNotFoundError, pygame.error):
                    self._avisar_faltante(nombre)
            self._sonidos[nombre] = sonido
        return sonido

    def reproducir(self, nombre, volumen=1.0):
        sonido = self.sonido(nombre)
        sonido.set_volume(volumen)
        sonido.play()

    def reproducir_al_azar(self, nombres, volumen=1.0):
        self.reproducir(random.choice(nombres), volumen)

    def musica(self, nombre, volumen=aj.VOLUMEN_MUSICA, repetir=True, continuar=False):
        """Con `continuar=True`, si ya está sonando esa misma canción no la reinicia."""
        if not self.audio_ok:
            return
        if continuar and nombre == self._musica_actual and pygame.mixer.music.get_busy():
            return
        try:
            pygame.mixer.music.load(str(aj.DIR_ASSETS / nombre))
            pygame.mixer.music.set_volume(volumen)
            pygame.mixer.music.play(-1 if repetir else 0)
            self._musica_actual = nombre
        except (FileNotFoundError, pygame.error):
            self._avisar_faltante(nombre)

    def detener_musica(self):
        self._musica_actual = None
        if self.audio_ok:
            pygame.mixer.music.stop()

    # --- imágenes -------------------------------------------------------
    def imagen(self, nombre, tam_respaldo=None):
        imagen = self._imagenes.get(nombre)
        if imagen is None:
            try:
                imagen = pygame.image.load(str(aj.DIR_ASSETS / nombre)).convert_alpha()
            except (FileNotFoundError, pygame.error):
                self._avisar_faltante(nombre)
                imagen = self._placeholder(tam_respaldo or (aj.CELDA, aj.CELDA))
            self._imagenes[nombre] = imagen
        return imagen

    def dibujar(self, lienzo, nombre, x, y):
        """Dibuja una imagen con su esquina inferior izquierda en la celda (x, y).

        Es la misma convención que Wollok: el origen está abajo a la izquierda y
        la imagen crece hacia arriba y hacia la derecha. x e y pueden ser float.
        """
        imagen = self.imagen(nombre)
        lienzo.blit(imagen, (round(x * aj.CELDA),
                             round(aj.ALTO - y * aj.CELDA - imagen.get_height())))

    def dibujar_fondo(self, lienzo, nombre):
        lienzo.blit(self.imagen(nombre, (aj.ANCHO, aj.ALTO)), (0, 0))

    # --- texto ----------------------------------------------------------
    def fuente(self, tam):
        """Usa assets/fuente.ttf si existe (ideal una fuente píxel); si no, la fuente por defecto."""
        fuente = self._fuentes.get(tam)
        if fuente is None:
            ruta = aj.DIR_ASSETS / "fuente.ttf"
            if not pygame.font.get_init():
                pygame.font.init()
            fuente = pygame.font.Font(str(ruta) if ruta.is_file() else None, tam)
            self._fuentes[tam] = fuente
        return fuente

    def texto(self, lienzo, texto, tam, color, centro_x, y, sombra=(0, 0, 0)):
        """Dibuja `texto` centrado en `centro_x` (en píxeles del lienzo), con `y` como borde superior."""
        fuente = self.fuente(tam)
        imagen = fuente.render(texto, True, color)
        x = centro_x - imagen.get_width() // 2
        if sombra:
            lienzo.blit(fuente.render(texto, True, sombra), (x + max(2, tam // 14), y + max(2, tam // 14)))
        lienzo.blit(imagen, (x, y))
        return imagen.get_rect(topleft=(x, y))

    # --- internos -------------------------------------------------------
    def _avisar_faltante(self, nombre):
        if nombre not in self.faltantes:
            self.faltantes.add(nombre)
            print(f"[assets] No se pudo cargar '{nombre}' (se usa un placeholder)", file=sys.stderr)

    @staticmethod
    def _placeholder(tam):
        superficie = pygame.Surface(tam, pygame.SRCALPHA)
        superficie.fill((255, 0, 255, 90))
        pygame.draw.rect(superficie, (255, 0, 255), superficie.get_rect(), 2)
        return superficie


recursos = Recursos()
