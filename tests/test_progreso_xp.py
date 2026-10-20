"""Tests para el sistema de puntuación, XP, niveles, guardado y eliminación de progreso."""
import json
import os
import shutil
import sys
import tempfile
import unittest
from pathlib import Path

os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
os.environ.setdefault("SDL_AUDIODRIVER", "dummy")
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import pygame  # noqa: E402

from pixelstrike import ajustes as aj  # noqa: E402
from pixelstrike import datos as d  # noqa: E402
from pixelstrike.entidades import BalaEnemigo, Enemigo, Jugador  # noqa: E402
from pixelstrike.escena_nivel import EscenaNivel, VICTORIA  # noqa: E402
from pixelstrike.escenas_menu import SelectorNiveles  # noqa: E402
from pixelstrike.juego import Juego  # noqa: E402
from pixelstrike.progreso import Progreso, calcular_nivel_xp  # noqa: E402


class CalculoNivelXPTest(unittest.TestCase):
    def test_nivel_1_recluta(self):
        info_cero = calcular_nivel_xp(0)
        self.assertEqual(info_cero["nivel"], 1)
        self.assertEqual(info_cero["titulo"], "Recluta")
        self.assertEqual(info_cero["xp_en_nivel"], 0)
        self.assertEqual(info_cero["xp_para_subir"], 150)
        self.assertEqual(info_cero["porcentaje"], 0.0)

        info_cien = calcular_nivel_xp(100)
        self.assertEqual(info_cien["nivel"], 1)
        self.assertEqual(info_cien["xp_en_nivel"], 100)
        self.assertAlmostEqual(info_cien["porcentaje"], 100 / 150)

    def test_niveles_progresivos(self):
        # Nivel 2: 150 a 399
        info2 = calcular_nivel_xp(150)
        self.assertEqual(info2["nivel"], 2)
        self.assertEqual(info2["titulo"], "Cadete")
        self.assertEqual(info2["xp_en_nivel"], 0)
        self.assertEqual(info2["xp_para_subir"], 250)

        # Nivel 3: 400 a 799
        info3 = calcular_nivel_xp(400)
        self.assertEqual(info3["nivel"], 3)
        self.assertEqual(info3["titulo"], "Soldado")
        self.assertEqual(info3["xp_en_nivel"], 0)
        self.assertEqual(info3["xp_para_subir"], 400)

        # Nivel 4: 800 a 1399
        info4 = calcular_nivel_xp(800)
        self.assertEqual(info4["nivel"], 4)
        self.assertEqual(info4["titulo"], "Veterano")

        # Nivel 5: 1400 a 2199
        info5 = calcular_nivel_xp(1400)
        self.assertEqual(info5["nivel"], 5)
        self.assertEqual(info5["titulo"], "Comandante")

        # Nivel 6: 2200 a 3199
        info6 = calcular_nivel_xp(2200)
        self.assertEqual(info6["nivel"], 6)
        self.assertEqual(info6["titulo"], "Élite")

        # Nivel 7: 3200 a 4199
        info7 = calcular_nivel_xp(3200)
        self.assertEqual(info7["nivel"], 7)
        self.assertEqual(info7["titulo"], "Maestro")
        self.assertEqual(info7["xp_para_subir"], 1000)

    def test_niveles_adicionales_leyenda(self):
        # Nivel 8: 4200+
        info8 = calcular_nivel_xp(4200)
        self.assertEqual(info8["nivel"], 8)
        self.assertEqual(info8["titulo"], "Leyenda")
        self.assertEqual(info8["xp_en_nivel"], 0)
        self.assertEqual(info8["xp_para_subir"], 1000)

        # Nivel 9: 5200+
        info9 = calcular_nivel_xp(5500)
        self.assertEqual(info9["nivel"], 9)
        self.assertEqual(info9["titulo"], "Leyenda")
        self.assertEqual(info9["xp_en_nivel"], 300)
        self.assertAlmostEqual(info9["porcentaje"], 0.3)


