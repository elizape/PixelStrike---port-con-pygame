"""Tests del selector de dificultad. Se ejecutan sin ventana ni audio:

    python -m unittest discover -s tests -v
"""
import os
import random
import sys
import unittest
from pathlib import Path

os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
os.environ.setdefault("SDL_AUDIODRIVER", "dummy")
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import pygame  # noqa: E402

from pixelstrike import ajustes as aj  # noqa: E402
from pixelstrike import datos as d  # noqa: E402
from pixelstrike.entidades import Enemigo, Jugador  # noqa: E402
from pixelstrike.escena_nivel import EscenaNivel  # noqa: E402
from pixelstrike.escenas_menu import SelectorDificultad, SelectorNiveles  # noqa: E402
from pixelstrike.jefe import JefeFinal  # noqa: E402
from pixelstrike.juego import Juego  # noqa: E402


def tecla(clave):
    return pygame.event.Event(pygame.KEYDOWN, key=clave)


class NivelFalso:
    """Lo mínimo que necesita un enemigo para disparar."""

    def __init__(self):
        self.jugador = Jugador(d.BYTE_HUNTER)
        self.balas = []


def primera_bala(enemigo):
    nivel = NivelFalso()
    nivel.jugador.x, nivel.jugador.y = 0, enemigo.y      # en su fila y adelante de él
    enemigo._disparar(nivel)
    return nivel.balas[0]


class DatosDificultadTest(unittest.TestCase):
    def test_hay_tres_dificultades_con_normal_en_el_medio(self):
        self.assertEqual([x.clave for x in d.ORDEN_DIFICULTADES], ["facil", "normal", "dificil"])
        self.assertEqual(d.DIFICULTAD_INICIAL, "normal")

    def test_normal_es_el_juego_original(self):
        n = d.NORMAL
        self.assertEqual((n.mult_vida, n.mult_velocidad, n.mult_cadencia, n.mult_danio, n.mult_spawn),
                         (1.0, 1.0, 1.0, 1.0, 1.0))
        self.assertEqual((n.danio_escape, n.vida_jefe, n.intervalo_ataques_jefe), (15, 150, 1.1))


class EnemigoTest(unittest.TestCase):
    def test_sin_dificultad_equivale_a_normal(self):
        for tipo in (d.ALIEN_RAPTOR, d.CRAWLER):
            e = Enemigo(tipo)
            self.assertEqual(e.vida, tipo.vida)
            self.assertEqual(e._cadencia, tipo.arma.cadencia)
            self.assertEqual(e._danio_bala, tipo.arma.danio)
            self.assertTrue(tipo.intervalo_paso[0] <= e._intervalo_paso <= tipo.intervalo_paso[1])

    def test_vida_segun_dificultad(self):
        self.assertEqual(Enemigo(d.ALIEN_RAPTOR, d.FACIL).vida, 10)
        self.assertEqual(Enemigo(d.CRAWLER, d.FACIL).vida, 15)
        self.assertEqual(Enemigo(d.ALIEN_RAPTOR, d.DIFICIL).vida, 30)
        self.assertEqual(Enemigo(d.CRAWLER, d.DIFICIL).vida, 45)

    def test_velocidad_segun_dificultad(self):
        for _ in range(30):
            facil = Enemigo(d.CRAWLER, d.FACIL)
            dificil = Enemigo(d.CRAWLER, d.DIFICIL)
            self.assertTrue(0.5 / 0.8 <= facil._intervalo_paso <= 0.75 / 0.8)
            self.assertTrue(0.5 / 1.25 <= dificil._intervalo_paso <= 0.75 / 1.25)

    def test_cadencia_y_danio_de_la_bala(self):
        facil = Enemigo(d.ALIEN_RAPTOR, d.FACIL)
        dificil = Enemigo(d.ALIEN_RAPTOR, d.DIFICIL)
        self.assertAlmostEqual(facil._cadencia, 0.8 * 1.25)
        self.assertAlmostEqual(dificil._cadencia, 0.8 * 0.8)
        self.assertEqual(primera_bala(facil).danio, 5)
        self.assertEqual(primera_bala(Enemigo(d.ALIEN_RAPTOR)).danio, 10)
        self.assertEqual(primera_bala(dificil).danio, 15)

    def test_no_se_modifican_los_datos_base(self):
        Enemigo(d.CRAWLER, d.DIFICIL)
        self.assertEqual(d.CRAWLER.vida, 30)
        self.assertEqual(d.BOLA_FUEGO.cadencia, 1.2)

    def test_el_danio_escalado_sobrevive_al_power_up_de_defensa(self):
        # Jugador.defensa se restaura a 1 al terminar el power up: no debe pisar la dificultad
        nivel = NivelFalso()
        jugador = nivel.jugador
        jugador.aplicar_powerup("defensa")
        jugador.recibir_danio(100)
        self.assertEqual(jugador.vida, jugador.vida_max)                  # inmune mientras dura
        jugador.actualizar(d.POWERUPS["defensa"].duracion + 1)
        self.assertEqual(jugador.defensa, 1)
        enemigo = Enemigo(d.ALIEN_RAPTOR, d.DIFICIL)
        enemigo.y = jugador.y
        jugador.x = 0
        enemigo._disparar(nivel)
        jugador.recibir_danio(nivel.balas[0].danio)
        self.assertEqual(jugador.vida, jugador.vida_max - 15)


