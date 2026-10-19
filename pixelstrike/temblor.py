"""Screen shake: sacude el juego (no la interfaz) con una fuerza que depende del daño recibido."""
import random

PIXELES_POR_DANIO = 0.5       # intensidad inicial = daño * esto ...
INTENSIDAD_MIN = 3            # ... entre estos dos valores (en píxeles del lienzo)
INTENSIDAD_MAX = 16
DURACION_BASE = 0.15          # segundos; se suma DURACION_POR_DANIO * daño
DURACION_POR_DANIO = 0.01
DURACION_MAX = 0.45


class Temblor:
    def __init__(self):
        self.restante = 0.0
        self.duracion = 0.0
        self.intensidad = 0.0
        self.desplazamiento = (0, 0)          # (dx, dy) que se aplica al dibujar el juego

    @property
    def activo(self):
        return self.restante > 0

    def sacudir(self, danio):
        """Un golpe más fuerte sacude más y por más tiempo. Si ya había temblor, gana el más fuerte."""
        intensidad = min(INTENSIDAD_MAX, max(INTENSIDAD_MIN, danio * PIXELES_POR_DANIO))
        duracion = min(DURACION_MAX, DURACION_BASE + DURACION_POR_DANIO * danio)
        if intensidad * duracion >= self._fuerza_actual():
            self.intensidad, self.duracion, self.restante = intensidad, duracion, duracion

    def actualizar(self, dt):
        if not self.activo:
            self.desplazamiento = (0, 0)
            return
        self.restante = max(0.0, self.restante - dt)
        amplitud = self.intensidad * (self.restante / self.duracion)      # se apaga de a poco
        self.desplazamiento = (round(random.uniform(-amplitud, amplitud)),
                               round(random.uniform(-amplitud, amplitud)))

    def _fuerza_actual(self):
        return self.intensidad * self.restante if self.activo else 0.0
