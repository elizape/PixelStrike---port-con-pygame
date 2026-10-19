"""Partículas de muerte: cuadraditos que salen disparados, caen y se encogen hasta desaparecer."""
import math
import random

from . import ajustes as aj

GRAVEDAD = 700.0           # px/s²
VIDA_MIN, VIDA_MAX = 0.45, 1.0
VELOCIDAD_MIN, VELOCIDAD_MAX = 120.0, 420.0
TAMANO_MIN, TAMANO_MAX = 4, 10


class Particula:
    __slots__ = ("x", "y", "vx", "vy", "vida", "vida_total", "tamano", "color")

    def __init__(self, x, y, vx, vy, vida, tamano, color):
        self.x, self.y = x, y
        self.vx, self.vy = vx, vy
        self.vida = self.vida_total = vida
        self.tamano = tamano
        self.color = color

    def actualizar(self, dt):
        self.vida -= dt
        self.vy += GRAVEDAD * dt
        self.x += self.vx * dt
        self.y += self.vy * dt

    @property
    def viva(self):
        return self.vida > 0

    @property
    def lado(self):
        """Se encoge a medida que se acaba su vida (más barato que ir cambiando el alfa)."""
        return max(1, round(self.tamano * max(self.vida, 0) / self.vida_total))


class SistemaParticulas:
    def __init__(self):
        self.particulas = []

    def __len__(self):
        return len(self.particulas)

    def emitir(self, x, y, color, cantidad=20, dispersion=0.0):
        """Explosión en el punto (x, y) en píxeles del lienzo.

        `dispersion`: radio en píxeles alrededor del punto donde nacen las partículas
        (sirve para cuerpos grandes como el del jefe).
        """
        for _ in range(cantidad):
            angulo = random.uniform(0, math.tau)
            velocidad = random.uniform(VELOCIDAD_MIN, VELOCIDAD_MAX)
            radio = random.uniform(0, dispersion)
            origen = random.uniform(0, math.tau)
            self.particulas.append(Particula(
                x + math.cos(origen) * radio, y + math.sin(origen) * radio,
                math.cos(angulo) * velocidad, math.sin(angulo) * velocidad - 120.0,   # sesgo hacia arriba
                random.uniform(VIDA_MIN, VIDA_MAX), random.randint(TAMANO_MIN, TAMANO_MAX),
                self._variar(color)))

    def emitir_en_celda(self, x, y, color, cantidad=20, dispersion=0.0):
        """Igual que `emitir`, pero con la posición en celdas (origen abajo a la izquierda)."""
        self.emitir((x + 0.5) * aj.CELDA, aj.ALTO - (y + 0.5) * aj.CELDA, color, cantidad, dispersion)

    @staticmethod
    def _variar(color):
        """Un poco más claro u oscuro, para que la nube no sea un bloque de un solo tono."""
        factor = random.uniform(0.7, 1.25)
        return tuple(max(0, min(255, round(c * factor))) for c in color)

    def actualizar(self, dt):
        for particula in self.particulas:
            particula.actualizar(dt)
        self.particulas = [p for p in self.particulas if p.viva]

    def dibujar(self, lienzo):
        for p in self.particulas:
            lado = p.lado
            lienzo.fill(p.color, (round(p.x - lado / 2), round(p.y - lado / 2), lado, lado))
