"""Manejo de teclas con repetición al mantener apretado."""
import pygame

from . import ajustes as aj


class TeclasRepetibles:
    def __init__(self, acciones, repetir=True):
        self.acciones = acciones          # {tecla: callable}
        self.repetir = repetir
        self._espera = {}

    def tecla_abajo(self, tecla):
        """Devuelve True si la tecla era una de las de este grupo."""
        accion = self.acciones.get(tecla)
        if accion is None:
            return False
        accion()
        if self.repetir:
            self._espera[tecla] = aj.REPETICION_RETARDO
        return True

    def actualizar(self, dt):
        if not self._espera:
            return
        apretadas = pygame.key.get_pressed()
        for tecla in list(self._espera):
            if not apretadas[tecla]:
                del self._espera[tecla]
                continue
            self._espera[tecla] -= dt
            while self._espera[tecla] <= 0:
                self.acciones[tecla]()
                self._espera[tecla] += aj.REPETICION_INTERVALO
