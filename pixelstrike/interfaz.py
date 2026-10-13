"""Elementos de HUD: barras de vida y barra de power ups."""
from . import ajustes as aj
from . import datos as d
from .recursos import recursos


def dibujar_barra_vida(lienzo, vida, vida_max, x0, y, imagen_corazon):
    """Un corazón cada 10 de vida; los perdidos se muestran en gris."""
    total = vida_max // aj.VIDA_POR_CORAZON
    llenos = max(0, vida) // aj.VIDA_POR_CORAZON
    for i in range(total):
        recursos.dibujar(lienzo, imagen_corazon if i < llenos else d.CORAZON_GRIS, x0 + i, y)


def dibujar_barra_powerups(lienzo, jugador):
    duracion_parpadeo = aj.PARPADEO_ICONO * aj.PARPADEO_ICONO_REPS
    for clave, datos in d.POWERUPS.items():
        restante = jugador.efectos.get(clave)
        if restante is None:
            imagen = datos.icono_inactivo
        elif restante > duracion_parpadeo:
            imagen = datos.icono_activo
        else:
            # Últimos segundos: el ícono parpadea y termina apagado
            fase = int((duracion_parpadeo - restante) / aj.PARPADEO_ICONO)
            if fase % 2 == 0:
                continue
            imagen = datos.icono_activo
        recursos.dibujar(lienzo, imagen, datos.x_icono, d.Y_ICONOS_POWERUP)
