"""Datos del juego: armas, personajes, enemigos, niveles, imágenes y sonidos.

Es el equivalente "declarativo" de las constantes que estaban repartidas entre
armas.wlk, enemigos.wlk, claseNivel.wlk, imagenIndicaciones.wlk, etc.
"""
from dataclasses import dataclass
from typing import Optional


# ============================================================================
# Armas
# ============================================================================
@dataclass(frozen=True)
class DatosArma:
    imagen_bala: str
    danio: int
    cadencia: float      # segundos entre disparos
    sonidos: tuple


_SONIDOS_FUSIL = ("sonidoRifle(1).mp3", "sonidoRifle(4).mp3", "sonidoRifle(5).mp3")
_SONIDOS_FUEGO = ("sonidoBolaFuego(1).mp3", "sonidoBolaFuego(2).mp3", "sonidoBolaFuego(3).mp3")
_SONIDOS_FUEGO_MAGMA = ("sondioBolaMagma(1).mp3", "sonidoBolaMagma(2).mp3", "sonidoBolaMagma(3).mp3")

FUSIL = DatosArma("bala(5).png", 10, 0.8, _SONIDOS_FUSIL)
FUSIL_ALIEN = DatosArma("balaAlienRaptor(5).png", 10, 0.8, _SONIDOS_FUSIL)
PISTOLA_PLASMA = DatosArma("balaPistolaPlasma.png", 8, 0.4, _SONIDOS_FUSIL)
BOLA_FUEGO = DatosArma("balaCrawler(4).png", 10, 1.2, _SONIDOS_FUEGO)
BOLA_MAGMA = DatosArma("balaZyrak.png", 7, 0.6, _SONIDOS_FUEGO_MAGMA)
BOLA_FUEGO_KRATOS = DatosArma("balaKratos.png", 10, 0.4, _SONIDOS_FUEGO)
BOLA_FUEGO_KRATOS_JUGABLE = DatosArma("balaKratos(1).png", 10, 0.4, _SONIDOS_FUEGO)

SONIDOS_IMPACTO = ("sonidoImpactoBala(1).mp3", "sonidoImpactoBala(2).mp3", "sonidoImpactoBala(3).mp3")


# ============================================================================
# Personajes
# ============================================================================
@dataclass(frozen=True)
class DatosPersonaje:
    clave: str
    skin: str
    vida_max: int
    arma: DatosArma
    tarjeta: str
    color_muerte: tuple = (255, 255, 255)   # color de las partículas al morir
    altura_muerte: float = 0.0              # celdas que se suben las partículas (el sprite sobresale de la celda)


BYTE_HUNTER = DatosPersonaje("byteHunter", "byteHunter.png", 100, FUSIL, "tarjetaJugador(1).png", (60, 140, 255), 1.75)
JADE = DatosPersonaje("jade", "jade.png", 100, PISTOLA_PLASMA, "tarjetaJugador(2).png", (140, 255, 150), 1.75)
KRATOS = DatosPersonaje("kratos", "finalBossReverse(1).png", 150, BOLA_FUEGO_KRATOS_JUGABLE, "tarjetaJugador(3).png", (220, 30, 30), 1.75)

ORDEN_PERSONAJES = (BYTE_HUNTER, JADE, KRATOS)
PERSONAJES = {p.clave: p for p in ORDEN_PERSONAJES}
PERSONAJE_INICIAL = BYTE_HUNTER.clave      # viene desbloqueado desde el comienzo
POSICION_TARJETA = (10, 7)


# ============================================================================
# Enemigos
# ============================================================================
@dataclass(frozen=True)
class DatosEnemigo:
    imagen: str
    vida: int
    arma: DatosArma
    intervalo_paso: tuple   # (min, max) segundos que tarda en avanzar una celda
    color_muerte: tuple = (255, 255, 255)
    altura_muerte: float = 0.0              # celdas que se suben las partículas (el sprite sobresale de la celda)


# Altura (en celdas) a la que nacen las partículas del jefe, contando desde su celda.
JEFE_ALTURA_MUERTE = 1.0

ALIEN_RAPTOR = DatosEnemigo("alienRaptorArma(1).png", 20, FUSIL_ALIEN, (0.75, 2.0), (255, 105, 180), 1.75)
CRAWLER = DatosEnemigo("crawler(2).png", 30, BOLA_FUEGO, (0.5, 0.75), (20, 120, 50), 1.75)
ZYRAK = DatosEnemigo("Zyrak(2).png", 25, BOLA_MAGMA, (0.6, 0.9), (255, 140, 0), 1.75)

