"""Clase base de las pantallas del juego."""
import random
from functools import partial

from . import datos as d
from .recursos import recursos
from .temporizador import Planificador


class Escena:
    def __init__(self, juego):
        self.juego = juego
        self.ui = Planificador()       # corre siempre, incluso con el juego en pausa
        self.indicadores = []          # imágenes visibles, en orden de dibujo

    # --- ciclo de vida --------------------------------------------------
    def al_entrar(self):
        pass

    def manejar_evento(self, evento):
        pass

    def actualizar(self, dt):
        self.ui.actualizar(dt)

    def dibujar(self, lienzo):
        pass

    # --- indicadores ----------------------------------------------------
    def mostrar(self, indicador):
        if indicador not in self.indicadores:
            self.indicadores.append(indicador)

    def ocultar(self, indicador):
        if indicador in self.indicadores:
            self.indicadores.remove(indicador)

    def mostrar_por(self, indicador, segundos, planificador=None):
        self.mostrar(indicador)
        (planificador or self.ui).despues(segundos, partial(self.ocultar, indicador))

    def secuencia(self, indicadores, planificador=None, con_sonido=True):
        """Muestra las imágenes una detrás de otra, cada una durante su `duracion`."""
        planificador = planificador or self.ui
        t = 0.0
        for indicador in indicadores:
            planificador.despues(t, partial(self._abrir_paso, indicador, con_sonido))
            t += indicador.duracion
            planificador.despues(t, partial(self.ocultar, indicador))
            t += 0.05
        return t

    def _abrir_paso(self, indicador, con_sonido):
        self.mostrar(indicador)
        if con_sonido:
            recursos.reproducir(random.choice(d.SFX_WHOOSH))

    def dibujar_indicadores(self, lienzo):
        for indicador in self.indicadores:
            recursos.dibujar(lienzo, indicador.imagen, indicador.x, indicador.y)
