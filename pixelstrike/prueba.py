import pygame
import random

pygame.init()
pantalla = pygame.display.set_mode((800, 600))
reloj = pygame.time.Clock()

class Particula:
    def __init__(self, x, y):
        self.x = x
        self.y = y
        # Velocidad en X y Y aleatoria
        self.vx = random.uniform(-3, 3)
        self.vy = random.uniform(-4, 0)
        self.radio = random.randint(2, 4)
        self.vida = 100  # Tiempo de vida de la partícula
        self.color = (255, random.randint(0, 100), 0)

    def actualizar(self):
        self.x += self.vx
        self.y += self.vy
        self.vida -= 1  # Se reduce la vida en cada fotograma

    def dibujar(self, superficie):
        if self.vida > 0:
            # Dibujar un círculo con desvanecimiento o color fijo
            pygame.draw.circle(
                superficie, 
                self.color, 
                (int(self.x), int(self.y)), 
                self.radio
            )

particulas = []
ejecutando = True

while ejecutando:
    dt = reloj.tick(60)
    for evento in pygame.event.get():
        if evento.type == pygame.QUIT:
            ejecutando = False

    # Crear nuevas partículas en la posición del mouse al hacer clic
    if pygame.mouse.get_pressed()[0]:
        mx, my = pygame.mouse.get_pos()
        for _ in range(5):
            particulas.append(Particula(mx, my))

    pantalla.fill((30, 30, 30))

    # Actualizar y filtrar partículas con vida mayor a cero
    for p in particulas:
        p.actualizar()
        p.dibujar(pantalla)
    
    particulas = [p for p in particulas if p.vida > 0]

    pygame.display.flip()

pygame.quit()
