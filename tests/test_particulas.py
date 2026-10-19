"""Tests de las partículas de muerte (sin ventana ni audio)."""
import dataclasses
import os
import random
import sys
import unittest
from pathlib import Path

os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
os.environ.setdefault("SDL_AUDIODRIVER", "dummy")
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import pygame  # noqa: E402

from pixelstrike import datos as d  # noqa: E402
from pixelstrike.entidades import Enemigo  # noqa: E402
from pixelstrike.escena_nivel import (  # noqa: E402
    CANTIDAD_ENEMIGO, CANTIDAD_JEFE, CANTIDAD_JUGADOR, EscenaNivel)
from pixelstrike.juego import Juego  # noqa: E402
from pixelstrike.particulas import SistemaParticulas  # noqa: E402


class SistemaParticulasTest(unittest.TestCase):
    def test_emite_la_cantidad_pedida_y_se_vacia_solo(self):
        sistema = SistemaParticulas()
        sistema.emitir(100, 100, (255, 0, 0), 25)
        self.assertEqual(len(sistema), 25)
        for _ in range(200):
            sistema.actualizar(0.016)
        self.assertEqual(len(sistema), 0)

    def test_dt_cero_no_rompe_ni_las_mueve(self):
        sistema = SistemaParticulas()
        sistema.emitir(100, 100, (255, 0, 0), 5)
        antes = [(p.x, p.y) for p in sistema.particulas]
        sistema.actualizar(0)
        self.assertEqual(antes, [(p.x, p.y) for p in sistema.particulas])

    def test_el_color_se_mantiene_cerca_del_pedido(self):
        random.seed(1)
        sistema = SistemaParticulas()
        sistema.emitir(0, 0, (20, 120, 50), 50)
        for p in sistema.particulas:
            self.assertGreater(p.color[1], p.color[0])        # sigue siendo "verde"
            self.assertGreater(p.color[1], p.color[2])

    def test_se_encogen_y_el_tamano_nunca_baja_de_1(self):
        sistema = SistemaParticulas()
        sistema.emitir(0, 0, (255, 255, 255), 10)
        p = sistema.particulas[0]
        grande = p.lado
        p.vida = p.vida_total * 0.1
        self.assertLessEqual(p.lado, grande)
        p.vida = 0.0001
        self.assertGreaterEqual(p.lado, 1)

    def test_emitir_en_celda_usa_el_centro_de_la_celda(self):
        sistema = SistemaParticulas()
        sistema.emitir_en_celda(3, 2, (1, 2, 3), 1)
        p = sistema.particulas[0]
        self.assertAlmostEqual(p.x, 3.5 * 50)
        self.assertAlmostEqual(p.y, 900 - 2.5 * 50)

    def test_dibuja_sin_salirse_del_lienzo(self):
        sistema = SistemaParticulas()
        sistema.emitir(-30, 2000, (255, 0, 0), 20, dispersion=100)     # fuera de pantalla
        sistema.dibujar(pygame.Surface((1600, 900)))


