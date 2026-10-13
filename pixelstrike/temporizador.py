"""Planificador de eventos (reemplaza a game.schedule / game.onTick de Wollok)."""


class Temporizador:
    __slots__ = ("restante", "intervalo", "callback", "cancelado")

    def __init__(self, espera, callback, intervalo=None):
        self.restante = espera
        self.intervalo = intervalo
        self.callback = callback
        self.cancelado = False

    def cancelar(self):
        self.cancelado = True


class Planificador:
    """Ejecuta callbacks diferidos o periódicos a medida que avanza `actualizar(dt)`.

    Si no se llama a `actualizar`, el tiempo "se congela": así se implementa la
    pausa sin tener que chequear una bandera en cada callback.
    """

    def __init__(self):
        self._lista = []

    def despues(self, espera, callback):
        return self._agregar(Temporizador(espera, callback))

    def cada(self, intervalo, callback):
        assert intervalo > 0
        return self._agregar(Temporizador(intervalo, callback, intervalo))

    def correr(self, generador):
        """Corre una secuencia escrita como generador: cada `yield n` espera n segundos."""
        def avanzar():
            try:
                espera = next(generador)
            except StopIteration:
                return
            self.despues(espera, avanzar)
        avanzar()

    def limpiar(self):
        for t in self._lista:
            t.cancelado = True
        self._lista = []

    def actualizar(self, dt):
        for t in list(self._lista):
            if t.cancelado:
                continue
            t.restante -= dt
            while t.restante <= 0 and not t.cancelado:
                t.callback()
                if t.intervalo is None:
                    t.cancelado = True
                else:
                    t.restante += t.intervalo
        self._lista = [t for t in self._lista if not t.cancelado]

    def _agregar(self, temporizador):
        self._lista.append(temporizador)
        return temporizador


class Parpadeo:
    """Alterna `visible` cada `intervalo` segundos (equivale a controlDeAnimaciones.parpadear_1)."""

    def __init__(self):
        self.visible = True
        self._restantes = 0
        self._intervalo = 0.0
        self._t = 0.0

    def iniciar(self, intervalo, repeticiones):
        self.visible = False
        self._restantes = repeticiones - 1
        self._intervalo = intervalo
        self._t = intervalo

    def actualizar(self, dt):
        if self._restantes <= 0:
            return
        self._t -= dt
        while self._t <= 0 and self._restantes > 0:
            self.visible = not self.visible
            self._restantes -= 1
            self._t += self._intervalo
