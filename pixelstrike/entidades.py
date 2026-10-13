"""Entidades del juego: jugador, enemigos, balas e ítems de power up."""
import random

from . import ajustes as aj
from . import datos as d
from .recursos import recursos
from .temporizador import Parpadeo


# ============================================================================
# Armas y balas
# ============================================================================
class Arma:
    """Arma en uso. Los power ups la modifican con multiplicadores (fáciles de revertir)."""

    def __init__(self, datos):
        self.datos = datos
        self.mult_danio = 1
        self.mult_cadencia = 1.0

    @property
    def danio(self):
        return round(self.datos.danio * self.mult_danio)

    @property
    def cadencia(self):
        return self.datos.cadencia * self.mult_cadencia

    def sonar(self):
        recursos.reproducir_al_azar(self.datos.sonidos)


class Bala:
    direccion = 1

    def __init__(self, x, y, imagen, danio):
        self.x = x
        self.y = y
        self.imagen = imagen
        self.danio = danio
        self.activa = True
        self._acumulado = 0.0

    def actualizar(self, dt, nivel):
        # El blanco pudo moverse hasta la celda de la bala desde el cuadro anterior.
        if self._impacta(nivel):
            self.activa = False
            return
        # Cada paso mueve la bala una celda y se revisa la colisión AL LLEGAR a ella.
        # Si solo se mirara la celda de origen, la bala y el blanco podrían cruzarse
        # (ella entra a su celda justo cuando él sale) sin detectarse nunca.
        self._acumulado += aj.VELOCIDAD_BALA * dt
        while self._acumulado >= 1 and self.activa:
            self._acumulado -= 1
            self.x += self.direccion
            if self._fuera_de_pantalla() or self._impacta(nivel):
                self.activa = False

    def dibujar(self, lienzo):
        recursos.dibujar(lienzo, self.imagen, self.x, self.y)

    def _fuera_de_pantalla(self):
        raise NotImplementedError

    def _impacta(self, nivel):
        raise NotImplementedError


class BalaJugador(Bala):
    direccion = 1

    def _fuera_de_pantalla(self):
        return self.x > aj.ANCHO_GRILLA

    def _impacta(self, nivel):
        blanco = nivel.blanco_en(self.x, self.y)
        if blanco is None:
            return False
        recursos.reproducir_al_azar(d.SONIDOS_IMPACTO)
        blanco.recibir_danio(self.danio, nivel)
        return True


class BalaEnemigo(Bala):
    direccion = -1

    def _fuera_de_pantalla(self):
        return self.x < 0

    def _impacta(self, nivel):
        jugador = nivel.jugador
        if (jugador.x, jugador.y) != (self.x, self.y):
            return False
        recursos.reproducir_al_azar(d.SONIDOS_IMPACTO)
        jugador.recibir_danio(self.danio)
        return True