class PuntuacionNivelTest(unittest.TestCase):
    def setUp(self):
        self.juego = Juego()
        self.escena = EscenaNivel(self.juego, "nivel1")

    def test_matar_alien_suma_25_xp(self):
        enemigo = Enemigo(d.ALIEN_RAPTOR)
        self.escena.enemigo_muerto(enemigo)
        self.assertEqual(self.escena.xp_nivel, 25)

    def test_matar_crawler_suma_40_xp(self):
        enemigo = Enemigo(d.CRAWLER)
        self.escena.enemigo_muerto(enemigo)
        self.assertEqual(self.escena.xp_nivel, 40)

    def test_disparo_recibido_resta_15_xp(self):
        # Con XP suficiente
        self.escena.xp_nivel = 50
        self.escena.disparo_recibido()
        self.assertEqual(self.escena.xp_nivel, 35)
        self.assertEqual(self.escena.disparos_recibidos, 1)

    def test_disparo_recibido_no_baja_de_cero(self):
        self.escena.xp_nivel = 10
        self.escena.disparo_recibido()
        self.assertEqual(self.escena.xp_nivel, 0)

    def test_racha_3_enemigos_suma_10_xp(self):
        # 3 aliens: 25 * 3 = 75 + bono racha 3 (10) = 85 XP
        for _ in range(3):
            self.escena.enemigo_muerto(Enemigo(d.ALIEN_RAPTOR))
        self.assertEqual(self.escena.xp_nivel, 85)
        self.assertEqual(self.escena.racha_actual, 3)

    def test_racha_7_enemigos_suma_30_xp_adicional(self):
        # 7 aliens: 25 * 7 = 175 + bono 3 (10) + bono 7 (30) = 215 XP
        for _ in range(7):
            self.escena.enemigo_muerto(Enemigo(d.ALIEN_RAPTOR))
        self.assertEqual(self.escena.xp_nivel, 215)
        self.assertEqual(self.escena.racha_actual, 7)

    def test_recibir_disparo_reinicia_la_racha(self):
        # Mata 2 enemigos
        self.escena.enemigo_muerto(Enemigo(d.ALIEN_RAPTOR))
        self.escena.enemigo_muerto(Enemigo(d.ALIEN_RAPTOR))
        self.assertEqual(self.escena.racha_actual, 2)

        # Recibe un disparo (pierde 15 XP y reinicia racha)
        self.escena.disparo_recibido()
        self.assertEqual(self.escena.racha_actual, 0)
        self.assertEqual(self.escena.xp_nivel, 35)  # 50 - 15 = 35

        # Mata 1 enemigo más: racha debe ser 1 (no llega a 3 todavía)
        self.escena.enemigo_muerto(Enemigo(d.ALIEN_RAPTOR))
        self.assertEqual(self.escena.racha_actual, 1)
        self.assertEqual(self.escena.xp_nivel, 60)  # 35 + 25 = 60 (sin bono de racha aún)

    def test_bala_enemiga_impacta_activa_disparo_recibido(self):
        self.escena.jugador.x, self.escena.jugador.y = 5, 2
        self.escena.xp_nivel = 50
        bala = BalaEnemigo(5, 2, d.FUSIL_ALIEN.imagen_bala, 10)
        self.assertTrue(bala._impacta(self.escena))
        self.assertEqual(self.escena.disparos_recibidos, 1)
        self.assertEqual(self.escena.xp_nivel, 35)

    def test_finalizar_nivel_sin_disparos_recibidos_suma_100_xp(self):
        # Nivel ganado sin recibir disparos
        self.escena.xp_nivel = 100
        self.escena.disparos_recibidos = 0
        self.escena._victoria()
        self.assertEqual(self.escena.xp_nivel, 200)  # 100 + 100 bono
        self.assertEqual(self.juego.progreso.puntaje_nivel("nivel1"), 200)
        self.assertEqual(self.juego.progreso.xp_total, 200)

    def test_finalizar_nivel_con_disparos_recibidos_no_suma_bono(self):
        self.escena.xp_nivel = 100
        self.escena.disparos_recibidos = 2
        self.escena._victoria()
        self.assertEqual(self.escena.xp_nivel, 100)  # sin los 100 de bono
        self.assertEqual(self.juego.progreso.puntaje_nivel("nivel1"), 100)


