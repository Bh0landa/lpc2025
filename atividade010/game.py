import random
import sys
from dataclasses import dataclass

import pygame as pg

import config as C
from systems import World
from utils import text


# Representa uma cena simples do jogo por nome
@dataclass
class Scene:
    """Cena simples representada por um nome.

    Usada para alternar entre 'menu' e 'play'.
    """
    name: str


class Game:
    # Inicializa pygame, fontes, janela e o mundo do jogo
    def __init__(self):
        pg.init()
        if C.RANDOM_SEED is not None:
            random.seed(C.RANDOM_SEED)
        # Abrir a janela na resolução definida em config (janela)
        self.screen = pg.display.set_mode((C.WIDTH, C.HEIGHT))
        pg.display.set_caption("Asteroids")
        self.clock = pg.time.Clock()
        self.font = pg.font.SysFont("consolas", 20)
        self.big = pg.font.SysFont("consolas", 48)
        self.scene = Scene("menu")
        self.world = World()

    # Loop principal do jogo que processa eventos e atualiza a cena
    def run(self):
        while True:
            dt = self.clock.tick(C.FPS) / 1000.0
            for e in pg.event.get():
                if e.type == pg.QUIT:
                    pg.quit()
                    sys.exit(0)
                if e.type == pg.KEYDOWN and e.key == pg.K_ESCAPE:
                    pg.quit()
                    sys.exit(0)
                # Entradas dependem da cena atual
                if self.scene.name == "play":
                    # Hyperspace ainda por tecla Shift (evento)
                    if e.type == pg.KEYDOWN and e.key == pg.K_LSHIFT:
                        self.world.hyperspace()
                elif self.scene.name == "menu":
                    if e.type == pg.KEYDOWN:
                        self.scene = Scene("play")

            keys = pg.key.get_pressed()
            # Permite atirar enquanto o botão esquerdo do mouse estiver pressionado
            mouse_buttons = pg.mouse.get_pressed()
            if self.scene.name == "play" and mouse_buttons[0]:
                self.world.try_fire()

            self.screen.fill(C.BLACK)

            if self.scene.name == "menu":
                self.draw_menu()
            elif self.scene.name == "play":
                # Atualiza o mundo e desenha os sprites
                self.world.update(dt, keys)
                self.world.draw(self.screen, self.font)

            pg.display.flip()

    # Desenha o menu inicial
    def draw_menu(self):
        # Centered menu layout
        title_surf = self.big.render("ASTEROIDS", True, C.WHITE)
        title_rect = title_surf.get_rect(center=(C.WIDTH // 2, 160))
        self.screen.blit(title_surf, title_rect)
        info = (
            "W: thrust  S: brake  Mouse: rotate  Right-click: shoot "
            "Shift: hyperspace"
        )
        info_surf = self.font.render(info, True, C.WHITE)
        info_rect = info_surf.get_rect(center=(C.WIDTH // 2, 260))
        self.screen.blit(info_surf, info_rect)

        dev_surf = self.font.render("DEVS: Holanda, Clewerton", True, C.WHITE)
        dev_rect = dev_surf.get_rect(center=(C.WIDTH // 2, 300))
        self.screen.blit(dev_surf, dev_rect)

        prompt_surf = self.font.render("Press any key...", True, C.WHITE)
        prompt_rect = prompt_surf.get_rect(center=(C.WIDTH // 2, 360))
        self.screen.blit(prompt_surf, prompt_rect)