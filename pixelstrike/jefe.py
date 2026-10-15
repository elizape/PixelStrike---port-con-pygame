"""Jefe final (Kratos) y sus ataques: bolas de fuego, filas de fuego y lluvia de fuego.

Las secuencias de cada ataque están escritas como generadores: cada `yield n`
significa "esperá n segundos". Se corren con `nivel.sim.correr(...)`, así que
se congelan solas cuando el juego está en pausa.
"""
import random

from . import ajustes as aj
from . import datos as d
from .entidades import BalaEnemigo, BalaJugador
from .interfaz import dibujar_barra_vida
from .recursos import recursos

DANIO_FUEGO = 10      # daño base del fuego en el piso y de la lluvia (se escala por dificultad)


class JefeFinal:
    COLUMNA = 27
    FILA_INICIAL = 2
    CANTIDAD_BOLAS = 3

    def __init__(self, nivel, dificultad=d.NORMAL):
        self.nivel = nivel
        self.arma = d.BOLA_FUEGO_KRATOS
        self.vida_max = dificultad.vida_jefe
        self.vida = self.vida_max
        self.intervalo_ataques = dificultad.intervalo_ataques_jefe
        self.danio_fuego = max(1, round(DANIO_FUEGO * dificultad.mult_danio))
        self.danio_bala = max(1, round(self.arma.danio * dificultad.mult_danio))
        self.x = self.COLUMNA
        self.y = self.FILA_INICIAL
        self.skin = d.JEFE_SKIN_INTRO
        self.vivo = True
        self.atacable = False            # durante la intro es invulnerable
        self.puede_atacar = True
        self.efectos = []                # ataques de área en curso (filas / lluvia)
        self._timer_ataques = None
        self._timer_esquiva = None

    # --- ciclo de combate -----------------------------------------------
    def comenzar_ataques(self):
        self.skin = d.JEFE_SKIN_COMBATE
        self.atacable = True
        self.nivel.mostrar(d.NOMBRE_KRATOS)
        self._timer_ataques = self.nivel.sim.cada(self.intervalo_ataques, self._elegir_ataque)

    def _elegir_ataque(self):
        if not self.puede_atacar:
            return
        ataque = random.choice(("lluvia", "filas", "bolas"))
        if ataque == "lluvia":
            self._ataque_de_area(LluviaFuego(self, cantidad=13, duracion=5))
        elif ataque == "filas":
            self._ataque_de_area(FilasFuego(self))
        else:
            self.puede_atacar = False
            self.nivel.sim.correr(self._ataque_bolas())

    def actualizar(self, dt, nivel):
        for efecto in list(self.efectos):
            efecto.actualizar(dt, nivel)

    def recibir_danio(self, cantidad, nivel):
        self.vida = max(0, self.vida - cantidad)
        if self.vida == 0:
            self.vivo = False
            self.atacable = False
            self.efectos.clear()
            for timer in (self._timer_ataques, self._timer_esquiva):
                if timer:
                    timer.cancelar()
            nivel.jefe_derrotado()

    # --- ataques --------------------------------------------------------
    def _ataque_de_area(self, efecto):
        self.puede_atacar = False
        self._timer_esquiva = self.nivel.sim.cada(0.5, self._esquivar)
        self.efectos.append(efecto)
        self.nivel.sim.correr(efecto.guion())

    def terminar_ataque_de_area(self, efecto):
        if efecto in self.efectos:
            self.efectos.remove(efecto)
        if self._timer_esquiva:
            self._timer_esquiva.cancelar()
            self._timer_esquiva = None
        self.puede_atacar = True

    def _esquivar(self):
        """Mientras prepara un ataque de área, esquiva las balas del jugador que vienen por su fila."""
        if not any(isinstance(b, BalaJugador) and b.y == self.y for b in self.nivel.balas):
            return
        if 0 < self.y < aj.FILA_MAX:
            self.y += random.choice((1, -1))
        elif self.y == aj.FILA_MAX:
            self.y -= 1
        else:
            self.y += 1

    def _ataque_bolas(self):
        """Sube a la fila 3 y baja de a una, disparando tres bolas de fuego en cada fila."""
        while True:
            yield 0.5
            if not self.vivo:
                return
            if self.y < aj.FILA_MAX:
                self.y += 1
            else:
                break
        cadencia = self.arma.cadencia
        fila, bolas = aj.FILA_MAX, 0
        while fila >= 0:
            yield cadencia
            if not self.vivo:
                return
            if bolas < self.CANTIDAD_BOLAS:
                self._disparar()
                bolas += 1
            else:
                bolas = 0
                fila -= 1
                if self.y > 0:
                    self.y -= 1
        while True:                       # vuelve a su fila original
            yield cadencia
            if not self.vivo:
                return
            if self.y < self.FILA_INICIAL:
                self.y += 1
            else:
                break
        self.puede_atacar = True

    def _disparar(self):
        self.nivel.balas.append(BalaEnemigo(self.x - 1, self.y, self.arma.imagen_bala, self.danio_bala))
        recursos.reproducir_al_azar(self.arma.sonidos)

    # --- dibujo ---------------------------------------------------------
    def dibujar(self, lienzo):
        if self.vivo:
            recursos.dibujar(lienzo, self.skin, self.x, self.y)

    def dibujar_suelo(self, lienzo):
        for efecto in self.efectos:
            efecto.dibujar_suelo(lienzo)

    def dibujar_aire(self, lienzo):
        for efecto in self.efectos:
            efecto.dibujar_aire(lienzo)

    def dibujar_barra_vida(self, lienzo):
        if self.vivo and self.atacable:
            dibujar_barra_vida(lienzo, self.vida, self.vida_max, 8, 12, d.CORAZON_VIOLETA)