class ParticulasEnElNivelTest(unittest.TestCase):
    def nivel(self, personaje="byteHunter", clave="nivel1"):
        juego = Juego()
        juego.progreso.personaje = personaje
        escena = EscenaNivel(juego, clave)
        escena.estado = 1                          # JUGANDO
        return escena

    def test_colores_por_personaje(self):
        esperados = {d.BYTE_HUNTER: "azul", d.JADE: "verde claro", d.KRATOS: "rojo",
                     d.ALIEN_RAPTOR: "rosa", d.CRAWLER: "verde oscuro"}
        colores = {x.color_muerte for x in esperados}
        self.assertEqual(len(colores), 5)           # los cinco son distintos
        r, g, b = d.BYTE_HUNTER.color_muerte
        self.assertTrue(b > r and b > g)
        r, g, b = d.KRATOS.color_muerte
        self.assertTrue(r > 150 and g < 80 and b < 80)
        r, g, b = d.ALIEN_RAPTOR.color_muerte
        self.assertTrue(r > 200 and b > 120 and g < r)
        self.assertGreater(d.JADE.color_muerte[1], d.CRAWLER.color_muerte[1])   # claro vs oscuro

    def test_al_morir_un_enemigo_salen_particulas_de_su_color(self):
        escena = self.nivel()
        for tipo in (d.ALIEN_RAPTOR, d.CRAWLER):
            escena.particulas.particulas.clear()
            enemigo = Enemigo(tipo)
            enemigo.x, enemigo.y = 20, 5
            escena.enemigos.append(enemigo)
            enemigo.recibir_danio(10_000, escena)
            self.assertEqual(len(escena.particulas), CANTIDAD_ENEMIGO)

    def test_al_morir_el_jugador_salen_particulas_de_su_personaje(self):
        for personaje in d.ORDEN_PERSONAJES:
            with self.subTest(personaje=personaje.clave):
                escena = self.nivel(personaje.clave)
                escena.jugador.recibir_danio(10_000)
                escena.actualizar(0.016)
                self.assertEqual(len(escena.particulas), CANTIDAD_JUGADOR)

    def test_al_caer_kratos_hay_explosion_en_tandas(self):
        escena = self.nivel(clave="nivel4")
        escena.jefe.atacable = True
        escena.jefe.recibir_danio(10_000, escena)
        escena.jefe_derrotado()
        for _ in range(60):
            escena.actualizar(0.016)
            if len(escena.particulas) >= CANTIDAD_JEFE * 3:
                break
        self.assertGreaterEqual(len(escena.particulas), CANTIDAD_JEFE * 2)

    def test_altura_de_las_particulas_por_enemigo(self):
        escena = self.nivel()
        for altura in (0.0, 1.5):
            escena.particulas.particulas.clear()
            tipo = dataclasses.replace(d.ALIEN_RAPTOR, altura_muerte=altura)
            enemigo = Enemigo(tipo)
            enemigo.x, enemigo.y = 20, 5
            escena.enemigos.append(enemigo)
            enemigo.recibir_danio(10_000, escena)
            y_base = 900 - (5 + 0.5 + altura) * 50           # centro de emisión, en píxeles
            promedio = sum(p.y for p in escena.particulas.particulas) / len(escena.particulas)
            self.assertAlmostEqual(promedio, y_base, delta=1)

    def test_altura_de_las_particulas_del_jugador(self):
        personaje = dataclasses.replace(d.JADE, altura_muerte=2.0)
        juego = Juego()
        escena = EscenaNivel(juego, "nivel1")
        escena.personaje = personaje
        escena.estado = 1
        escena.jugador.recibir_danio(10_000)
        escena.actualizar(0)
        y_base = 900 - (escena.jugador.y + 0.5 + 2.0) * 50
        promedio = sum(p.y for p in escena.particulas.particulas) / len(escena.particulas)
        self.assertAlmostEqual(promedio, y_base, delta=20)       # dispersión de 15 px

    def test_la_pausa_las_congela_y_siguen_en_derrota(self):
        escena = self.nivel()
        escena.particulas.emitir(500, 500, (255, 0, 0), 10)
        escena.estado = 2                          # PAUSA
        antes = [p.vida for p in escena.particulas.particulas]
        escena.actualizar(0.1)
        self.assertEqual(antes, [p.vida for p in escena.particulas.particulas])
        escena.estado = 4                          # DERROTA
        escena.actualizar(0.1)
        self.assertNotEqual(antes, [p.vida for p in escena.particulas.particulas])

    def test_el_nivel_se_dibuja_con_particulas(self):
        escena = self.nivel()
        escena.particulas.emitir_en_celda(10, 5, (255, 0, 0), 30)
        escena.dibujar(pygame.Surface((1600, 900)))


if __name__ == "__main__":
    unittest.main()