class GuardadoProgresoTest(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.mkdtemp()
        self.archivo_guardado = Path(self.temp_dir) / "progreso_test.json"

    def tearDown(self):
        shutil.rmtree(self.temp_dir)

    def test_guardar_y_cargar_progreso(self):
        prog = Progreso(ruta_guardado=self.archivo_guardado, auto_cargar=False)
        prog.desbloquear_nivel("nivel1")
        prog.desbloquear_nivel("nivel2")
        prog.desbloquear_personaje("jade")
        prog.personaje = "jade"
        prog.dificultad = "dificil"
        prog.registrar_puntaje_nivel("nivel1", 350)

        self.assertTrue(self.archivo_guardado.is_file())

        # Cargar en una nueva instancia
        prog2 = Progreso(ruta_guardado=self.archivo_guardado, auto_cargar=True)
        self.assertTrue(prog2.nivel_desbloqueado("nivel1"))
        self.assertTrue(prog2.nivel_desbloqueado("nivel2"))
        self.assertTrue(prog2.personaje_desbloqueado("jade"))
        self.assertEqual(prog2.personaje, "jade")
        self.assertEqual(prog2.dificultad, "dificil")
        self.assertEqual(prog2.xp_total, 350)
        self.assertEqual(prog2.puntaje_nivel("nivel1"), 350)
        self.assertEqual(prog2.nivel_xp, 2)  # 350 XP -> Nivel 2

    def test_borrar_progreso_reinicia_y_elimina_archivo(self):
        prog = Progreso(ruta_guardado=self.archivo_guardado, auto_cargar=False)
        prog.desbloquear_nivel("nivel2")
        prog.registrar_puntaje_nivel("nivel1", 500)
        self.assertTrue(self.archivo_guardado.is_file())

        prog.borrar_progreso()
        self.assertFalse(self.archivo_guardado.is_file())
        self.assertEqual(prog.niveles, {"nivel0"})
        self.assertEqual(prog.personajes, {d.PERSONAJE_INICIAL})
        self.assertEqual(prog.personaje, d.PERSONAJE_INICIAL)
        self.assertEqual(prog.xp_total, 0)
        self.assertEqual(prog.puntajes, {})
        self.assertEqual(prog.nivel_xp, 1)


class SelectorNivelesUITest(unittest.TestCase):
    def setUp(self):
        self.juego = Juego()
        self.escena = SelectorNiveles(self.juego)

    def test_info_xp_disponible_en_progreso(self):
        self.juego.progreso.xp_total = 450
        info = self.juego.progreso.info_xp
        self.assertEqual(info["nivel"], 3)
        self.assertEqual(info["titulo"], "Soldado")

    def test_flujo_confirmacion_borrado_progreso(self):
        self.juego.progreso.desbloquear_nivel("nivel2")
        self.juego.progreso.xp_total = 1000

        # Al presionar tecla Supr / Delete entra en confirmación
        evento_supr = pygame.event.Event(pygame.KEYDOWN, key=pygame.K_DELETE)
        self.escena.manejar_evento(evento_supr)
        self.assertTrue(self.escena.confirmando_borrado)

        # Si presiona Escape, se cancela sin borrar
        evento_esc = pygame.event.Event(pygame.KEYDOWN, key=pygame.K_ESCAPE)
        self.escena.manejar_evento(evento_esc)
        self.assertFalse(self.escena.confirmando_borrado)
        self.assertEqual(self.juego.progreso.xp_total, 1000)

        # Si presiona Supr y luego Enter, se borra el progreso
        self.escena.manejar_evento(evento_supr)
        self.assertTrue(self.escena.confirmando_borrado)
        evento_enter = pygame.event.Event(pygame.KEYDOWN, key=pygame.K_RETURN)
        self.escena.manejar_evento(evento_enter)
        self.assertFalse(self.escena.confirmando_borrado)
        self.assertEqual(self.juego.progreso.xp_total, 0)
        self.assertEqual(self.juego.progreso.nivel_xp, 1)
