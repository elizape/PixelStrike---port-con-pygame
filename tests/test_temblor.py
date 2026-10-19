"""Tests del screen shake (sin ventana ni audio)."""
import os
import random
import sys
import unittest
import unittest.mock as mock
from pathlib import Path

os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
os.environ.setdefault("SDL_AUDIODRIVER", "dummy")
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import pygame  # noqa: E402

from pixelstrike import datos as d  # noqa: E402
from pixelstrike.entidades import BalaEnemigo, Enemigo  # noqa: E402
from pixelstrike.escena_nivel import PAUSA, EscenaNivel  # noqa: E402
from pixelstrike.juego import Juego  # noqa: E402
from pixelstrike.temblor import INTENSIDAD_MAX, INTENSIDAD_MIN, Temblor  # noqa: E402


class TemblorTest(unittest.TestCase):
    def test_inactivo_no_desplaza(self):
        t = Temblor()
        t.actualizar(0.016)
        self.assertFalse(t.activo)
        self.assertEqual(t.desplazamiento, (0, 0))

    def test_mas_dano_sacude_mas_fuerte_y_mas_tiempo(self):
        debil, fuerte = Temblor(), Temblor()
        debil.sacudir(5)
        fuerte.sacudir(20)
        self.assertLess(debil.intensidad, fuerte.intensidad)
        self.assertLess(debil.duracion, fuerte.duracion)

    def test_la_intensidad_tiene_piso_y_techo(self):
        t = Temblor()
        t.sacudir(0.1)
        self.assertEqual(t.intensidad, INTENSIDAD_MIN)
        t = Temblor()
        t.sacudir(10_000)
        self.assertEqual(t.intensidad, INTENSIDAD_MAX)

    def test_el_desplazamiento_no_supera_la_intensidad_y_se_apaga(self):
        random.seed(2)
        t = Temblor()
        t.sacudir(20)
        for _ in range(200):
            t.actualizar(0.016)
            self.assertLessEqual(max(abs(t.desplazamiento[0]), abs(t.desplazamiento[1])), t.intensidad)
            if not t.activo:
                break
        self.assertFalse(t.activo)
        t.actualizar(0.016)
        self.assertEqual(t.desplazamiento, (0, 0))

    def test_un_golpe_debil_no_pisa_a_uno_fuerte_en_curso(self):
        t = Temblor()
        t.sacudir(30)
        fuerte = t.intensidad
        t.sacudir(2)
        self.assertEqual(t.intensidad, fuerte)

    def test_dt_cero_no_rompe(self):
        t = Temblor()
        t.sacudir(10)
        t.actualizar(0)
        self.assertTrue(t.activo)


class TemblorEnElNivelTest(unittest.TestCase):
    def nivel(self):
        escena = EscenaNivel(Juego(), "nivel1")
        escena.estado = 1                          # JUGANDO
        return escena

    def test_una_bala_enemiga_que_impacta_sacude_segun_su_dano(self):
        for danio in (5, 25):
            with self.subTest(danio=danio):
                escena = self.nivel()
                escena.jugador.x, escena.jugador.y = 10, 5
                bala = BalaEnemigo(10, 5, d.FUSIL_ALIEN.imagen_bala, danio)
                self.assertTrue(bala._impacta(escena))
                esperada = Temblor()
                esperada.sacudir(danio)
                self.assertEqual(escena.temblor.intensidad, esperada.intensidad)

    def test_el_defensa_reduce_el_temblor_igual_que_el_dano(self):
        escena = self.nivel()
        escena.jugador.defensa = 0.5
        escena.jugador.x, escena.jugador.y = 10, 5
        BalaEnemigo(10, 5, d.FUSIL_ALIEN.imagen_bala, 20)._impacta(escena)
        esperada = Temblor()
        esperada.sacudir(10)
        self.assertEqual(escena.temblor.intensidad, esperada.intensidad)

    def test_una_bala_que_no_impacta_no_sacude(self):
        escena = self.nivel()
        escena.jugador.x, escena.jugador.y = 10, 5
        self.assertFalse(BalaEnemigo(3, 1, d.FUSIL_ALIEN.imagen_bala, 20)._impacta(escena))
        self.assertFalse(escena.temblor.activo)

    def test_un_enemigo_que_escapa_sacude_segun_el_dano_de_escape(self):
        for dificultad in (d.FACIL, d.DIFICIL):
            with self.subTest(dificultad=dificultad.clave):
                escena = self.nivel()
                escena.dificultad = dificultad
                enemigo = Enemigo(d.CRAWLER)
                escena.enemigos.append(enemigo)
                escena.enemigo_escapo(enemigo)
                esperada = Temblor()
                esperada.sacudir(dificultad.danio_escape)
                self.assertEqual(escena.temblor.intensidad, esperada.intensidad)

    def test_la_pausa_lo_congela_y_dibuja_sin_desplazar(self):
        escena = self.nivel()
        escena.sacudir(20)
        escena.estado = PAUSA
        antes = escena.temblor.restante
        escena.actualizar(0.1)
        self.assertEqual(escena.temblor.restante, antes)
        with mock.patch.object(escena, "_dibujar_juego") as juego, \
                mock.patch.object(escena, "_dibujar_interfaz"):
            lienzo = pygame.Surface((1600, 900))
            escena.dibujar(lienzo)
            juego.assert_called_once_with(lienzo)          # directo al lienzo: sin desplazamiento

    def test_solo_se_sacude_el_juego_y_no_la_interfaz(self):
        escena = self.nivel()
        escena.sacudir(30)
        escena.temblor.desplazamiento = (12, 7)
        rojo, verde = (255, 0, 0), (0, 255, 0)

        def juego(superficie):
            superficie.fill((10, 20, 30))
            pygame.draw.rect(superficie, rojo, (100, 100, 20, 20))

        def interfaz(superficie):
            pygame.draw.rect(superficie, verde, (300, 300, 20, 20))

        with mock.patch.object(escena, "_dibujar_juego", side_effect=juego), \
                mock.patch.object(escena, "_dibujar_interfaz", side_effect=interfaz):
            lienzo = pygame.Surface((1600, 900))
            escena.dibujar(lienzo)
        self.assertEqual(tuple(lienzo.get_at((112, 107)))[:3], rojo)       # el juego se movió (12, 7)
        self.assertEqual(tuple(lienzo.get_at((0, 0)))[:3], (10, 20, 30))   # sin franja negra en el borde
        self.assertEqual(tuple(lienzo.get_at((300, 300)))[:3], verde)      # la interfaz, en su lugar

    def test_el_nivel_completo_se_dibuja_temblando(self):
        escena = self.nivel()
        escena.sacudir(20)
        for _ in range(30):
            escena.actualizar(0.016)
            escena.dibujar(pygame.Surface((1600, 900)))
        self.assertFalse(escena.temblor.activo)


if __name__ == "__main__":
    unittest.main()