# ============================================================================
# Dificultades
# ============================================================================
@dataclass(frozen=True)
class Dificultad:
    """Cómo se modifican los enemigos y el jefe. NORMAL es el juego tal cual era.

    Los datos base (DatosEnemigo, DatosArma...) no se tocan: cada enemigo aplica
    estos valores al crearse.
    """
    clave: str
    nombre: str
    descripcion: str
    mult_vida: float            # vida de los enemigos
    mult_velocidad: float       # velocidad de avance (más alto = más rápido)
    mult_cadencia: float        # multiplica el TIEMPO entre disparos (más alto = dispara menos)
    mult_danio: float           # daño de las balas y del fuego enemigos
    mult_spawn: float           # multiplica el TIEMPO entre apariciones (más alto = menos enemigos)
    danio_escape: int           # daño al jugador si un enemigo cruza la pantalla
    vida_jefe: int
    intervalo_ataques_jefe: float   # segundos entre ataques de Kratos
    mult_xp_ganada: float = 1.0     # multiplicador de experiencia ganada
    mult_xp_perdida: float = 1.0    # multiplicador de experiencia perdida


FACIL = Dificultad("facil", "Facil",
                   "Enemigos con la mitad de vida, mas lentos y que pegan menos.",
                   mult_vida=0.5, mult_velocidad=0.8, mult_cadencia=1.25, mult_danio=0.5,
                   mult_spawn=1.25, danio_escape=10, vida_jefe=100, intervalo_ataques_jefe=1.4,
                   mult_xp_ganada=0.8, mult_xp_perdida=1.0)
NORMAL = Dificultad("normal", "Normal",
                    "La experiencia original de Pixel Strike.",
                    mult_vida=1.0, mult_velocidad=1.0, mult_cadencia=1.0, mult_danio=1.0,
                    mult_spawn=1.0, danio_escape=15, vida_jefe=150, intervalo_ataques_jefe=1.1,
                    mult_xp_ganada=1.0, mult_xp_perdida=1.0)
DIFICIL = Dificultad("dificil", "Dificil",
                     "Enemigos mas resistentes, rapidos y letales. Kratos no tiene piedad.",
                     mult_vida=1.5, mult_velocidad=1.25, mult_cadencia=0.8, mult_danio=1.5,
                     mult_spawn=0.75, danio_escape=20, vida_jefe=225, intervalo_ataques_jefe=0.8,
                     mult_xp_ganada=1.2, mult_xp_perdida=1.2)

ORDEN_DIFICULTADES = (FACIL, NORMAL, DIFICIL)
DIFICULTADES = {x.clave: x for x in ORDEN_DIFICULTADES}
DIFICULTAD_INICIAL = NORMAL.clave


# ============================================================================
# Power ups
# ============================================================================
@dataclass(frozen=True)
class DatosPowerUp:
    clave: str
    item: str
    icono_inactivo: str
    icono_activo: str
    duracion: float       # segundos
    x_icono: int


POWERUPS = {
    "cadencia": DatosPowerUp("cadencia", "powerUpCadenciaItem.png", "powerUpCadenciaIcon(1).png",
                             "powerUpCadencia(2).png", 20.0, 25),
    "danio": DatosPowerUp("danio", "powerUpDañoItem.png", "powerUpDañoIcon(1).png",
                          "powerUpDaño(2).png", 15.0, 27),
    "defensa": DatosPowerUp("defensa", "powerUpDefensaItem.png", "powerUpDefensaIcon(1).png",
                            "powerUpDefensa(2).png", 13.0, 29),
}
Y_ICONOS_POWERUP = 16


# ============================================================================
# Indicadores (imágenes que se muestran en pantalla)
# ============================================================================
@dataclass(frozen=True)
class DatosIndicador:
    imagen: str
    x: int
    y: int
    duracion: float = 0.0   # solo importa en las secuencias de imágenes

TITULO_MENU_PRINCIPAL = DatosIndicador("CreditosFinal(4).png", 0, 0)

