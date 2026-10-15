"""Pantallas de menú: selector de dificultad, de niveles, de personajes y créditos."""
import pygame

from . import ajustes as aj
from . import datos as d
from .entrada import TeclasRepetibles
from .escena import Escena
from .recursos import recursos

DORADO = (255, 210, 63)
GRIS_CLARO = (205, 205, 205)
BLANCO = (255, 255, 255)

# Diseño del selector de dificultad (píxeles del lienzo de 1600x900)
TITULO_CENTRO_Y = 150          # centro vertical del título (imagen o texto)
TITULO_MAX = (1400, 230)       # si la imagen del título es más grande, se reduce a este tamaño
OPCION_Y0, OPCION_PASO = 370, 100
TAM_OPCION_ELEGIDA = 72
MARGEN_TRIANGULOS = 30         # separación entre cada triángulo y el texto de la opción


class SelectorDificultad(Escena):
    """Primera pantalla del juego: W/S (o A/D) para elegir, Enter para confirmar.

    Si existen `tituloPixelStrike.png` y `selectorTriangulos.png` en assets/ se usan;
    si no, se dibujan un título de texto y un recuadro dorado.
    """

    def __init__(self, juego):
        super().__init__(juego)
        claves = [x.clave for x in d.ORDEN_DIFICULTADES]
        self.indice = claves.index(juego.progreso.dificultad)
        self._velo = None
        self._adornos_listos = False
        self._titulo = None            # Surface del título, o None para usar texto
        self._triangulos = None        # (izquierdo, derecho), o None para usar el recuadro dorado

    def _preparar_adornos(self):
        """Carga (una sola vez) las imágenes opcionales del título y de los triángulos."""
        self._adornos_listos = True
        if recursos.existe(d.TITULO_JUEGO):
            titulo = recursos.imagen(d.TITULO_JUEGO)
            ancho_max, alto_max = TITULO_MAX
            if titulo.get_width() > ancho_max or titulo.get_height() > alto_max:
                escala = min(ancho_max / titulo.get_width(), alto_max / titulo.get_height())
                titulo = pygame.transform.scale(
                    titulo, (round(titulo.get_width() * escala), round(titulo.get_height() * escala)))
            self._titulo = titulo
        if recursos.existe(d.TRIANGULOS_SELECTOR):
            imagen = recursos.imagen(d.TRIANGULOS_SELECTOR)
            ancho, alto = imagen.get_size()
            # El PNG se parte por la mitad: cada triángulo se acomoda a un lado del texto,
            # sin importar cuánto mida la palabra. Cada mitad se recorta a lo que realmente
            # dibuja, así el margen con el texto es siempre MARGEN_TRIANGULOS aunque el PNG
            # tenga espacio vacío alrededor.
            self._triangulos = (self._recortar(imagen.subsurface((0, 0, ancho // 2, alto))),
                                self._recortar(imagen.subsurface((ancho // 2, 0, ancho - ancho // 2, alto))))

    @staticmethod
    def _recortar(superficie):
        """Quita el borde transparente (si la mitad está vacía, la deja como está)."""
        caja = superficie.get_bounding_rect()
        return superficie.subsurface(caja) if caja.width and caja.height else superficie

    def al_entrar(self):
        recursos.musica(d.MUSICA_SELECTOR_NIVELES, aj.VOLUMEN_MUSICA, continuar=True)

    def manejar_evento(self, evento):
        if evento.type != pygame.KEYDOWN:
            return
        tecla = evento.key
        if tecla in (aj.TECLA_ARRIBA, aj.TECLA_IZQUIERDA):
            self._mover(-1)
        elif tecla in (aj.TECLA_ABAJO, aj.TECLA_DERECHA):
            self._mover(1)
        elif tecla in aj.TECLAS_ENTER:
            self._confirmar()

    def _mover(self, paso):
        nuevo = self.indice + paso
        if 0 <= nuevo < len(d.ORDEN_DIFICULTADES):
            self.indice = nuevo
            recursos.reproducir(d.SFX_CLICK)

    def _marcar_opcion(self, lienzo, texto):
        """Marca la opción elegida: un triángulo a cada lado del texto, o un recuadro dorado."""
        centro_y = texto.top + round(TAM_OPCION_ELEGIDA * 0.43)     # centro visual de las mayúsculas
        if self._triangulos is None:
            caja = pygame.Rect(0, 0, 560, 84)
            caja.center = (texto.centerx, centro_y)
            pygame.draw.rect(lienzo, DORADO, caja, 4, border_radius=14)
            return
        izquierdo, derecho = self._triangulos
        lienzo.blit(izquierdo, (texto.left - MARGEN_TRIANGULOS - izquierdo.get_width(),
                                centro_y - izquierdo.get_height() // 2))
        lienzo.blit(derecho, (texto.right + MARGEN_TRIANGULOS, centro_y - derecho.get_height() // 2))

    def _confirmar(self):
        self.juego.progreso.dificultad = d.ORDEN_DIFICULTADES[self.indice].clave
        recursos.reproducir(d.SFX_CLICK)
        self.juego.ir_a_selector_niveles()

    def dibujar(self, lienzo):
        if not self._adornos_listos:
            self._preparar_adornos()
        recursos.dibujar_fondo(lienzo, d.FONDO_SELECTOR_DIFICULTAD)
        if self._velo is None:
            self._velo = pygame.Surface((aj.ANCHO, aj.ALTO), pygame.SRCALPHA)
            self._velo.fill((0, 0, 0, 150))
        lienzo.blit(self._velo, (0, 0))

        centro = aj.ANCHO // 2
        if self._titulo is not None:
            lienzo.blit(self._titulo, self._titulo.get_rect(center=(centro, TITULO_CENTRO_Y)))
        else:
            recursos.texto(lienzo, aj.TITULO.upper(), 150, DORADO, centro, 80)
        recursos.texto(lienzo, "Elegí la dificultad", 52, BLANCO, centro, 270)
        for i, dificultad in enumerate(d.ORDEN_DIFICULTADES):
            y = OPCION_Y0 + i * OPCION_PASO
            if i == self.indice:
                texto = recursos.texto(lienzo, dificultad.nombre.upper(), TAM_OPCION_ELEGIDA, DORADO, centro, y)
                self._marcar_opcion(lienzo, texto)
            else:
                recursos.texto(lienzo, dificultad.nombre.upper(), 64, GRIS_CLARO, centro, y + 4)
        recursos.texto(lienzo, d.ORDEN_DIFICULTADES[self.indice].descripcion, 38, BLANCO, centro, 710)
        recursos.texto(lienzo, "W / S: elegir        Enter: confirmar", 32, GRIS_CLARO, centro, 810)
        self.dibujar_indicadores(lienzo)


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
        # continuar=True: si venimos del selector de dificultad, la música sigue sin cortarse
        recursos.musica(d.MUSICA_SELECTOR_NIVELES, aj.VOLUMEN_MUSICA, continuar=True)

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
        elif evento.key == aj.TECLA_VOLVER:      # Esc: cambiar la dificultad
            self.juego.ir_a_selector_dificultad()

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
        recursos.texto(lienzo, f"Dificultad: {self.juego.progreso.dificultad_actual().nombre}   (Esc: cambiar)",
                       30, BLANCO, aj.ANCHO - 330, 14)
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
