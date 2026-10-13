"""Pantallas de menú: selector de niveles, selector de personajes y créditos."""
import pygame

from . import ajustes as aj
from . import datos as d
from .entrada import TeclasRepetibles
from .escena import Escena
from .recursos import recursos


class SelectorNiveles(Escena):
    """Pasillo con una puerta por nivel. Verde = jugable, roja = bloqueado."""

    def __init__(self, juego):
        super().__init__(juego)
        self.x, self.y = aj.SELECTOR_INICIO
        self.bloqueado = False        # true mientras se reproduce la transición
        self.teclas = TeclasRepetibles({
            aj.TECLA_ARRIBA: self._subir,
            aj.TECLA_ABAJO: self._bajar,
            aj.TECLA_IZQUIERDA: self._izquierda,
            aj.TECLA_DERECHA: self._derecha,
        }, repetir=aj.MANTENER_PARA_MOVER)

    def al_entrar(self):
        recursos.musica(d.MUSICA_SELECTOR_NIVELES, aj.VOLUMEN_MUSICA)

    # --- movimiento: el jugador solo puede entrar a una puerta por debajo de ella ---
    def _bajo_una_puerta(self):
        return any(px <= self.x <= px + 1 for px, _ in d.PUERTAS)

    def _en_celda_izquierda_de_puerta(self):
        return any(self.x == px for px, _ in d.PUERTAS)

    def _en_celda_derecha_de_puerta(self):
        return any(self.x == px + 1 for px, _ in d.PUERTAS)

    def _subir(self):
        if not self.bloqueado and (self.y < 2 or (self.y == 2 and self._bajo_una_puerta())):
            self.y += 1

    def _bajar(self):
        if not self.bloqueado and self.y > 1:
            self.y -= 1

    def _izquierda(self):
        if self.bloqueado:
            return
        if (self.x > 0 and self.y < d.FILA_PUERTAS) or (
                self.y == d.FILA_PUERTAS and self._en_celda_derecha_de_puerta()):
            self.x -= 1

    def _derecha(self):
        if self.bloqueado:
            return
        if (self.x < aj.COLUMNA_MAX and self.y < d.FILA_PUERTAS) or (
                self.y == d.FILA_PUERTAS and self._en_celda_izquierda_de_puerta()):
            self.x += 1

    # --- eventos / lógica ---
    def manejar_evento(self, evento):
        if evento.type != pygame.KEYDOWN or self.bloqueado:
            return
        if self.teclas.tecla_abajo(evento.key):
            return
        if evento.key == aj.TECLA_DISPARO:       # 'p' abre el selector de personajes
            recursos.detener_musica()
            self.juego.ir_a_selector_personajes()

    def actualizar(self, dt):
        super().actualizar(dt)
        self.teclas.actualizar(dt)
        if self.bloqueado or self.y != d.FILA_PUERTAS:
            return
        for px, clave in d.PUERTAS:
            if self.x in (px, px + 1) and self.juego.progreso.nivel_desbloqueado(clave):
                self._entrar_al_nivel(clave)
                return

    def _entrar_al_nivel(self, clave):
        self.bloqueado = True
        recursos.reproducir(d.SFX_VICTORIA_3)
        self.ui.despues(2.65, lambda: self._ir_al_nivel(clave))

    def _ir_al_nivel(self, clave):
        recursos.detener_musica()
        self.juego.ir_a_nivel(clave)

    def dibujar(self, lienzo):
        recursos.dibujar_fondo(lienzo, d.FONDO_SELECTOR_NIVELES)
        for px, clave in d.PUERTAS:
            abierta = self.juego.progreso.nivel_desbloqueado(clave)
            recursos.dibujar(lienzo, d.PUERTA_DESBLOQUEADA if abierta else d.PUERTA_BLOQUEADA,
                             px, d.FILA_PUERTAS)
        personaje = d.PERSONAJES[self.juego.progreso.personaje]
        recursos.dibujar(lienzo, personaje.skin, self.x, self.y)
        self.dibujar_indicadores(lienzo)


class SelectorPersonajes(Escena):
    """Carrusel de tarjetas: A / D para navegar, Enter para elegir, P para volver."""

    def __init__(self, juego):
        super().__init__(juego)
        self.bloqueado = False

    def al_entrar(self):
        recursos.musica(d.MUSICA_SELECTOR_PERSONAJES, aj.VOLUMEN_MUSICA)

    def manejar_evento(self, evento):
        if evento.type != pygame.KEYDOWN or self.bloqueado:
            return
        tecla = evento.key
        if tecla == aj.TECLA_DERECHA:
            self._mover(1)
        elif tecla == aj.TECLA_IZQUIERDA:
            self._mover(-1)
        elif tecla in aj.TECLAS_ENTER:
            self._seleccionar()
        elif tecla == aj.TECLA_DISPARO:
            recursos.detener_musica()
            self.juego.ir_a_selector_niveles()

    def _mover(self, paso):
        progreso = self.juego.progreso
        nuevo = progreso.indice_tarjeta + paso
        if 0 <= nuevo < len(d.ORDEN_PERSONAJES):
            progreso.indice_tarjeta = nuevo
            self.ocultar(d.PERSONAJE_BLOQUEADO)
            recursos.reproducir(d.SFX_CLICK)

    def _seleccionar(self):
        progreso = self.juego.progreso
        personaje = d.ORDEN_PERSONAJES[progreso.indice_tarjeta]
        if progreso.personaje_desbloqueado(personaje.clave):
            progreso.personaje = personaje.clave
            self.bloqueado = True
            recursos.reproducir(d.SFX_SELECCION_PERSONAJE)
            self.ui.despues(2.175, self._terminar)
        elif d.PERSONAJE_BLOQUEADO not in self.indicadores:
            self.mostrar(d.PERSONAJE_BLOQUEADO)
            recursos.reproducir(d.SFX_ERROR)

    def _terminar(self):
        recursos.detener_musica()
        self.juego.ir_a_selector_niveles()

    def dibujar(self, lienzo):
        recursos.dibujar_fondo(lienzo, d.FONDO_SELECTOR_PERSONAJES)
        tarjeta = d.ORDEN_PERSONAJES[self.juego.progreso.indice_tarjeta].tarjeta
        recursos.dibujar(lienzo, tarjeta, *d.POSICION_TARJETA)
        self.dibujar_indicadores(lienzo)


class Creditos(Escena):
    DURACION_TOTAL = 26.0

    def al_entrar(self):
        recursos.musica(d.MUSICA_CREDITOS, aj.VOLUMEN_MUSICA_CREDITOS)
        self.mostrar(d.TUTO_ENTER)
        self.secuencia(d.CREDITOS, con_sonido=True)
        self.ui.despues(self.DURACION_TOTAL, self._terminar)

    def manejar_evento(self, evento):
        if evento.type == pygame.KEYDOWN and evento.key in aj.TECLAS_ENTER:
            self._terminar()

    def _terminar(self):
        recursos.detener_musica()
        self.juego.ir_a_selector_niveles()

    def dibujar(self, lienzo):
        recursos.dibujar_fondo(lienzo, d.FONDO_CREDITOS)
        self.dibujar_indicadores(lienzo)