MENU_PAUSA = DatosIndicador("menuPausa.png", 3, 2)
NO_PUEDES_PAUSAR = DatosIndicador("noPuedesPausar.png", 9, 13)
PERSONAJE_DESBLOQUEADO = DatosIndicador("hasDesbloqueadoUnPersonaje(1).png", 9, 9)
PERSONAJE_BLOQUEADO = DatosIndicador("personajeBloqueado.png", 10, 7)
NOMBRE_KRATOS = DatosIndicador("vidaKratosImagen(1).png", 14, 11)
MAS_ENEMIGOS = DatosIndicador("Nivel + MasEnemigos.png", 8, 14)
HAS_GANADO = DatosIndicador("Has-Ganado(2).png", 0, 0)
HAS_MUERTO = DatosIndicador("Has-Muerto(1).png", 0, 0)
REINICIAR = DatosIndicador("reiniciar(3).png", 11, 5)
ATENCION_LLUVIA = DatosIndicador("AtencionLluviaFuego.png", 8, 14)

BANNER_NIVEL_1 = DatosIndicador("Nivel-1-ten-cuidado-con.png", 8, 14)
BANNER_NIVEL_2 = DatosIndicador("Nivel-2-Crawlers.png", 9, 14)
BANNER_NIVEL_3 = DatosIndicador("Nivel-3-Alien-Crawler.png", 7, 14)

TUTO_ENTER = DatosIndicador("Presione-enter-para-cont(1).png", 24, 16)
TUTO_MOVER = DatosIndicador("Muevete-con-WASD.png", 12, 14)
TUTO_DISPARAR = DatosIndicador("disparecon.png", 12, 14)
TUTO_POWERUP = DatosIndicador("instruccionPowerUp.png", 8, 13)
TUTO_INTERACTIVO_1 = DatosIndicador("tutorialInteractivo(1).png", 4, 14)
TUTO_INTERACTIVO_2 = DatosIndicador("tutorialInteractivo(2).png", 4, 14)
TUTO_FIN = DatosIndicador("Perfecto-pasemos-al-niv.png", 10, 14)
PASOS_TUTORIAL = (TUTO_MOVER, TUTO_DISPARAR, TUTO_POWERUP)

INTRO_JEFE = (
    DatosIndicador("Nivel-Final(5).png", 1, 14, 5),
    DatosIndicador("Nivel-Final(6).png", 4, 14, 5),
    DatosIndicador("Nivel-Final(7).png", 5, 14, 5),
    DatosIndicador("Nivel-Final(8).png", 11, 14, 4),
)
CREDITOS = (
    DatosIndicador("CreditosFinal.png", 14, 9, 5),
    DatosIndicador("CreditosFinal(2).png", 11, 9, 5),
    DatosIndicador("CreditosFinal(3).png", 12, 9, 5),
    DatosIndicador("CreditosFinal(4).png", 14, 9, 5),
)

# Imágenes sueltas
CORAZON_ROJO = "vidaCorazonRojo.png"
CORAZON_VIOLETA = "vidaCorazonVioleta.png"
CORAZON_GRIS = "vidaCorazonGris(7).png"
MARCA_CAMINO = "marcaCamino(2).png"
PUERTA_BLOQUEADA = "puertaRoja(1).png"
PUERTA_DESBLOQUEADA = "puertaVerde(1).png"
JEFE_SKIN_INTRO = "finalBoss(2).png"
JEFE_SKIN_COMBATE = "finalBoss(1).png"
FILA_FUEGO = "filaFuego(2).png"
FILA_ADVERTENCIA = "advertenciaDeFila(1).png"
GOTA_FUEGO = "bolaDeFuegoKratos.png"
GOTA_ADVERTENCIA = "advertenciaDeLluvia.png"

# Fondos
FONDO_SELECTOR_PERSONAJES = "fondoSelectorPersonajes(2).png"
FONDO_SELECTOR_NIVELES = "FondoSelectorNiveles(2).png"
FONDO_CREDITOS = "fondoFinal.png"
FONDO_SELECTOR_DIFICULTAD = "menuPrincipal.png"

# Imágenes OPCIONALES del selector de dificultad. Si no están en assets/ se usa
# texto para el título y un recuadro dorado para marcar la opción elegida.
TITULO_JUEGO = "tituloPixelStrike.png"
TRIANGULOS_SELECTOR = "selectorTriangulos.png"   # un solo PNG con dos triángulos enfrentados

# Música
MUSICA_SELECTOR_PERSONAJES = "selectorDePersonajesSong.mp3"
MUSICA_SELECTOR_NIVELES = "selectorDeNivelesSong.mp3"
MUSICA_CREDITOS = "finalSong.mp3"

