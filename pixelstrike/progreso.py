"""Estado que persiste entre pantallas (qué niveles y personajes están desbloqueados)."""
from . import datos as d


class Progreso:
    def __init__(self):
        self.niveles = {"nivel0"}
        self.personajes = {d.PERSONAJE_INICIAL}
        self.personaje = d.PERSONAJE_INICIAL      # clave del personaje elegido
        self.indice_tarjeta = 0                   # tarjeta visible en el selector de personajes
        self.dificultad = d.DIFICULTAD_INICIAL    # clave de la dificultad elegida

    def dificultad_actual(self):
        return d.DIFICULTADES[self.dificultad]

    def desbloquear_nivel(self, clave):
        if clave:
            self.niveles.add(clave)

    def nivel_desbloqueado(self, clave):
        return clave in self.niveles

    def desbloquear_personaje(self, clave):
        """Devuelve True si el personaje estaba bloqueado hasta ahora."""
        if clave is None or clave in self.personajes:
            return False
        self.personajes.add(clave)
        return True

    def personaje_desbloqueado(self, clave):
        return clave in self.personajes