# ============================================================================
# Jugador
# ============================================================================
class Jugador:
    def __init__(self, personaje):
        self.personaje = personaje
        self.vida_max = personaje.vida_max
        self.vida = personaje.vida_max
        self.arma = Arma(personaje.arma)
        self.x, self.y = aj.JUGADOR_INICIO
        self.defensa = 1                 # multiplicador del daño recibido
        self.enfriamiento = 0.0
        self.efectos = {}                # clave de power up -> segundos restantes
        self.parpadeo = Parpadeo()

    @property
    def vivo(self):
        return self.vida > 0

    @property
    def hay_powerup_activo(self):
        return bool(self.efectos)

    def mover(self, dx, dy):
        x, y = self.x + dx, self.y + dy
        if 0 <= x <= aj.COLUMNA_MAX and 0 <= y <= aj.FILA_MAX:
            self.x, self.y = x, y

    def disparar(self):
        """Devuelve una BalaJugador, o None si el arma todavía se está enfriando."""
        if not self.vivo or self.enfriamiento > 0:
            return None
        self.arma.sonar()
        self.enfriamiento = self.arma.cadencia
        return BalaJugador(self.x + 1, self.y, self.arma.datos.imagen_bala, self.arma.danio)

    def recibir_danio(self, cantidad):
        if not self.vivo:
            return
        antes = self.vida
        self.vida = max(0, self.vida - cantidad * self.defensa)
        if antes > aj.VIDA_CRITICA >= self.vida > 0:
            recursos.reproducir(d.SFX_LATIDO)
            self.parpadeo.iniciar(0.1, 8)

    def aplicar_powerup(self, clave):
        self.efectos[clave] = d.POWERUPS[clave].duracion     # si ya estaba activo, se renueva
        self._configurar_efecto(clave, True)

    def actualizar(self, dt):
        self.enfriamiento = max(0.0, self.enfriamiento - dt)
        self.parpadeo.actualizar(dt)
        for clave in list(self.efectos):
            self.efectos[clave] -= dt
            if self.efectos[clave] <= 0:
                del self.efectos[clave]
                self._configurar_efecto(clave, False)

    def dibujar(self, lienzo):
        if self.vivo and self.parpadeo.visible:
            recursos.dibujar(lienzo, self.personaje.skin, self.x, self.y)

    def _configurar_efecto(self, clave, activo):
        if clave == "danio":
            self.arma.mult_danio = 2 if activo else 1
        elif clave == "cadencia":
            self.arma.mult_cadencia = 0.4 if activo else 1.0    # 60% menos de espera
        elif clave == "defensa":
            self.defensa = 0 if activo else 1                    # inmune al daño


# ============================================================================
# Enemigos
# ============================================================================
class Enemigo:
    def __init__(self, tipo):
        self.tipo = tipo
        self.x = aj.ENEMIGO_X_INICIAL
        self.y = random.randint(0, aj.FILA_MAX)
        self.vida = tipo.vida
        self.powerup = None              # clave del power up que suelta al morir
        self.activo = True
        self._intervalo_paso = random.uniform(*tipo.intervalo_paso)
        self._t_paso = self._intervalo_paso
        self._t_disparo = tipo.arma.cadencia

    def actualizar(self, dt, nivel):
        self._t_paso -= dt
        if self._t_paso <= 0:
            self._t_paso += self._intervalo_paso
            self.x -= 1
            if self.x < aj.ENEMIGO_X_LIMITE:
                nivel.enemigo_escapo(self)
                return
        self._t_disparo -= dt
        if self._t_disparo <= 0:
            self._t_disparo += self.tipo.arma.cadencia
            self._disparar(nivel)

    def _disparar(self, nivel):
        jugador = nivel.jugador
        # Solo dispara si el jugador está en su fila y adelante de él
        if jugador.vivo and jugador.y == self.y and jugador.x < self.x:
            arma = self.tipo.arma
            nivel.balas.append(BalaEnemigo(self.x - 1, self.y, arma.imagen_bala, arma.danio))
            recursos.reproducir_al_azar(arma.sonidos)

    def recibir_danio(self, cantidad, nivel):
        self.vida -= cantidad
        if self.vida <= 0 and self.activo:
            self.activo = False
            nivel.enemigo_muerto(self)

    def dibujar(self, lienzo):
        recursos.dibujar(lienzo, self.tipo.imagen, self.x, self.y)


# ============================================================================
# Ítems
# ============================================================================
class ItemPowerUp:
    def __init__(self, clave, x, y):
        self.datos = d.POWERUPS[clave]
        self.x = x
        self.y = y
        self.restante = aj.DURACION_ITEM_POWERUP
        self.activo = True

    def actualizar(self, dt, nivel):
        jugador = nivel.jugador
        if jugador.vivo and (jugador.x, jugador.y) == (self.x, self.y):
            recursos.reproducir(d.SFX_POWERUP)
            jugador.aplicar_powerup(self.datos.clave)
            self.activo = False
            return
        self.restante -= dt
        if self.restante <= 0:
            self.activo = False

    def dibujar(self, lienzo):
        recursos.dibujar(lienzo, self.datos.item, self.x, self.y)