# Efectos de sonido
SFX_NIVEL_NUEVO = "level-up-enhancement-8-bit-retro-sound-effect-153002.mp3"
SFX_ATENCION = "masEnemigosAtencion(1).mp3"
SFX_POWERUP = "recogerPowerUp(1).mp3"
SFX_LATIDO = "heartbeat.mp3"
SFX_CLICK = "clickButton.mp3"
SFX_ERROR = "errorSonido.mp3"
SFX_SELECCION_PERSONAJE = "selectorPersonajes(1).mp3"
SFX_VICTORIA_1 = "victory(3).mp3"
SFX_VICTORIA_2 = "victory(4).mp3"
SFX_VICTORIA_3 = "victory(5).mp3"
SFX_DERROTA_1 = "gameOver(3).mp3"
SFX_DERROTA_2 = "gameOver(2).mp3"
SFX_TRUENO = "thunder.mp3"
SFX_LLUVIA = ("lluvia(1).mp3", "lluvia(2).mp3", "lluvia(6).mp3", "lluvia(7).mp3", "lluvia(8).mp3")
SFX_LLUVIA_FINAL = "lluvia(9).mp3"
SFX_WHOOSH = ("whoosh.mp3", "whoosh(1).mp3")


# ============================================================================
# Sistema de XP y Puntuación
# ============================================================================
XP_ALIEN = 25
XP_CRAWLER = 40
XP_PENALIZACION_DISPARO = 15
XP_RACHA_3 = 10
XP_RACHA_7 = 30
XP_NIVEL_PERFECTO = 100
XP_JEFE = 200

UMBRALES_XP = (0, 150, 400, 800, 1400, 2200, 3200)
XP_POR_NIVEL_ADICIONAL = 1000

RANGOS_XP = {
    1: "Recluta",
    2: "Cadete",
    3: "Soldado",
    4: "Veterano",
    5: "Comandante",
    6: "Élite",
    7: "Maestro",
}



# ============================================================================
# Niveles
# ============================================================================
@dataclass(frozen=True)
class DatosNivel:
    clave: str
    musica: str
    fondo: str
    siguiente: Optional[str] = None
    tipo: str = "horda"                    # "tutorial" | "horda" | "jefe"
    aliens: int = 0
    crawlers: int = 0
    zyraks: int = 0
    spawn_min: int = 0                     # segundos entre enemigos (se sortea un entero)
    spawn_max: int = 0
    powerup: Optional[str] = None
    enemigo_con_powerup: Optional[int] = None   # n-ésimo enemigo en aparecer
    banner: Optional[DatosIndicador] = None
    personaje: Optional[str] = None        # personaje que se desbloquea al superarlo


NIVELES = {
    "nivel0": DatosNivel("nivel0", "nivelCeroSong(1).mp3", "FondoJuego(3).png",
                         siguiente="nivel1", tipo="tutorial"),
    "nivel1": DatosNivel("nivel1", "nivelUnoSong(1).mp3", "FondoJuego(3).png",
                         siguiente="nivel2", aliens=5, spawn_min=4, spawn_max=4,
                         powerup="danio", enemigo_con_powerup=4,
                         banner=BANNER_NIVEL_1, personaje=JADE.clave),
    "nivel2": DatosNivel("nivel2", "nivelDosSong(1).mp3", "FondoJuegoPrueba(2).png",
                         siguiente="nivel3", crawlers=7, spawn_min=3, spawn_max=4,
                         powerup="cadencia", enemigo_con_powerup=4, banner=BANNER_NIVEL_2),
    "nivel3": DatosNivel("nivel3", "nivelTresSong(2).mp3", "FondoJuegoPrueba(4).png",
                         siguiente="nivel4", aliens=7, crawlers=8, spawn_min=3, spawn_max=3,
                         powerup="defensa", enemigo_con_powerup=4, banner=BANNER_NIVEL_3),
    "nivel4": DatosNivel("nivel4", "nivelFinalSong(1).mp3", "FondoJuegoNivelFinal.png",
                         tipo="jefe", personaje=KRATOS.clave),
    "nivel_Pruebas": DatosNivel("test", "", "FondoJuego(3).png",aliens=0, crawlers=0, zyraks=1, spawn_min=4, spawn_max=4, powerup="danio", enemigo_con_powerup=1, banner=BANNER_NIVEL_1),
}

# Puertas del selector de niveles: (columna, clave del nivel). Todas en la fila 3.
PUERTAS = ((2, "nivel0"), (8, "nivel1"), (14, "nivel2"), (20, "nivel3"), (26, "nivel4"))
FILA_PUERTAS = 3