class JefeTest(unittest.TestCase):
    def setUp(self):
        self.juego = Juego()

    def jefe(self, dificultad):
        self.juego.progreso.dificultad = dificultad.clave
        nivel = EscenaNivel(self.juego, "nivel4")
        return nivel.jefe

    def test_valores_por_dificultad(self):
        casos = ((d.FACIL, 100, 1.4, 5, 5), (d.NORMAL, 150, 1.1, 10, 10), (d.DIFICIL, 225, 0.8, 15, 15))
        for dif, vida, intervalo, fuego, bala in casos:
            jefe = self.jefe(dif)
            self.assertEqual(jefe.vida_max, vida)
            self.assertEqual(jefe.vida, vida)
            self.assertEqual(jefe.intervalo_ataques, intervalo)
            self.assertEqual(jefe.danio_fuego, fuego)
            self.assertEqual(jefe.danio_bala, bala)

    def test_el_jefe_usa_el_intervalo_de_ataques(self):
        jefe = self.jefe(d.DIFICIL)
        jefe.comenzar_ataques()
        timers = [t for t in jefe.nivel.sim._lista if t.intervalo is not None]
        self.assertEqual([t.intervalo for t in timers], [0.8])

    def test_constructor_por_defecto_es_normal(self):
        self.assertEqual(JefeFinal(NivelFalso()).vida_max, 150)


class EscenaNivelTest(unittest.TestCase):
    def setUp(self):
        self.juego = Juego()

    def nivel(self, clave, dificultad):
        self.juego.progreso.dificultad = dificultad.clave
        return EscenaNivel(self.juego, clave)

    def test_el_nivel_usa_la_dificultad_elegida(self):
        self.assertIs(self.nivel("nivel1", d.DIFICIL).dificultad, d.DIFICIL)

    def test_el_tutorial_siempre_es_normal(self):
        self.assertIs(self.nivel("nivel0", d.DIFICIL).dificultad, d.NORMAL)
        self.assertIs(self.nivel("nivel0", d.FACIL).dificultad, d.NORMAL)

    def test_danio_por_escape(self):
        for dif, esperado in ((d.FACIL, 10), (d.NORMAL, 15), (d.DIFICIL, 20)):
            nivel = self.nivel("nivel1", dif)
            nivel.enemigo_escapo(Enemigo(d.ALIEN_RAPTOR))
            self.assertEqual(nivel.jugador.vida, nivel.jugador.vida_max - esperado)

    def test_primer_enemigo_aparece_segun_el_tiempo_de_spawn(self):
        # nivel 1: 0.1 s de carga + 0.5 s + banner 3 s + 0.5 s + intervalo (4 s x mult_spawn)
        esperado = {"facil": 9.1, "normal": 8.1, "dificil": 7.1}
        for dif in d.ORDEN_DIFICULTADES:
            random.seed(1)
            nivel = self.nivel("nivel1", dif)
            nivel.al_entrar()
            t = 0.0
            while not nivel.enemigos and t < 20:
                nivel.actualizar(0.05)
                t += 0.05
            # delta de 0.25: el reloj avanza de a 0.05 s y la carga inicial se redondea hacia arriba
            self.assertAlmostEqual(t, esperado[dif.clave], delta=0.25, msg=dif.clave)


