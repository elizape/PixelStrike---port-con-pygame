"""Escena de juego: tutorial, niveles de hordas y nivel del jefe final."""
import random

import pygame

from . import ajustes as aj
from . import datos as d
from .entidades import BalaJugador, Enemigo, ItemPowerUp, Jugador
from .entrada import TeclasRepetibles
from .escena import Escena
from .interfaz import dibujar_barra_powerups, dibujar_barra_vida
from .jefe import JefeFinal
from .particulas import SistemaParticulas
from .recursos import recursos
from .temblor import Temblor
from .temporizador import Planificador

# Estados del nivel
CARGANDO, JUGANDO, PAUSA, VICTORIA, DERROTA = range(5)

# Partículas de muerte
CANTIDAD_ENEMIGO, CANTIDAD_JUGADOR, CANTIDAD_JEFE = 18, 32, 40


class EscenaNivel(Escena):
    def __init__(self, juego, clave):
        super().__init__(juego)
        self.datos = d.NIVELES[clave]
        self.personaje = d.PERSONAJES[juego.progreso.personaje]
        # El tutorial siempre se juega en Normal, para que las instrucciones no cambien.
        self.dificultad = (d.NORMAL if self.datos.tipo == "tutorial"
                           else juego.progreso.dificultad_actual())
        self.jugador = Jugador(self.personaje)
        self.sim = Planificador()      # solo corre mientras se juega: se congela en la pausa
        self.enemigos = []
        self.balas = []
        self.items = []
        self.particulas = SistemaParticulas()
        self.temblor = Temblor()
        self._mundo = None             # superficie donde se dibuja el juego mientras tiembla
        self.jefe = JefeFinal(self, self.dificultad) if self.datos.tipo == "jefe" else None
        self.estado = CARGANDO
        self.paso_tutorial = 0
        self._aviso_pausa_visible = False
        self.xp_nivel = 0
        self.racha_actual = 0
        self.disparos_recibidos = 0
        self.bono_perfecto_otorgado = False
        self._notificaciones_xp = []
        self.teclas = TeclasRepetibles({
            aj.TECLA_ARRIBA: lambda: self._mover(0, 1),
            aj.TECLA_ABAJO: lambda: self._mover(0, -1),
            aj.TECLA_IZQUIERDA: lambda: self._mover(-1, 0),
            aj.TECLA_DERECHA: lambda: self._mover(1, 0),
        }, repetir=aj.MANTENER_PARA_MOVER)

    # ========================================================================
    # Ciclo de vida
    # ========================================================================
    def al_entrar(self):
        recursos.musica(self.datos.musica, aj.VOLUMEN_MUSICA)
        self.ui.despues(0.1, self._comenzar)
        if self.datos.tipo == "tutorial":
            self.mostrar(d.TUTO_MOVER)
            self.mostrar(d.TUTO_ENTER)
        elif self.datos.tipo == "jefe":
            self.sim.correr(self._guion_jefe())
        else:
            self.sim.correr(self._guion_horda())

    def _comenzar(self):
        self.estado = JUGANDO

    # ========================================================================
    # Entrada
    # ========================================================================
    def manejar_evento(self, evento):
        if evento.type != pygame.KEYDOWN:
            return
        tecla = evento.key
        if self.teclas.tecla_abajo(tecla):
            return
        if tecla == aj.TECLA_DISPARO:
            self._disparar()
        elif tecla == aj.TECLA_PAUSA:
            self._alternar_pausa()
        elif tecla in aj.TECLAS_ENTER:
            self._avanzar_tutorial()
        elif tecla in (aj.TECLA_REINICIAR, aj.TECLA_SELECTOR) and self.estado in (PAUSA, DERROTA):
            if tecla == aj.TECLA_REINICIAR:
                self.juego.ir_a_nivel(self.datos.clave)
            else:
                recursos.detener_musica()
                self.juego.ir_a_selector_niveles()

    def _mover(self, dx, dy):
        if self.estado == JUGANDO:
            self.jugador.mover(dx, dy)

    def _disparar(self):
        if self.estado != JUGANDO:
            return
        bala = self.jugador.disparar()
        if bala:
            self.balas.append(bala)

    def _alternar_pausa(self):
        if self.estado == JUGANDO:
            if self.jugador.hay_powerup_activo:
                # Igual que en el original: con un power up activo no se puede pausar
                if not self._aviso_pausa_visible:
                    self._aviso_pausa_visible = True
                    self.mostrar(d.NO_PUEDES_PAUSAR)
                    self.ui.despues(3.5, self._ocultar_aviso_pausa)
            else:
                self.estado = PAUSA
                self.mostrar(d.MENU_PAUSA)
        elif self.estado == PAUSA:
            self.estado = JUGANDO
            self.ocultar(d.MENU_PAUSA)

    def _ocultar_aviso_pausa(self):
        self._aviso_pausa_visible = False
        self.ocultar(d.NO_PUEDES_PAUSAR)

    # ========================================================================
    # Actualización
    # ========================================================================
    def actualizar(self, dt):
        super().actualizar(dt)
        for notif in list(self._notificaciones_xp):
            notif["tiempo"] -= dt
            if notif["tiempo"] <= 0:
                self._notificaciones_xp.remove(notif)
        if self.estado != PAUSA:                 # siguen animándose en victoria/derrota
            self.particulas.actualizar(dt)
            self.temblor.actualizar(dt)          # en pausa se congela
        self.teclas.actualizar(dt)
        if self.estado != JUGANDO:
            return
        if aj.MANTENER_PARA_DISPARAR and pygame.key.get_pressed()[aj.TECLA_DISPARO]:
            self._disparar()

        self.sim.actualizar(dt)
        if self.estado != JUGANDO:       # un guion pudo terminar el nivel
            return

        self.jugador.actualizar(dt)
        for enemigo in list(self.enemigos):
            enemigo.actualizar(dt, self)
        for bala in list(self.balas):
            bala.actualizar(dt, self)
        for item in list(self.items):
            item.actualizar(dt, self)
        if self.jefe:
            self.jefe.actualizar(dt, self)

        self.enemigos = [e for e in self.enemigos if e.activo]
        self.balas = [b for b in self.balas if b.activa]
        self.items = [i for i in self.items if i.activo]

        if self.estado == JUGANDO and not self.jugador.vivo:
            self._derrota()

    # ========================================================================
    # API que usan las entidades
    # ========================================================================
    def blanco_en(self, x, y):
        """Enemigo (o jefe) que ocupa la celda, o None. Lo usan las balas del jugador."""
        for enemigo in self.enemigos:
            if enemigo.activo and (enemigo.x, enemigo.y) == (x, y):
                return enemigo
        jefe = self.jefe
        if jefe and jefe.vivo and jefe.atacable and (jefe.x, jefe.y) == (x, y):
            return jefe
        return None

    def _notificar_xp(self, texto, color=(255, 217, 59)):
        self._notificaciones_xp.append({"texto": texto, "color": color, "tiempo": 2.2})
        if len(self._notificaciones_xp) > 4:
            self._notificaciones_xp.pop(0)

    def disparo_recibido(self):
        self.disparos_recibidos += 1
        self.racha_actual = 0
        self.xp_nivel = max(0, self.xp_nivel - d.XP_PENALIZACION_DISPARO)
        self._notificar_xp(f"-{d.XP_PENALIZACION_DISPARO} XP (Disparo recibido)", color=(255, 90, 90))

    def enemigo_muerto(self, enemigo):
        self.particulas.emitir_en_celda(enemigo.x, enemigo.y + enemigo.tipo.altura_muerte,
                                        enemigo.tipo.color_muerte, CANTIDAD_ENEMIGO)
        if enemigo.powerup:
            self.items.append(ItemPowerUp(enemigo.powerup, enemigo.x, enemigo.y))

        self.racha_actual += 1
        if enemigo.tipo == d.ALIEN_RAPTOR:
            puntos = d.XP_ALIEN
            nombre_enemigo = "Alien"
        elif enemigo.tipo == d.CRAWLER:
            puntos = d.XP_CRAWLER
            nombre_enemigo = "Crawler"
        else:
            puntos = d.XP_ALIEN
            nombre_enemigo = "Enemigo"

        self.xp_nivel += puntos
        self._notificar_xp(f"+{puntos} XP ({nombre_enemigo})")

        # Bonificaciones por racha sin recibir disparos
        if self.racha_actual % 7 == 3:
            self.xp_nivel += d.XP_RACHA_3
            self._notificar_xp(f"¡Racha de 3! +{d.XP_RACHA_3} XP", color=(255, 217, 59))
        elif self.racha_actual % 7 == 0 and self.racha_actual > 0:
            self.xp_nivel += d.XP_RACHA_7
            self._notificar_xp(f"¡Racha de 7! +{d.XP_RACHA_7} XP", color=(255, 217, 59))

    def sacudir(self, danio):
        """Hace temblar el juego (no la interfaz) según el daño que se acaba de recibir."""
        self.temblor.sacudir(danio)

    def enemigo_escapo(self, enemigo):
        enemigo.activo = False
        self.sacudir(self.dificultad.danio_escape * self.jugador.defensa)
        self.jugador.recibir_danio(self.dificultad.danio_escape)

    def jefe_derrotado(self):
        self.xp_nivel += d.XP_JEFE
        self._notificar_xp(f"¡Kratos derrotado! +{d.XP_JEFE} XP", color=(255, 217, 59))
        # Una explosión grande en varias tandas sobre el cuerpo de Kratos
        for i in range(4):
            self.ui.despues(0.12 * i, lambda: self.particulas.emitir_en_celda(
                self.jefe.x + 0.5, self.jefe.y + d.JEFE_ALTURA_MUERTE, d.KRATOS.color_muerte, CANTIDAD_JEFE, dispersion=70))
        self.ui.despues(0.05, self._victoria)

    # ========================================================================
    # Guiones (secuencias del nivel)
    # ========================================================================
    def _guion_horda(self):
        datos = self.datos
        yield 0.5
        recursos.reproducir(d.SFX_NIVEL_NUEVO)
        self.mostrar(datos.banner)
        yield 3.0
        self.ocultar(datos.banner)

        yield from self._oleada(con_powerup=True)
        while self.enemigos:
            yield 0.25

        recursos.reproducir(d.SFX_ATENCION)
        self.mostrar_por(d.MAS_ENEMIGOS, 4.0, self.sim)
        yield from self._oleada(con_powerup=False)
        while self.enemigos:
            yield 0.25
        self._victoria()

    def _oleada(self, con_powerup):
        """Va soltando los enemigos de a uno, en orden aleatorio."""
        datos = self.datos
        dificultad = self.dificultad
        cola = ([Enemigo(d.ALIEN_RAPTOR, dificultad) for _ in range(datos.aliens)]
                + [Enemigo(d.CRAWLER, dificultad) for _ in range(datos.crawlers)]
                + [Enemigo(d.ZYRAK, dificultad) for _ in range(datos.zyraks)])
        random.shuffle(cola)
        if con_powerup and datos.powerup and datos.enemigo_con_powerup <= len(cola):
            cola[datos.enemigo_con_powerup - 1].powerup = datos.powerup
        yield 0.5
        intervalo = random.randint(datos.spawn_min, datos.spawn_max) * dificultad.mult_spawn
        for enemigo in cola:
            yield intervalo
            self.enemigos.append(enemigo)

    def _guion_jefe(self):
        self.secuencia(d.INTRO_JEFE, self.sim, con_sonido=True)
        yield 21.0
        self.jefe.comenzar_ataques()

    # --- tutorial -----------------------------------------------------------
    def _avanzar_tutorial(self):
        if self.datos.tipo != "tutorial" or self.estado != JUGANDO:
            return
        pasos = d.PASOS_TUTORIAL
        if self.paso_tutorial < len(pasos) - 1:
            self.ocultar(pasos[self.paso_tutorial])
            self.paso_tutorial += 1
            self.mostrar(pasos[self.paso_tutorial])
        elif self.paso_tutorial == len(pasos) - 1:
            self.ocultar(pasos[self.paso_tutorial])
            self.ocultar(d.TUTO_ENTER)
            self.paso_tutorial += 1
            self.sim.correr(self._tutorial_interactivo())

    def _tutorial_interactivo(self):
        self.mostrar(d.TUTO_INTERACTIVO_1)
        etapas = ((d.ALIEN_RAPTOR, d.TUTO_INTERACTIVO_1, d.TUTO_INTERACTIVO_2),
                  (d.CRAWLER, d.TUTO_INTERACTIVO_2, None))
        for tipo, actual, siguiente in etapas:
            yield 2.5
            self.enemigos.append(Enemigo(tipo, self.dificultad))
            while self.enemigos:
                yield 0.25
            recursos.reproducir(d.SFX_NIVEL_NUEVO)
            self.ocultar(actual)
            if siguiente:
                self.mostrar(siguiente)
        self.mostrar(d.TUTO_FIN)
        self.juego.progreso.desbloquear_nivel(self.datos.siguiente)
        self._finalizar_puntaje()
        yield 5.0
        self._continuar()

    # ========================================================================
    # Fin del nivel
    # ========================================================================
    def _finalizar_puntaje(self):
        if self.bono_perfecto_otorgado:
            return
        self.bono_perfecto_otorgado = True
        if self.disparos_recibidos == 0:
            self.xp_nivel += d.XP_NIVEL_PERFECTO
            self._notificar_xp(f"¡Nivel Perfecto! +{d.XP_NIVEL_PERFECTO} XP", color=(255, 217, 59))
        self.juego.progreso.registrar_puntaje_nivel(self.datos.clave, self.xp_nivel)

    def _victoria(self):
        self.estado = VICTORIA
        self.juego.progreso.desbloquear_nivel(self.datos.siguiente)
        if self.juego.progreso.desbloquear_personaje(self.datos.personaje):
            self.ui.despues(2.0, self._avisar_personaje_desbloqueado)
        self._finalizar_puntaje()
        recursos.reproducir(d.SFX_VICTORIA_1)
        recursos.reproducir(d.SFX_VICTORIA_2)
        self.mostrar(d.HAS_GANADO)
        self.ui.despues(2.0, lambda: self.mostrar(d.REINICIAR))
        self.ui.despues(4.65, lambda: recursos.reproducir(d.SFX_VICTORIA_3))
        self.ui.despues(5.0, self._continuar)

    def _avisar_personaje_desbloqueado(self):
        self.mostrar(d.PERSONAJE_DESBLOQUEADO)
        recursos.reproducir(d.SFX_POWERUP)

    def _derrota(self):
        self.estado = DERROTA
        self.particulas.emitir_en_celda(self.jugador.x, self.jugador.y + self.personaje.altura_muerte,
                                        self.personaje.color_muerte, CANTIDAD_JUGADOR, dispersion=15)
        self.ui.despues(0.04, self._mostrar_derrota)
        self.ui.despues(2.0, lambda: recursos.reproducir(d.SFX_DERROTA_2))
        self.ui.despues(4.0, lambda: self.mostrar(d.REINICIAR))

    def _mostrar_derrota(self):
        self.mostrar(d.HAS_MUERTO)
        recursos.reproducir(d.SFX_DERROTA_1)

    def _continuar(self):
        recursos.detener_musica()
        if self.datos.siguiente:
            self.juego.ir_a_nivel(self.datos.siguiente)
        else:
            self.juego.ir_a_creditos()

    # ========================================================================
    # Dibujo (de atrás hacia adelante)
    # ========================================================================
    def dibujar(self, lienzo):
        if not self.temblor.activo or self.estado == PAUSA:     # en pausa no se ve desplazado
            self._dibujar_juego(lienzo)
        else:
            # El juego se dibuja aparte y se copia desplazado; la interfaz va después, quieta.
            if self._mundo is None:
                self._mundo = pygame.Surface((aj.ANCHO, aj.ALTO))
            self._dibujar_juego(self._mundo)
            lienzo.blit(self._mundo, (0, 0))              # cubre los bordes que deja el desplazamiento
            lienzo.blit(self._mundo, self.temblor.desplazamiento)
        self._dibujar_interfaz(lienzo)

    def _dibujar_juego(self, lienzo):
        recursos.dibujar_fondo(lienzo, self.datos.fondo)
        recursos.dibujar(lienzo, d.MARCA_CAMINO, 0, self.jugador.y)
        if self.jefe:
            self.jefe.dibujar_suelo(lienzo)
        for item in self.items:
            item.dibujar(lienzo)
        for enemigo in self.enemigos:
            enemigo.dibujar(lienzo)
        if self.jefe:
            self.jefe.dibujar(lienzo)
        self.jugador.dibujar(lienzo)
        for bala in self.balas:
            bala.dibujar(lienzo)
        self.particulas.dibujar(lienzo)
        if self.jefe:
            self.jefe.dibujar_aire(lienzo)

    def _dibujar_interfaz(self, lienzo):
        if self.jefe:
            self.jefe.dibujar_barra_vida(lienzo)
        dibujar_barra_vida(lienzo, self.jugador.vida, self.jugador.vida_max, 0, 17, d.CORAZON_ROJO)
        dibujar_barra_powerups(lienzo, self.jugador)

        # Marcador de XP y racha del nivel actual
        recursos.texto(lienzo, f"XP: {self.xp_nivel}", 28, (255, 217, 59), aj.ANCHO // 2, 14)
        if self.racha_actual >= 2:
            recursos.texto(lienzo, f"Racha: {self.racha_actual}x", 20, (255, 255, 120), aj.ANCHO // 2, 44)

        # Notificaciones emergentes de XP (+25 XP, -15 XP, Racha, etc.)
        y_notif = 68
        for notif in self._notificaciones_xp[-3:]:
            recursos.texto(lienzo, notif["texto"], 20, notif["color"], aj.ANCHO // 2, y_notif)
            y_notif += 24

        # En pantalla de victoria, resumen de XP del nivel
        if self.estado == VICTORIA:
            recursos.texto(lienzo, f"XP NIVEL: {self.xp_nivel}", 38, (255, 217, 59), aj.ANCHO // 2, 450)
            if self.disparos_recibidos == 0:
                recursos.texto(lienzo, f"¡Nivel Perfecto! (+{d.XP_NIVEL_PERFECTO} XP)", 26, (255, 255, 255), aj.ANCHO // 2, 500)

        self.dibujar_indicadores(lienzo)
