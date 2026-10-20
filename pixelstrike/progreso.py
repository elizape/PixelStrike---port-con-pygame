"""Estado que persiste entre pantallas (niveles, personajes, puntuaciones y XP)."""
import json
import os
import sys
from pathlib import Path

from . import ajustes as aj
from . import datos as d


def calcular_nivel_xp(xp_total: int) -> dict:
    """Calcula el nivel del jugador, título, progreso en el nivel actual y porcentaje.

    Nivel 1: 0 - 149 XP (Recluta)
    Nivel 2: 150 - 399 XP (Cadete)
    Nivel 3: 400 - 799 XP (Soldado)
    Nivel 4: 800 - 1399 XP (Veterano)
    Nivel 5: 1400 - 2199 XP (Comandante)
    Nivel 6: 2200 - 3199 XP (Élite)
    Nivel 7: 3200 - 4199 XP (Maestro)
    Nivel 8+: +1000 XP por nivel adicional (Leyenda)
    """
    xp = max(0, int(xp_total))
    umbrales = d.UMBRALES_XP

    if xp < umbrales[-1]:
        nivel = 1
        for i in range(len(umbrales) - 1, -1, -1):
            if xp >= umbrales[i]:
                nivel = i + 1
                base = umbrales[i]
                tope = umbrales[i + 1]
                break
    else:
        extra = (xp - umbrales[-1]) // d.XP_POR_NIVEL_ADICIONAL
        nivel = len(umbrales) + extra
        base = umbrales[-1] + extra * d.XP_POR_NIVEL_ADICIONAL
        tope = base + d.XP_POR_NIVEL_ADICIONAL

    xp_en_nivel = xp - base
    xp_para_subir = tope - base
    porcentaje = min(1.0, max(0.0, xp_en_nivel / xp_para_subir)) if xp_para_subir > 0 else 1.0
    titulo = d.RANGOS_XP.get(nivel, "Leyenda")

    return {
        "nivel": nivel,
        "titulo": titulo,
        "xp_total": xp,
        "xp_en_nivel": xp_en_nivel,
        "xp_para_subir": xp_para_subir,
        "xp_siguiente": tope,
        "porcentaje": porcentaje,
    }


class Progreso:
    def __init__(self, ruta_guardado=None, auto_cargar=True):
        self.ruta_guardado = Path(ruta_guardado) if ruta_guardado else aj.RUTA_GUARDADO
        self.niveles = {"nivel0"}
        self.personajes = {d.PERSONAJE_INICIAL}
        self.personaje = d.PERSONAJE_INICIAL      # clave del personaje elegido
        self.indice_tarjeta = 0                   # tarjeta visible en el selector de personajes
        self.dificultad = d.DIFICULTAD_INICIAL    # clave de la dificultad elegida
        self.xp_total = 0
        self.puntajes = {}                        # clave_nivel -> mejor_puntaje_xp

        es_test = "unittest" in sys.modules or os.environ.get("SDL_VIDEODRIVER") == "dummy"
        if auto_cargar and (ruta_guardado is not None or not es_test):
            self.cargar()

    @property
    def nivel_xp(self) -> int:
        return calcular_nivel_xp(self.xp_total)["nivel"]

    @property
    def info_xp(self) -> dict:
        return calcular_nivel_xp(self.xp_total)

    def dificultad_actual(self):
        return d.DIFICULTADES[self.dificultad]

    def desbloquear_nivel(self, clave):
        if clave:
            self.niveles.add(clave)
            self.guardar()

    def nivel_desbloqueado(self, clave):
        return clave in self.niveles

    def desbloquear_personaje(self, clave):
        """Devuelve True si el personaje estaba bloqueado hasta ahora."""
        if clave is None or clave in self.personajes:
            return False
        self.personajes.add(clave)
        self.guardar()
        return True

    def personaje_desbloqueado(self, clave):
        return clave in self.personajes

    def puntaje_nivel(self, clave: str) -> int:
        return self.puntajes.get(clave, 0)

    def registrar_puntaje_nivel(self, clave: str, xp_obtenida: int):
        xp_obtenida = max(0, int(xp_obtenida))
        self.xp_total += xp_obtenida
        if clave:
            self.puntajes[clave] = max(self.puntajes.get(clave, 0), xp_obtenida)
        self.guardar()

    def guardar(self, ruta=None) -> bool:
        destino = Path(ruta) if ruta else self.ruta_guardado
        try:
            datos = {
                "niveles": sorted(list(self.niveles)),
                "personajes": sorted(list(self.personajes)),
                "personaje": self.personaje,
                "indice_tarjeta": self.indice_tarjeta,
                "dificultad": self.dificultad,
                "xp_total": self.xp_total,
                "puntajes": self.puntajes,
            }
            destino.parent.mkdir(parents=True, exist_ok=True)
            tmp = destino.with_suffix(".tmp")
            with open(tmp, "w", encoding="utf-8") as f:
                json.dump(datos, f, indent=4)
            tmp.replace(destino)
            return True
        except Exception:
            return False

    def cargar(self, ruta=None) -> bool:
        origen = Path(ruta) if ruta else self.ruta_guardado
        if not origen.is_file():
            return False
        try:
            with open(origen, "r", encoding="utf-8") as f:
                datos = json.load(f)
            if isinstance(datos.get("niveles"), list):
                self.niveles = set(datos["niveles"])
            if isinstance(datos.get("personajes"), list):
                self.personajes = set(datos["personajes"])
            if datos.get("personaje") in d.PERSONAJES:
                self.personaje = datos["personaje"]
            if isinstance(datos.get("indice_tarjeta"), int):
                self.indice_tarjeta = datos["indice_tarjeta"]
            if datos.get("dificultad") in d.DIFICULTADES:
                self.dificultad = datos["dificultad"]
            if isinstance(datos.get("xp_total"), (int, float)):
                self.xp_total = max(0, int(datos["xp_total"]))
            if isinstance(datos.get("puntajes"), dict):
                self.puntajes = {k: max(0, int(v)) for k, v in datos["puntajes"].items() if isinstance(v, (int, float))}
            return True
        except Exception:
            return False

    def borrar_progreso(self, ruta=None, nueva_dificultad=None) -> bool:
        destino = Path(ruta) if ruta else self.ruta_guardado
        self.niveles = {"nivel0"}
        self.personajes = {d.PERSONAJE_INICIAL}
        self.personaje = d.PERSONAJE_INICIAL
        self.indice_tarjeta = 0
        self.dificultad = nueva_dificultad if nueva_dificultad in d.DIFICULTADES else d.DIFICULTAD_INICIAL
        self.xp_total = 0
        self.puntajes = {}
        try:
            if destino.is_file():
                destino.unlink()
            return True
        except Exception:
            return False

    def cambiar_dificultad(self, nueva: str) -> bool:
        """Cambia la dificultad elegida. Si la nueva dificultad es distinta de la actual,
        borra todos los datos de progreso (niveles, personajes, XP) y guarda.
        Devuelve True si cambió la dificultad y se borró el progreso.
        """
        if nueva not in d.DIFICULTADES:
            return False
        if nueva != self.dificultad:
            self.borrar_progreso(nueva_dificultad=nueva)
            self.guardar()
            return True
        self.guardar()
        return False
