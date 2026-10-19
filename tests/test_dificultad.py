"""Tests del selector de dificultad. Se ejecutan sin ventana ni audio:

    python -m unittest discover -s tests -v
"""
import math
import os
import random
import shutil
import sys
import tempfile
import unittest
import unittest.mock as mock
from pathlib import Path

os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
os.environ.setdefault("SDL_AUDIODRIVER", "dummy")
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import pygame  # noqa: E402

from pixelstrike import ajustes as aj  # noqa: E402
from pixelstrike import datos as d  # noqa: E402
from pixelstrike.entidades import Enemigo, Jugador  # noqa: E402
from pixelstrike.escena_nivel import EscenaNivel  # noqa: E402
from pixelstrike.escenas_menu import (  # noqa: E402
    DORADO, MARGEN_TRIANGULOS, TITULO_MAX, VELOCIDAD_TRIANGULOS, SelectorDificultad, SelectorNiveles)
from pixelstrike.jefe import JefeFinal  # noqa: E402
from pixelstrike.juego import Juego  # noqa: E402
from pixelstrike.recursos import recursos  # noqa: E402


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


# El triángulo derecho se acerca 10 px más (ajuste óptico por la fuente), ver _marcar_opcion.
CORRECCION_DERECHA = 10


class AdornosSelectorTest(unittest.TestCase):
    """Título y triángulos opcionales. Se prueban con una carpeta de assets temporal."""

    def setUp(self):
        self.tmp = Path(tempfile.mkdtemp())
        self.addCleanup(shutil.rmtree, self.tmp, ignore_errors=True)
        parche = mock.patch.object(aj, "DIR_ASSETS", self.tmp)
        parche.start()
        self.addCleanup(parche.stop)
        imagenes, faltantes = dict(recursos._imagenes), set(recursos.faltantes)
        self.addCleanup(lambda: (recursos._imagenes.clear(), recursos._imagenes.update(imagenes),
                                 recursos.faltantes.clear(), recursos.faltantes.update(faltantes)))
        self.juego = Juego()
        self.lienzo = self.juego.lienzo

    def guardar_png(self, nombre, ancho, alto, dibujar=None):
        superficie = pygame.Surface((ancho, alto), pygame.SRCALPHA)
        if dibujar:
            dibujar(superficie)
        else:
            superficie.fill((200, 30, 30, 255))
        pygame.image.save(superficie, str(self.tmp / nombre))

    def triangulos(self, superficie):
        """Dos triángulos enfrentados, con espacio vacío alrededor y en el medio."""
        pygame.draw.polygon(superficie, (255, 210, 63), [(40, 5), (40, 85), (110, 45)])
        pygame.draw.polygon(superficie, (255, 210, 63), [(590, 5), (590, 85), (660, 45)][::-1])

    def dibujar_escena(self):
        self.juego.escena.dibujar(self.lienzo)
        return self.juego.escena

    @staticmethod
    def sin_empuje(escena):
        """Congela la animación en el instante en que los triángulos están en su posición base."""
        escena._tiempo = 1.5 * math.pi / VELOCIDAD_TRIANGULOS      # sin(...) = -1  ->  empuje = 0

    def test_sin_imagenes_se_usa_texto_y_recuadro(self):
        escena = self.dibujar_escena()
        self.assertIsNone(escena._titulo)
        self.assertIsNone(escena._triangulos)
        lienzo = pygame.Surface((1600, 900), pygame.SRCALPHA)
        texto = pygame.Rect(700, 400, 200, 60)
        escena._marcar_opcion(lienzo, texto)
        borde = (texto.centerx - 279, texto.centery)
        self.assertEqual(tuple(lienzo.get_at(borde))[:3], DORADO)

    def test_titulo_grande_se_reduce_conservando_la_proporcion(self):
        self.guardar_png(d.TITULO_JUEGO, 2000, 400)
        ancho, alto = self.dibujar_escena()._titulo.get_size()
        self.assertLessEqual(ancho, TITULO_MAX[0])
        self.assertLessEqual(alto, TITULO_MAX[1])
        self.assertAlmostEqual(ancho / alto, 5.0, delta=0.05)

    def test_titulo_chico_se_dibuja_a_su_tamano(self):
        self.guardar_png(d.TITULO_JUEGO, 600, 100)
        self.assertEqual(self.dibujar_escena()._titulo.get_size(), (600, 100))

    def test_los_triangulos_quedan_a_margen_fijo_del_texto(self):
        # El PNG tiene espacio vacío; aun así cada triángulo debe quedar a MARGEN del texto.
        self.guardar_png(d.TRIANGULOS_SELECTOR, 700, 90, self.triangulos)
        escena = self.dibujar_escena()
        self.sin_empuje(escena)
        izquierdo, derecho = escena._triangulos
        self.assertLess(izquierdo.get_width(), 100)       # recortado: ya no tiene los ~350 px de la mitad
        self.assertLess(derecho.get_width(), 100)

        lienzo = pygame.Surface((1600, 900), pygame.SRCALPHA)
        texto = pygame.Rect(700, 400, 200, 60)
        escena._marcar_opcion(lienzo, texto)
        izq = lienzo.subsurface((0, 0, texto.left, 900)).get_bounding_rect()
        der = lienzo.subsurface((texto.right, 0, 1600 - texto.right, 900)).get_bounding_rect()
        self.assertEqual(izq.right, texto.left - MARGEN_TRIANGULOS)
        self.assertEqual(der.left, MARGEN_TRIANGULOS - CORRECCION_DERECHA)

    def test_los_triangulos_son_simetricos_para_cada_dificultad(self):
        # Cada palabra tiene letras con distinto espacio lateral (F vs L, N vs L...):
        # la distancia se mide contra lo que se VE del texto, no contra su caja.
        self.guardar_png(d.TRIANGULOS_SELECTOR, 700, 90, self.triangulos)
        escena = self.dibujar_escena()
        self.sin_empuje(escena)
        for dificultad in d.ORDEN_DIFICULTADES:
            with self.subTest(dificultad=dificultad.nombre):
                solo_texto = pygame.Surface((1600, 900), pygame.SRCALPHA)
                visible = recursos.texto(solo_texto, dificultad.nombre.upper(), 52, DORADO, 800, 400,
                                         sombra=None)
                real = solo_texto.get_bounding_rect()
                self.assertEqual(visible.left, real.left)
                self.assertEqual(visible.right, real.right)
                con_marca = pygame.Surface((1600, 900), pygame.SRCALPHA)
                escena._marcar_opcion(con_marca, visible)
                izq = con_marca.subsurface((0, 0, visible.left, 900)).get_bounding_rect()
                der = con_marca.subsurface((visible.right, 0, 1600 - visible.right, 900)).get_bounding_rect()
                self.assertEqual(visible.left - izq.right, MARGEN_TRIANGULOS)
                self.assertEqual(der.left, MARGEN_TRIANGULOS - CORRECCION_DERECHA)
                self.assertEqual(izq.centery, der.centery)
                self.assertAlmostEqual(izq.centery, visible.centery, delta=1)

    def test_el_selector_completo_se_dibuja_con_las_imagenes(self):
        self.guardar_png(d.TITULO_JUEGO, 900, 160)
        self.guardar_png(d.TRIANGULOS_SELECTOR, 700, 90, self.triangulos)
        escena = self.dibujar_escena()
        self.assertIsNotNone(escena._titulo)
        self.assertIsNotNone(escena._triangulos)
        for _ in range(3):                                # y con cualquier opción elegida
            self.juego.escena.manejar_evento(tecla(aj.TECLA_ABAJO))
            self.dibujar_escena()


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