class _AtaqueDeArea:
    def __init__(self, jefe):
        self.jefe = jefe

    def actualizar(self, dt, nivel):
        pass

    def dibujar_suelo(self, lienzo):
        pass

    def dibujar_aire(self, lienzo):
        pass


class FilasFuego(_AtaqueDeArea):
    """Tres de las cuatro filas se prenden fuego tras un aviso."""

    def __init__(self, jefe):
        super().__init__(jefe)
        valores = [True, True, True, False]
        random.shuffle(valores)
        self.filas = [aj.FILA_MAX - i for i, prendida in enumerate(valores) if prendida]
        self.fase = "espera"              # espera -> advertencia -> pausa -> fuego
        self._t_dano = 0.0

    def guion(self):
        yield 0.4
        self.fase = "advertencia"
        yield 1.5
        self.fase = "pausa"
        yield 0.6
        self.fase = "fuego"
        self._t_dano = 0.5
        yield 5.0
        self.jefe.terminar_ataque_de_area(self)

    def actualizar(self, dt, nivel):
        if self.fase != "fuego":
            return
        self._t_dano -= dt
        while self._t_dano <= 0:
            self._t_dano += 0.5
            if nivel.jugador.y in self.filas:
                nivel.jugador.recibir_danio(self.jefe.danio_fuego)

    def dibujar_suelo(self, lienzo):
        imagen = {"advertencia": d.FILA_ADVERTENCIA, "fuego": d.FILA_FUEGO}.get(self.fase)
        if imagen:
            for fila in self.filas:
                recursos.dibujar(lienzo, imagen, 0, fila)


class _Gota:
    ALTURA_INICIAL = 20

    def __init__(self, x, y_objetivo, danio=DANIO_FUEGO):
        self.x = x
        self.y_objetivo = y_objetivo
        self.danio = danio
        self.y = float(self.ALTURA_INICIAL)
        self.aterrizo = False
        self._t_dano = 0.25

    def actualizar(self, dt, nivel):
        if not self.aterrizo:
            self.y -= aj.VELOCIDAD_GOTA * dt
            if self.y <= self.y_objetivo:
                self.y = self.y_objetivo
                self.aterrizo = True
            return
        # Una vez en el piso, quema cada 0.25 s a quien esté parado encima
        self._t_dano -= dt
        while self._t_dano <= 0:
            self._t_dano += 0.25
            jugador = nivel.jugador
            if (jugador.x, jugador.y) == (self.x, self.y_objetivo):
                jugador.recibir_danio(self.danio)


class LluviaFuego(_AtaqueDeArea):
    """Marca celdas al azar y, un instante después, hace caer fuego sobre ellas."""

    def __init__(self, jefe, cantidad, duracion):
        super().__init__(jefe)
        self.duracion = duracion
        self.gotas = [_Gota(random.randint(0, 25), random.randint(0, aj.FILA_MAX), jefe.danio_fuego)
                      for _ in range(cantidad)]
        self.fase = "advertencia"         # advertencia -> espera -> lluvia

    def guion(self):
        nivel = self.jefe.nivel
        nivel.mostrar_por(d.ATENCION_LLUVIA, 2.5, nivel.sim)
        recursos.reproducir(d.SFX_ATENCION)
        yield 2.52
        self.fase = "espera"
        recursos.reproducir(d.SFX_TRUENO)
        yield 0.7
        self.fase = "lluvia"
        for sonido in d.SFX_LLUVIA:
            recursos.reproducir(sonido)
        nivel.sim.despues(1.5, lambda: recursos.reproducir(d.SFX_LLUVIA_FINAL))
        yield self.duracion
        self.gotas = []
        self.jefe.terminar_ataque_de_area(self)

    def actualizar(self, dt, nivel):
        if self.fase == "lluvia":
            for gota in self.gotas:
                gota.actualizar(dt, nivel)

    def dibujar_suelo(self, lienzo):
        if self.fase == "advertencia":
            for gota in self.gotas:
                recursos.dibujar(lienzo, d.GOTA_ADVERTENCIA, gota.x, gota.y_objetivo)

    def dibujar_aire(self, lienzo):
        if self.fase == "lluvia":
            for gota in self.gotas:
                recursos.dibujar(lienzo, d.GOTA_FUEGO, gota.x, gota.y)