class FlujoDeEscenasTest(unittest.TestCase):
    def setUp(self):
        self.juego = Juego()

    def pulsar(self, clave):
        self.juego.escena.manejar_evento(tecla(clave))
        self.juego.actualizar(1 / 60)      # aplica el cambio de escena pendiente

    def test_el_juego_arranca_en_el_selector_de_dificultad_con_normal(self):
        self.assertIsInstance(self.juego.escena, SelectorDificultad)
        self.assertEqual(d.ORDEN_DIFICULTADES[self.juego.escena.indice].clave, "normal")

    def test_navegacion_con_limites(self):
        escena = self.juego.escena
        for _ in range(5):
            self.pulsar(aj.TECLA_ARRIBA)
        self.assertEqual(escena.indice, 0)
        for _ in range(5):
            self.pulsar(aj.TECLA_ABAJO)
        self.assertEqual(escena.indice, 2)

    def test_a_y_d_tambien_navegan(self):
        self.pulsar(aj.TECLA_IZQUIERDA)
        self.assertEqual(self.juego.escena.indice, 0)
        self.pulsar(aj.TECLA_DERECHA)
        self.assertEqual(self.juego.escena.indice, 1)

    def test_enter_guarda_la_eleccion_y_pasa_al_selector_de_niveles(self):
        self.pulsar(aj.TECLA_ABAJO)
        self.pulsar(pygame.K_RETURN)
        self.assertIsInstance(self.juego.escena, SelectorNiveles)
        self.assertEqual(self.juego.progreso.dificultad, "dificil")

    def test_esc_vuelve_a_elegir_sin_perder_el_progreso(self):
        self.juego.progreso.desbloquear_nivel("nivel1")
        self.juego.progreso.desbloquear_personaje("jade")
        self.pulsar(pygame.K_RETURN)                          # Normal -> selector de niveles
        self.pulsar(aj.TECLA_VOLVER)
        self.assertIsInstance(self.juego.escena, SelectorDificultad)
        self.assertEqual(self.juego.escena.indice, 1)         # arranca en la dificultad actual
        self.pulsar(aj.TECLA_IZQUIERDA)
        self.pulsar(pygame.K_RETURN)
        self.assertEqual(self.juego.progreso.dificultad, "facil")
        self.assertTrue(self.juego.progreso.nivel_desbloqueado("nivel1"))
        self.assertTrue(self.juego.progreso.personaje_desbloqueado("jade"))

    def test_reiniciar_un_nivel_conserva_la_dificultad(self):
        self.juego.progreso.dificultad = "dificil"
        self.juego.ir_a_nivel("nivel1")
        self.juego._aplicar_cambio_de_escena()
        nivel = self.juego.escena
        nivel.estado = 2                                      # PAUSA
        self.pulsar(aj.TECLA_REINICIAR)
        self.assertIsInstance(self.juego.escena, EscenaNivel)
        self.assertIs(self.juego.escena.dificultad, d.DIFICIL)


class HumoTest(unittest.TestCase):
    """Recorre todos los niveles en cada dificultad sin que se rompa nada."""

    def test_todos_los_niveles_en_todas_las_dificultades(self):
        juego = Juego()
        for dif in d.ORDEN_DIFICULTADES:
            juego.progreso.dificultad = dif.clave
            for clave in d.NIVELES:
                juego.ir_a_nivel(clave)
                juego._aplicar_cambio_de_escena()
                nivel = juego.escena
                for i in range(60 * 12):
                    if i % 5 == 0:
                        nivel._disparar()
                    if i % 40 == 0:
                        nivel._avanzar_tutorial()
                    juego.actualizar(1 / 60)
                    juego.dibujar()
                    if juego.escena is not nivel:
                        break


if __name__ == "__main__":
    unittest.main()
