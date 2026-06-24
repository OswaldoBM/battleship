# -*- coding: utf-8 -*-
"""
====================================================
  BATALLA NAVAL - VERSIÓN GRÁFICA CON PIXEL ART
  Librería: pip install pygame-ce
  Python 3.x

  Controles:
    - Click izquierdo  -> Colocar barco / Disparar
    - Click derecho    -> Rotar barco (al colocarlo)
    - Tecla R          -> Rotar barco (al colocarlo)
    - ESC              -> Salir

  Conceptos de POO:
    - Clases y Objetos
    - Herencia (JugadorIA)
    - Encapsulamiento (métodos privados con _)
    - Composición (BatallaNavalGUI contiene Tablero, IA, SpriteManager)
====================================================
"""

import pygame   # Librería para gráficos y ventana
import sys      # Para cerrar el programa
import random   # Para la IA y colocación aleatoria
import math     # Para animaciones con seno/coseno
import os       # Para rutas de archivos
try:
    import cv2      # Para reproducir el video
    import numpy as np
    CV2_OK = True
except ImportError:
    CV2_OK = False

# ─── Inicialización de Pygame ───
pygame.init()

# ── Dimensiones de la ventana ──
ANCHO = 1200
ALTO  = 720
CELDA = 44       # Tamaño en píxeles de cada celda
FILAS = 10
COLS  = 10
FPS   = 60       # Fotogramas por segundo

# ── Pixel Art ──
PPU = 11         # Píxeles artísticos por celda (resolución baja)
#                  Al escalar 4x (44/11) se crea el efecto pixel art

# ── Posiciones de tableros en pantalla ──
POS_JUG = (52, 160)     # Tablero del jugador (izquierda)
POS_ENE = (645, 160)    # Tablero del enemigo (derecha)
POS_COL = (380, 130)    # Tablero centrado en fase de colocación

# ─────────────────────────────────────────────────────
#  PALETA DE COLORES (RGB)
# ─────────────────────────────────────────────────────
FONDO     = (8,   15,  40)
AGUA      = (18,  58, 138)
IMPACTO   = (228,  58,  48)
FALLO_C   = (72, 132, 198)
BORDE     = (28,  68, 158)
BORDE_H   = (78, 158, 255)
TEXTO     = (205, 228, 255)
TITULO_C  = (92, 195, 255)
ACENTO    = (255, 202,  48)
BLANCO    = (255, 255, 255)
GRIS      = (112, 125, 152)
VERDE     = (45, 198, 102)
ROJO_C    = (222,  48,  48)
BTN       = (22,  58, 138)
BTN_H     = (48, 108, 218)
BTN_T     = (195, 225, 255)
PANEL_C   = (12,  28,  68)

# ── Colores pixel art de los barcos ──
C_CASCO    = (58, 68, 85)       # Borde del casco
C_CUBIERTA = (78, 90, 110)      # Relleno de cubierta
C_TORRETA  = (48, 55, 70)       # Torretas de cañón
C_PUENTE   = (52, 60, 78)       # Puente de mando
C_DETALLE  = (95, 108, 128)     # Detalles claros
C_VENTANA  = (140, 180, 240)    # Ventanas / luces
C_PISTA    = (92, 102, 118)     # Pista del portaaviones

# ── Colores de efectos ──
C_FUEGO1 = (255, 160, 20)       # Fuego naranja
C_FUEGO2 = (255, 80,  20)       # Fuego rojo

# ── Estados del juego ──
MENU    = 'menu'
COLOCAR = 'colocar'
JUGAR   = 'jugar'
FIN     = 'fin'
VIDEO   = 'video'

# ── Ruta del video de victoria ──
VIDEO_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                           'quiero_que_el_video_sea_el_per.mp4')

# ── Información de barcos (nombre, tamaño) ──
BARCOS_INFO = [
    ('Portaaviones', 5),
    ('Acorazado',    4),
    ('Crucero',      3),
    ('Submarino',    3),
    ('Destructor',   2),
]


# ============================================================
# CLASE: Barco
# ============================================================
class Barco:
    """Representa un barco con nombre, tamaño e impactos recibidos."""

    def __init__(self, nombre, tamano):
        self.nombre   = nombre
        self.tamano   = tamano
        self.impactos = 0
        self.hundido  = False

    def recibir_impacto(self):
        """Registra un impacto. Retorna True si el barco se hundió."""
        self.impactos += 1
        if self.impactos >= self.tamano:
            self.hundido = True
            return True
        return False

    def __str__(self):
        return f"{self.nombre} ({self.tamano})"


# ============================================================
# CLASE: Tablero
# Cuadrícula 10x10 con rastreo de barcos por celda
# ============================================================
class Tablero:
    """
    Tablero de 10x10 que sabe qué barco hay en cada celda.
    self.mapa[f][c] = (índice_barco, índice_segmento, es_horizontal) o None
    """

    def __init__(self):
        self.celdas   = [['agua'] * COLS for _ in range(FILAS)]
        self.barcos   = []          # Lista de {'barco', 'casillas', 'dir_h'}
        self.disparos = set()       # Coordenadas ya disparadas
        self.mapa     = [[None] * COLS for _ in range(FILAS)]

    def _calcular_casillas(self, fila, col, tamano, dir_h):
        """Calcula qué celdas ocuparía un barco. Retorna None si se sale."""
        casillas = []
        for i in range(tamano):
            f = fila + (0 if dir_h else i)
            c = col  + (i if dir_h else 0)
            if not (0 <= f < FILAS and 0 <= c < COLS):
                return None
            casillas.append((f, c))
        return casillas

    def puede_colocar(self, fila, col, tamano, dir_h):
        """Verifica si se puede colocar sin solaparse ni salirse."""
        casillas = self._calcular_casillas(fila, col, tamano, dir_h)
        if casillas is None:
            return False
        return all(self.celdas[f][c] == 'agua' for f, c in casillas)

    def colocar(self, barco, fila, col, dir_h):
        """Coloca un barco y registra su posición en el mapa."""
        casillas = self._calcular_casillas(fila, col, barco.tamano, dir_h)
        if casillas is None:
            return False
        for f, c in casillas:
            if self.celdas[f][c] != 'agua':
                return False

        idx = len(self.barcos)
        for i, (f, c) in enumerate(casillas):
            self.celdas[f][c] = 'barco'
            self.mapa[f][c] = (idx, i, dir_h)

        self.barcos.append({'barco': barco, 'casillas': casillas, 'dir_h': dir_h})
        return True

    def disparar(self, fila, col):
        """Procesa un disparo. Retorna resultado con info del barco."""
        coord = (fila, col)
        if coord in self.disparos:
            return {'resultado': 'repetido', 'barco': None}
        self.disparos.add(coord)

        for entrada in self.barcos:
            if coord in entrada['casillas']:
                barco   = entrada['barco']
                hundido = barco.recibir_impacto()
                self.celdas[fila][col] = 'impacto'
                return {
                    'resultado': 'hundido' if hundido else 'impacto',
                    'barco':     barco,
                    'casillas':  entrada['casillas'] if hundido else None,
                    'dir_h':     entrada.get('dir_h', True),
                }
        self.celdas[fila][col] = 'fallo'
        return {'resultado': 'agua', 'barco': None}

    def todos_hundidos(self):
        return all(e['barco'].hundido for e in self.barcos)


# ============================================================
# CLASE: JugadorIA
# IA con estrategia: modo buscar → modo atacar
# ============================================================
class JugadorIA:
    """Computadora que coloca barcos y dispara con estrategia."""

    def __init__(self):
        self.tablero    = Tablero()
        self.modo       = 'buscar'
        self.pendientes = []
        self._colocar_barcos()

    def _colocar_barcos(self):
        for nombre, tam in BARCOS_INFO:
            barco = Barco(nombre, tam)
            ok = False
            while not ok:
                f     = random.randint(0, 9)
                c     = random.randint(0, 9)
                dir_h = random.choice([True, False])
                ok    = self.tablero.colocar(barco, f, c, dir_h)

    def elegir_disparo(self, tablero_jug):
        ya = tablero_jug.disparos
        if self.modo == 'atacar' and self.pendientes:
            while self.pendientes:
                f, c = self.pendientes.pop(0)
                if (f, c) not in ya:
                    return (f, c)
        self.modo = 'buscar'
        while True:
            f = random.randint(0, 9)
            c = random.randint(0, 9)
            if (f, c) not in ya:
                return (f, c)

    def notificar(self, fila, col, resultado):
        if resultado == 'impacto':
            self.modo = 'atacar'
            for df, dc in [(-1, 0), (1, 0), (0, -1), (0, 1)]:
                nf, nc = fila + df, col + dc
                if 0 <= nf < 10 and 0 <= nc < 10 and (nf, nc) not in self.pendientes:
                    self.pendientes.append((nf, nc))
        elif resultado == 'hundido':
            self.modo       = 'buscar'
            self.pendientes = []


# ============================================================
# CLASE: SpriteManager
# Genera sprites pixel art para cada tipo de barco
# ============================================================
class SpriteManager:
    """
    Crea los dibujos de los barcos a resolución artística baja (PPU=11)
    y los escala 4x para obtener el look pixel art.
    Guarda versiones horizontales, verticales y de naufragio.
    """

    def __init__(self):
        self.sprites_h    = {}   # nombre -> [segmento0, segmento1, ...]
        self.sprites_v    = {}
        self.naufragios_h = {}   # Versiones destruidas (oscurecidas)
        self.naufragios_v = {}
        self._generar_todos()

    def obtener(self, nombre, dir_h):
        """Retorna los segmentos de sprite en la dirección dada."""
        return self.sprites_h[nombre] if dir_h else self.sprites_v[nombre]

    def obtener_naufragio(self, nombre, dir_h):
        """Retorna los segmentos de naufragio (barco hundido)."""
        return self.naufragios_h[nombre] if dir_h else self.naufragios_v[nombre]

    def _generar_todos(self):
        """Genera sprites para todos los barcos, en ambas direcciones."""
        for nombre, tam in BARCOS_INFO:
            segs_h = self._crear_barco(nombre, tam, True)
            segs_v = self._crear_barco(nombre, tam, False)
            self.sprites_h[nombre]    = segs_h
            self.sprites_v[nombre]    = segs_v
            self.naufragios_h[nombre] = self._oscurecer(segs_h)
            self.naufragios_v[nombre] = self._oscurecer(segs_v)

    def _oscurecer(self, segmentos):
        """Crea versión oscurecida/destruida de los sprites."""
        result = []
        for s in segmentos:
            w = s.copy()
            # Capa oscura
            dark = pygame.Surface(w.get_size(), pygame.SRCALPHA)
            dark.fill((0, 0, 0, 130))
            w.blit(dark, (0, 0))
            # Tinte rojo de daño
            red = pygame.Surface(w.get_size(), pygame.SRCALPHA)
            red.fill((180, 30, 0, 45))
            w.blit(red, (0, 0))
            result.append(w)
        return result

    def _crear_barco(self, nombre, tamano, horizontal):
        """
        1. Dibuja el barco completo a resolución PPU (baja)
        2. Lo escala 4x para efecto pixel art
        3. Lo divide en segmentos de CELDA×CELDA
        """
        w_art = tamano * PPU   # Ancho artístico total
        h_art = PPU             # Alto artístico (11 px)

        art = pygame.Surface((w_art, h_art), pygame.SRCALPHA)

        # Dibujar casco (polígono relleno + borde)
        puntos = self._casco(nombre, w_art, h_art)
        pygame.draw.polygon(art, C_CUBIERTA, puntos)    # Relleno claro
        pygame.draw.polygon(art, C_CASCO, puntos, 1)    # Borde oscuro

        # Dibujar detalles específicos del tipo de barco
        self._detalles(art, nombre, w_art, h_art)

        # Escalar al tamaño real (nearest neighbor = pixel art)
        grande = pygame.transform.scale(art, (tamano * CELDA, CELDA))

        # Si es vertical, rotar 90° en sentido horario
        if not horizontal:
            grande = pygame.transform.rotate(grande, 90)

        # Dividir en segmentos de CELDA × CELDA
        segmentos = []
        for i in range(tamano):
            seg = pygame.Surface((CELDA, CELDA), pygame.SRCALPHA)
            if horizontal:
                seg.blit(grande, (-i * CELDA, 0))
            else:
                seg.blit(grande, (0, -i * CELDA))
            segmentos.append(seg)
        return segmentos

    # ── Formas de casco (polígonos top-down) ──

    def _casco(self, nombre, w, h):
        """
        Retorna los puntos del polígono del casco visto desde arriba.
        La proa (frente) está a la izquierda (x=0).
        """
        cy = h // 2  # Centro vertical (5 para PPU=11)

        if nombre == 'Portaaviones':
            # Ancho, cubierta plana, proa apuntada
            return [
                (0, cy), (3, 1), (7, 1),
                (w - 3, 1), (w - 1, 3),
                (w - 1, h - 3), (w - 3, h - 1),
                (7, h - 1), (3, h - 1),
            ]
        elif nombre == 'Acorazado':
            # Clásico, proa afilada, cuerpo medio
            return [
                (0, cy), (3, 2), (6, 2),
                (w - 3, 2), (w - 1, 4),
                (w - 1, h - 4), (w - 3, h - 2),
                (6, h - 2), (3, h - 2),
            ]
        elif nombre == 'Crucero':
            # Esbelto, rápido
            return [
                (0, cy), (3, 2), (5, 2),
                (w - 3, 2), (w - 1, 4),
                (w - 1, h - 4), (w - 3, h - 2),
                (5, h - 2), (3, h - 2),
            ]
        elif nombre == 'Submarino':
            # Forma de cigarro, ambos extremos redondeados
            return [
                (1, cy), (3, 3), (5, 3),
                (w - 5, 3), (w - 3, 3), (w - 1, cy),
                (w - 3, h - 3), (w - 5, h - 3),
                (5, h - 3), (3, h - 3),
            ]
        else:  # Destructor
            # Pequeño y ágil, ambos extremos en punta
            return [
                (0, cy), (2, 3), (4, 3),
                (w - 4, 3), (w - 1, cy),
                (w - 4, h - 3), (4, h - 3), (2, h - 3),
            ]

    # ── Detalles de cada barco ──

    def _detalles(self, surf, nombre, w, h):
        """Dibuja torretas, puente, pista, periscopio, etc."""
        cy = h // 2

        if nombre == 'Portaaviones':
            # Línea de pista de aterrizaje (centro)
            pygame.draw.line(surf, C_PISTA, (5, cy), (w - 4, cy))
            # Isla de vuelo (torre de control arriba a la derecha)
            pygame.draw.rect(surf, C_PUENTE, (w * 3 // 4, 1, 5, 3))
            # Antena sobre la isla
            pygame.draw.rect(surf, C_TORRETA, (w * 3 // 4 + 1, 0, 3, 1))
            # Marcas de pista (puntos decorativos a lo largo)
            for x in range(10, w - 8, 7):
                surf.set_at((x, cy - 1), C_DETALLE)
                surf.set_at((x, cy + 1), C_DETALLE)

        elif nombre == 'Acorazado':
            # Tres torretas de cañones con líneas de cañón
            for tx in [7, w // 2 - 1, w - 10]:
                pygame.draw.rect(surf, C_TORRETA, (tx, cy - 2, 3, 4))
                pygame.draw.line(surf, C_CASCO, (tx - 1, cy), (tx, cy))
            # Puente de mando (centro)
            pygame.draw.rect(surf, C_PUENTE, (w // 2 - 3, 2, 3, h - 4))
            # Ventanillas del puente
            surf.set_at((w // 2 - 2, 3), C_VENTANA)
            surf.set_at((w // 2 - 2, h - 4), C_VENTANA)

        elif nombre == 'Crucero':
            # Torreta delantera con cañón
            pygame.draw.rect(surf, C_TORRETA, (5, cy - 1, 3, 3))
            pygame.draw.line(surf, C_CASCO, (4, cy), (5, cy))
            # Puente central
            pygame.draw.rect(surf, C_PUENTE, (w // 2 - 1, 3, 3, h - 6))
            surf.set_at((w // 2, 3), C_VENTANA)
            # Torreta trasera
            pygame.draw.rect(surf, C_TORRETA, (w - 8, cy - 1, 3, 3))

        elif nombre == 'Submarino':
            # Torre de comando (sobresale del casco)
            pygame.draw.rect(surf, C_PUENTE, (w // 2 - 2, 2, 5, 3))
            # Periscopio (línea vertical arriba)
            pygame.draw.line(surf, C_DETALLE, (w // 2, 0), (w // 2, 2))
            surf.set_at((w // 2, 0), C_VENTANA)  # Lente del periscopio
            # Timón trasero
            pygame.draw.rect(surf, C_TORRETA, (w - 3, cy - 2, 2, 4))

        else:  # Destructor
            # Torreta delantera
            pygame.draw.rect(surf, C_TORRETA, (4, cy - 1, 2, 3))
            pygame.draw.line(surf, C_CASCO, (3, cy), (4, cy))
            # Puente pequeño
            pygame.draw.rect(surf, C_PUENTE, (w // 2, 3, 3, h - 6))
            surf.set_at((w // 2 + 1, 3), C_VENTANA)


# ============================================================
# CLASE: Particula
# Efecto visual de explosiones, fuego, salpicaduras, burbujas
# ============================================================
class Particula:
    """
    Partícula animada con posición, velocidad y vida.
    Tipos: 'normal', 'fuego', 'burbuja', 'fragmento'.
    """

    def __init__(self, x, y, color, tipo='normal'):
        self.x     = float(x)
        self.y     = float(y)
        self.color = color
        self.tipo  = tipo

        # Cada tipo tiene comportamiento diferente
        if tipo == 'fuego':
            self.vx    = random.uniform(-3, 3)
            self.vy    = random.uniform(-6, -1)
            self.vida  = random.randint(15, 35)
            self.radio = random.randint(3, 7)
        elif tipo == 'burbuja':
            self.vx    = random.uniform(-0.5, 0.5)
            self.vy    = random.uniform(-1.5, -0.5)
            self.vida  = random.randint(30, 60)
            self.radio = random.randint(2, 5)
        elif tipo == 'fragmento':
            self.vx    = random.uniform(-5, 5)
            self.vy    = random.uniform(-9, -2)
            self.vida  = random.randint(40, 80)
            self.radio = random.randint(3, 8)
        else:
            self.vx    = random.uniform(-4.5, 4.5)
            self.vy    = random.uniform(-7, -1)
            self.vida  = random.randint(20, 45)
            self.radio = random.randint(2, 6)

        self.vida_max = self.vida

    def actualizar(self):
        self.x += self.vx
        self.y += self.vy
        if self.tipo == 'burbuja':
            self.x += math.sin(self.vida * 0.2) * 0.5
            self.vy -= 0.01       # Las burbujas suben
        else:
            self.vy += 0.3        # Gravedad
        self.vida -= 1

    def dibujar(self, surface):
        alfa = max(0, self.vida / self.vida_max)
        r, g, b = self.color
        col = (int(r * alfa), int(g * alfa), int(b * alfa))
        rad = max(1, int(self.radio * alfa))
        pygame.draw.circle(surface, col, (int(self.x), int(self.y)), rad)

    @property
    def vivo(self):
        return self.vida > 0


# ============================================================
# CLASE: AnimHundimiento
# Animación dramática cuando un barco se destruye por completo
# ============================================================
class AnimHundimiento:
    """
    Fases de la animación:
      1. Flash blanco (frames 0-15)
      2. Onda expansiva (frames 0-50)
      3. Fragmentos del barco vuelan y caen (frames 12-120)
      4. Burbujas suben desde el agua (frames 20-120)
    """

    def __init__(self, casillas_px, sprites):
        """
        Parámetros:
            casillas_px : lista de (px, py) coordenadas en pantalla
            sprites     : lista de Surface de cada segmento del barco
        """
        self.frame     = 0
        self.duracion  = 130
        self.terminado = False
        self.casillas  = casillas_px

        # ── Fragmentos del barco ──
        # Cada segmento se parte en 4 pedazos que salen volando
        self.fragmentos = []
        mitad = CELDA // 2
        for (px, py), sprite in zip(casillas_px, sprites):
            for qx, qy in [(0, 0), (mitad, 0), (0, mitad), (mitad, mitad)]:
                frag = pygame.Surface((mitad, mitad), pygame.SRCALPHA)
                frag.blit(sprite, (-qx, -qy))
                self.fragmentos.append({
                    'surf':  frag,
                    'x':     float(px + qx),
                    'y':     float(py + qy),
                    'vx':    random.uniform(-4, 4),
                    'vy':    random.uniform(-8, -2),
                    'rot':   0.0,
                    'vrot':  random.uniform(-7, 7),
                    'alpha': 255.0,
                })

        # ── Burbujas que suben ──
        self.burbujas = []
        for px, py in casillas_px:
            for _ in range(5):
                self.burbujas.append({
                    'x':     float(px + random.randint(5, CELDA - 5)),
                    'y':     float(py + CELDA),
                    'vy':    random.uniform(-1.2, -0.3),
                    'radio': random.randint(2, 6),
                    'alpha': random.uniform(130, 230),
                    'delay': random.randint(15, 70),
                })

        # ── Onda expansiva ──
        self.onda_radio = 0.0
        self.onda_alpha = 255.0
        if casillas_px:
            self.cx = sum(p[0] for p in casillas_px) / len(casillas_px) + CELDA // 2
            self.cy = sum(p[1] for p in casillas_px) / len(casillas_px) + CELDA // 2
        else:
            self.cx, self.cy = 0, 0

    def actualizar(self):
        self.frame += 1
        if self.frame >= self.duracion:
            self.terminado = True
            return

        # Onda expansiva crece y se desvanece
        self.onda_radio += 4.5
        self.onda_alpha = max(0, self.onda_alpha - 5.5)

        # Los fragmentos empiezan a moverse tras el flash
        if self.frame > 12:
            for f in self.fragmentos:
                f['x']     += f['vx']
                f['y']     += f['vy']
                f['vy']    += 0.2          # Gravedad
                f['rot']   += f['vrot']
                f['alpha']  = max(0, f['alpha'] - 2.8)

        # Burbujas suben con un vaivén suave
        for b in self.burbujas:
            if self.frame > b['delay']:
                b['y']     += b['vy']
                b['x']     += math.sin(self.frame * 0.12 + b['x'] * 0.05) * 0.4
                b['alpha']  = max(0, b['alpha'] - 2.0)

    def dibujar(self, pantalla):
        # ── Flash blanco sobre las celdas del barco ──
        if self.frame < 15:
            alpha = int(255 * (1 - self.frame / 15))
            for px, py in self.casillas:
                flash = pygame.Surface((CELDA, CELDA), pygame.SRCALPHA)
                flash.fill((255, 255, 200, alpha))
                pantalla.blit(flash, (px, py))

        # ── Onda expansiva (anillo que crece) ──
        if self.onda_alpha > 5:
            onda_surf = pygame.Surface((ANCHO, ALTO), pygame.SRCALPHA)
            pygame.draw.circle(
                onda_surf,
                (255, 200, 50, int(self.onda_alpha * 0.4)),
                (int(self.cx), int(self.cy)),
                int(self.onda_radio), 3
            )
            pantalla.blit(onda_surf, (0, 0))

        # ── Fragmentos del barco volando ──
        for f in self.fragmentos:
            if f['alpha'] > 5:
                rot_surf = pygame.transform.rotate(f['surf'], f['rot'])
                rot_surf.set_alpha(int(f['alpha']))
                pantalla.blit(rot_surf, (int(f['x']), int(f['y'])))

        # ── Burbujas subiendo ──
        for b in self.burbujas:
            if self.frame > b['delay'] and b['alpha'] > 5:
                bub_surf = pygame.Surface(
                    (b['radio'] * 2 + 4, b['radio'] * 2 + 4), pygame.SRCALPHA
                )
                pygame.draw.circle(
                    bub_surf,
                    (120, 190, 255, int(b['alpha'])),
                    (b['radio'] + 2, b['radio'] + 2),
                    b['radio'], 1
                )
                pantalla.blit(bub_surf, (int(b['x']) - b['radio'],
                                         int(b['y']) - b['radio']))


# ============================================================
# CLASE: BatallaNavalGUI
# Clase principal: ventana, eventos, renderizado, lógica
# ============================================================
class BatallaNavalGUI:
    """
    Orquesta todo el juego: tableros, IA, sprites, animaciones.
    Usa composición: contiene Tablero, JugadorIA, SpriteManager.
    """

    def __init__(self):
        self.pantalla = pygame.display.set_mode((ANCHO, ALTO))
        pygame.display.set_caption('Batalla Naval  |  BattleShip')
        self.reloj = pygame.time.Clock()

        # Fuentes de texto
        self.f_grande = pygame.font.SysFont('Segoe UI', 52, bold=True)
        self.f_med    = pygame.font.SysFont('Segoe UI', 28, bold=True)
        self.f_norm   = pygame.font.SysFont('Segoe UI', 20)
        self.f_small  = pygame.font.SysFont('Segoe UI', 16)
        self.f_celda  = pygame.font.SysFont('Segoe UI', 14, bold=True)
        self.f_mini   = pygame.font.SysFont('Segoe UI', 13)

        # Generador de sprites pixel art
        self.sprite_mgr = SpriteManager()

        self._iniciar_partida()

    # ── Reinicio de partida ──
    def _iniciar_partida(self):
        self.tablero_jug  = Tablero()
        self.ia           = JugadorIA()
        self.estado       = MENU
        self.idx_barco    = 0
        self.dir_h        = True
        self.mouse_celda  = None
        self.turno        = 'jugador'
        self.ronda        = 0
        self.ganador      = None
        self.particulas   = []
        self.animaciones  = []       # Lista de AnimHundimiento activas
        self.esperando_ia = 0
        self.mensaje      = ''
        self.msg_color    = TEXTO
        self.ticks        = 0
        self.sacudida     = 0.0      # Efecto screen shake
        # ── Video de hundimiento ──
        self._video_cap          = None   # Captura de video (cv2.VideoCapture)
        self._video_fps          = 30.0
        self._video_timer        = 0.0    # Tiempo acumulado entre frames
        self._fin_pendiente      = False  # True si el juego termina tras el video
        self._turno_tras_video   = 'ia'   # A qué turno volver tras el video

    # ── Bucle principal del juego ──
    def ejecutar(self):
        while True:
            self.reloj.tick(FPS)
            self.ticks += 1
            self._manejar_eventos()
            self._actualizar()
            self._dibujar()
            pygame.display.flip()

    # ─────────────────────────────
    #  EVENTOS
    # ─────────────────────────────
    def _manejar_eventos(self):
        pos = pygame.mouse.get_pos()

        for ev in pygame.event.get():
            if ev.type == pygame.QUIT:
                pygame.quit(); sys.exit()
            if ev.type == pygame.KEYDOWN:
                if ev.key == pygame.K_ESCAPE:
                    if self.estado == VIDEO:
                        self._terminar_video()  # Skip con ESC
                    else:
                        pygame.quit(); sys.exit()
                if self.estado == COLOCAR and ev.key == pygame.K_r:
                    self.dir_h = not self.dir_h
                if self.estado == VIDEO:
                    self._terminar_video()  # Cualquier tecla salta el video
            if ev.type == pygame.MOUSEBUTTONDOWN:
                if self.estado == VIDEO:
                    self._terminar_video()  # Click salta el video
                elif ev.button == 1:
                    self._click_izq(pos)
                elif ev.button == 3 and self.estado == COLOCAR:
                    self.dir_h = not self.dir_h

        # Detectar celda bajo el cursor
        if self.estado == COLOCAR:
            self.mouse_celda = self._pixel_a_celda(pos, POS_COL)
        elif self.estado == JUGAR and self.turno == 'jugador':
            self.mouse_celda = self._pixel_a_celda(pos, POS_ENE)
        else:
            self.mouse_celda = None

    def _click_izq(self, pos):
        if self.estado == MENU:
            if self._r_btn_jugar().collidepoint(pos):
                self.estado = COLOCAR
                self._msg('Coloca tus barcos  |  Clic derecho o R para rotar', ACENTO)

        elif self.estado == COLOCAR:
            if self._r_btn_auto().collidepoint(pos):
                self._auto_colocar(); return
            if self._r_btn_reset().collidepoint(pos) and self.idx_barco > 0:
                self.tablero_jug = Tablero()
                self.idx_barco = 0
                self._msg('Tablero reiniciado', ACENTO); return
            celda = self._pixel_a_celda(pos, POS_COL)
            if celda and self.idx_barco < len(BARCOS_INFO):
                self._colocar_barco(*celda)

        elif self.estado == JUGAR:
            if self.turno == 'jugador' and self.esperando_ia == 0 and not self.animaciones:
                celda = self._pixel_a_celda(pos, POS_ENE)
                if celda:
                    self._disparar_jugador(*celda)

        elif self.estado == FIN:
            if self._r_btn_reiniciar().collidepoint(pos):
                self._iniciar_partida()
                self.estado = MENU

    # ─────────────────────────────
    #  COLOCACIÓN DE BARCOS
    # ─────────────────────────────
    def _colocar_barco(self, fila, col):
        nombre, tam = BARCOS_INFO[self.idx_barco]
        barco = Barco(nombre, tam)
        if self.tablero_jug.colocar(barco, fila, col, self.dir_h):
            self.idx_barco += 1
            if self.idx_barco >= len(BARCOS_INFO):
                self.estado = JUGAR
                self.ronda  = 0
                self._msg('Todos colocados!  A batallar!', VERDE)
            else:
                sig = BARCOS_INFO[self.idx_barco]
                self._msg(f'Siguiente: {sig[0]} ({sig[1]} celdas)', VERDE)
        else:
            self._msg('No se puede colocar ahi', ROJO_C)

    def _auto_colocar(self):
        while self.idx_barco < len(BARCOS_INFO):
            n, t = BARCOS_INFO[self.idx_barco]
            b = Barco(n, t)
            for _ in range(3000):
                if self.tablero_jug.colocar(
                        b, random.randint(0, 9), random.randint(0, 9),
                        random.choice([True, False])):
                    break
            self.idx_barco += 1
        self.estado = JUGAR
        self.ronda  = 0
        self._msg('Barcos colocados!  A jugar!', VERDE)

    # ─────────────────────────────
    #  DISPARO DEL JUGADOR
    # ─────────────────────────────
    def _disparar_jugador(self, fila, col):
        res  = self.ia.tablero.disparar(fila, col)
        tipo = res['resultado']
        if tipo == 'repetido':
            self._msg('Ya disparaste ahi', GRIS); return

        self.ronda += 1
        cx, cy = self._celda_a_pixel(fila, col, POS_ENE)
        cx += CELDA // 2
        cy += CELDA // 2

        if tipo == 'agua':
            self._emit(cx, cy, FALLO_C, 10, 'normal')
            self._emit(cx, cy, (120, 180, 255), 5, 'burbuja')
            self._msg('Agua... Disparo al mar', FALLO_C)
        elif tipo == 'impacto':
            self._emit(cx, cy, IMPACTO, 20, 'fuego')
            self._emit(cx, cy, C_FUEGO1, 15, 'fuego')
            self.sacudida = 7
            self._msg(f'IMPACTO en el {res["barco"].nombre}!', ACENTO)
        elif tipo == 'hundido':
            self._emit(cx, cy, IMPACTO, 30, 'fuego')
            self._emit(cx, cy, C_FUEGO1, 20, 'fuego')
            self._emit(cx, cy, ACENTO, 12, 'fragmento')
            self.sacudida = 14
            self._msg(f'HUNDISTE el {res["barco"].nombre}!', VERDE)
            self._crear_anim_hundimiento(
                res['barco'], res['casillas'], res['dir_h'], POS_ENE
            )
            # ── Reproducir video por cada barco hundido ──
            if self.ia.tablero.todos_hundidos():
                self.ganador         = 'jugador'
                self._fin_pendiente  = True
            else:
                self._fin_pendiente    = False
                self._turno_tras_video = 'ia'
            self._iniciar_video()
            return

        self.turno        = 'ia'
        self.esperando_ia = 90

    # ─────────────────────────────
    #  TURNO DE LA IA
    # ─────────────────────────────
    def _turno_ia(self):
        f, c = self.ia.elegir_disparo(self.tablero_jug)
        res  = self.tablero_jug.disparar(f, c)
        tipo = res['resultado']
        self.ia.notificar(f, c, tipo)

        cx, cy = self._celda_a_pixel(f, c, POS_JUG)
        cx += CELDA // 2
        cy += CELDA // 2

        if tipo == 'agua':
            self._emit(cx, cy, FALLO_C, 10, 'normal')
            self._msg('La computadora fallo!', VERDE)
        elif tipo == 'impacto':
            self._emit(cx, cy, IMPACTO, 20, 'fuego')
            self._emit(cx, cy, C_FUEGO1, 12, 'fuego')
            self.sacudida = 7
            self._msg(f'Golpearon tu {res["barco"].nombre}!', ROJO_C)
        elif tipo == 'hundido':
            self._emit(cx, cy, IMPACTO, 35, 'fuego')
            self._emit(cx, cy, C_FUEGO1, 20, 'fuego')
            self._emit(cx, cy, ROJO_C, 10, 'fragmento')
            self.sacudida = 14
            self._msg(f'Hundieron tu {res["barco"].nombre}!', ROJO_C)
            self._crear_anim_hundimiento(
                res['barco'], res['casillas'], res['dir_h'], POS_JUG
            )
            # ── Reproducir video por cada barco hundido ──
            if self.tablero_jug.todos_hundidos():
                self.ganador         = 'ia'
                self._fin_pendiente  = True
            else:
                self._fin_pendiente    = False
                self._turno_tras_video = 'jugador'
            self._iniciar_video()
            return

        self.turno = 'jugador'

    # ─────────────────────────────
    #  VIDEO DE FIN DE PARTIDA
    # ─────────────────────────────
    def _iniciar_video(self):
        """Abre el video y cambia el estado a VIDEO para reproducirlo."""
        if CV2_OK and os.path.exists(VIDEO_PATH):
            self._video_cap   = cv2.VideoCapture(VIDEO_PATH)
            self._video_fps   = self._video_cap.get(cv2.CAP_PROP_FPS) or 30.0
            self._video_timer = 0.0
            self.estado       = VIDEO
        else:
            # Sin cv2 o sin video, ir directo al estado FIN
            self.estado = FIN

    def _terminar_video(self):
        """Libera el video. Si fue el último barco va a FIN; si no, continúa el juego."""
        if self._video_cap is not None:
            self._video_cap.release()
            self._video_cap = None
        if self._fin_pendiente:
            self._fin_pendiente = False
            self.estado = FIN
        else:
            self.estado = JUGAR
            self.turno  = self._turno_tras_video
            if self._turno_tras_video == 'ia':
                self.esperando_ia = 90

    def _actualizar_video(self):
        """Avanza al siguiente frame del video según el FPS del clip."""
        if self._video_cap is None:
            self.estado = FIN
            return
        # Avanzar timer; 1 tick = 1 frame de juego (60 fps)
        self._video_timer += 60.0 / self._video_fps
        frames_a_avanzar = int(self._video_timer)
        self._video_timer -= frames_a_avanzar

        frame_surf = None
        for _ in range(max(1, frames_a_avanzar)):
            ok, frame = self._video_cap.read()
            if not ok:
                self._terminar_video()
                return
            frame_surf = frame

        if frame_surf is not None:
            # Convertir BGR (OpenCV) → RGB y crear Surface de pygame
            frame_rgb  = cv2.cvtColor(frame_surf, cv2.COLOR_BGR2RGB)
            h, w       = frame_rgb.shape[:2]
            # Escalar para que quepa en la ventana manteniendo proporción
            escala     = min(ANCHO / w, ALTO / h)
            nw, nh     = int(w * escala), int(h * escala)
            frame_rgb  = cv2.resize(frame_rgb, (nw, nh), interpolation=cv2.INTER_LINEAR)
            self._video_frame = pygame.surfarray.make_surface(
                np.transpose(frame_rgb, (1, 0, 2))
            )
        else:
            self._video_frame = None

    def _dibujar_video(self):
        """Dibuja el frame actual del video centrado en pantalla negra."""
        self.pantalla.fill((0, 0, 0))
        if hasattr(self, '_video_frame') and self._video_frame is not None:
            vw = self._video_frame.get_width()
            vh = self._video_frame.get_height()
            x  = (ANCHO - vw) // 2
            y  = (ALTO  - vh) // 2
            self.pantalla.blit(self._video_frame, (x, y))
        # Texto de skip
        skip_t = self.f_small.render('Presiona cualquier tecla o clic para saltar', True, (160, 160, 160))
        self.pantalla.blit(skip_t, (ANCHO // 2 - skip_t.get_width() // 2, ALTO - 30))

    def _crear_anim_hundimiento(self, barco, casillas, dir_h, origen):
        """Crea la animación de destrucción para el barco hundido."""
        sprites     = self.sprite_mgr.obtener(barco.nombre, dir_h)
        casillas_px = [self._celda_a_pixel(f, c, origen) for f, c in casillas]
        self.animaciones.append(AnimHundimiento(casillas_px, sprites))

    # ─────────────────────────────
    #  ACTUALIZACIÓN
    # ─────────────────────────────
    def _actualizar(self):
        # ── Estado VIDEO: solo avanzar frames ──
        if self.estado == VIDEO:
            self._actualizar_video()
            return

        # Partículas
        self.particulas = [p for p in self.particulas if p.vivo]
        for p in self.particulas:
            p.actualizar()

        # Animaciones de hundimiento
        for a in self.animaciones:
            a.actualizar()
        self.animaciones = [a for a in self.animaciones if not a.terminado]

        # Screen shake se atenúa
        if self.sacudida > 0:
            self.sacudida *= 0.85
            if self.sacudida < 0.5:
                self.sacudida = 0

        # Turno de la IA (espera a que terminen las animaciones)
        if (self.estado == JUGAR and self.turno == 'ia'
                and self.esperando_ia > 0 and not self.animaciones):
            self.esperando_ia -= 1
            if self.esperando_ia == 0:
                self._turno_ia()

    # ─────────────────────────────
    #  RENDERIZADO
    # ─────────────────────────────
    def _dibujar(self):
        self.pantalla.fill(FONDO)

        # Offset de sacudida de pantalla
        sx = int(random.uniform(-self.sacudida, self.sacudida)) if self.sacudida > 0.5 else 0
        sy = int(random.uniform(-self.sacudida, self.sacudida)) if self.sacudida > 0.5 else 0

        self._dibujar_fondo()

        if self.estado == MENU:
            self._dibujar_menu()
        elif self.estado == COLOCAR:
            self._dibujar_colocar()
        elif self.estado == JUGAR:
            self._dibujar_juego(sx, sy)
        elif self.estado == VIDEO:
            self._dibujar_video()
            return  # No dibujar nada más durante el video
        elif self.estado == FIN:
            self._dibujar_juego(sx, sy)
            self._dibujar_fin()

        # Partículas y animaciones siempre encima de todo
        for p in self.particulas:
            p.dibujar(self.pantalla)
        for a in self.animaciones:
            a.dibujar(self.pantalla)

    def _dibujar_fondo(self):
        """Líneas diagonales decorativas animadas."""
        t = self.ticks * 0.3
        for i in range(-5, 25):
            x = int((i * 55 + t) % (ANCHO + 100)) - 50
            pygame.draw.line(self.pantalla, (16, 30, 75), (x, 0), (x + 300, ALTO), 1)

    # ── MENÚ ──
    def _dibujar_menu(self):
        t = self.f_grande.render('BATALLA NAVAL', True, TITULO_C)
        self.pantalla.blit(t, (ANCHO // 2 - t.get_width() // 2, 80))

        sub = self.f_med.render('B A T T L E S H I P', True, ACENTO)
        self.pantalla.blit(sub, (ANCHO // 2 - sub.get_width() // 2, 145))

        pygame.draw.line(self.pantalla, BORDE,
                         (ANCHO // 2 - 280, 188), (ANCHO // 2 + 280, 188))

        # Lista de barcos con sus sprites pixel art
        y0 = 210
        for nombre, tam in BARCOS_INFO:
            tn = self.f_norm.render(nombre, True, TEXTO)
            self.pantalla.blit(tn, (ANCHO // 2 - 260, y0 + 8))

            # Dibujar el sprite pixel art del barco
            sprites = self.sprite_mgr.obtener(nombre, True)
            for i, seg in enumerate(sprites):
                self.pantalla.blit(seg, (ANCHO // 2 - 30 + i * CELDA, y0))

            ts = self.f_small.render(f'{tam} celdas', True, GRIS)
            self.pantalla.blit(ts, (ANCHO // 2 + tam * CELDA, y0 + 10))
            y0 += 52

        # Instrucciones
        inst = [
            'Click izquierdo  ->  Colocar / Disparar',
            'Click derecho  o  R  ->  Rotar barco',
            'ESC  ->  Salir',
        ]
        y0 += 5
        for ln in inst:
            ti = self.f_small.render(ln, True, GRIS)
            self.pantalla.blit(ti, (ANCHO // 2 - ti.get_width() // 2, y0))
            y0 += 22

        self._boton(self._r_btn_jugar(), 'COMENZAR JUEGO', self.f_med)

    # ── COLOCAR ──
    def _dibujar_colocar(self):
        t = self.f_med.render('COLOCA TUS BARCOS', True, TITULO_C)
        self.pantalla.blit(t, (ANCHO // 2 - t.get_width() // 2, 12))

        self._dibujar_tablero(self.tablero_jug, *POS_COL, mostrar_barcos=True)
        self._dibujar_etiquetas(*POS_COL)

        # Preview del barco con el sprite real
        if self.mouse_celda and self.idx_barco < len(BARCOS_INFO):
            nombre, tam = BARCOS_INFO[self.idx_barco]
            f, c     = self.mouse_celda
            valido   = self.tablero_jug.puede_colocar(f, c, tam, self.dir_h)
            casillas = self.tablero_jug._calcular_casillas(f, c, tam, self.dir_h)
            sprites  = self.sprite_mgr.obtener(nombre, self.dir_h)

            if casillas:
                for i, (cf, cc) in enumerate(casillas):
                    if 0 <= cf < FILAS and 0 <= cc < COLS and i < len(sprites):
                        px, py = self._celda_a_pixel(cf, cc, POS_COL)
                        # Sprite semitransparente
                        s_copy = sprites[i].copy()
                        s_copy.set_alpha(180)
                        self.pantalla.blit(s_copy, (px, py))
                        # Overlay verde (válido) o rojo (inválido)
                        ov = pygame.Surface((CELDA, CELDA), pygame.SRCALPHA)
                        ov.fill((50, 255, 100, 35) if valido else (255, 50, 50, 75))
                        self.pantalla.blit(ov, (px, py))

        # Info del barco actual
        if self.idx_barco < len(BARCOS_INFO):
            nombre, tam = BARCOS_INFO[self.idx_barco]
            dir_txt = '-> Horizontal' if self.dir_h else '|  Vertical'
            info = f'{nombre}  ({tam} celdas)   {dir_txt}'
            ti = self.f_norm.render(info, True, ACENTO)
            self.pantalla.blit(ti, (ANCHO // 2 - ti.get_width() // 2, 65))

        # Lista lateral de barcos
        xl, yl = 68, 130
        self.pantalla.blit(self.f_small.render('BARCOS:', True, GRIS), (xl, yl))
        for i, (nb, tam) in enumerate(BARCOS_INFO):
            if   i < self.idx_barco:  col, marca = VERDE, '+'
            elif i == self.idx_barco: col, marca = ACENTO, '>'
            else:                     col, marca = GRIS, 'o'
            ti = self.f_small.render(f'{marca} {nb} ({tam})', True, col)
            self.pantalla.blit(ti, (xl, yl + 24 + i * 26))

        # Botones
        self._boton(self._r_btn_auto(), 'AUTO', self.f_norm)
        if self.idx_barco > 0:
            self._boton(self._r_btn_reset(), 'REINICIAR', self.f_norm)
        self._dibujar_msg()

    # ── JUEGO ──
    def _dibujar_juego(self, sx=0, sy=0):
        t = self.f_med.render(f'RONDA  {self.ronda}', True, ACENTO)
        self.pantalla.blit(t, (ANCHO // 2 - t.get_width() // 2, 8))

        t1 = self.f_norm.render('TU TABLERO', True, VERDE)
        self.pantalla.blit(t1, (POS_JUG[0] + COLS * CELDA // 2 - t1.get_width() // 2 + sx,
                                118 + sy))
        t2 = self.f_norm.render('TABLERO ENEMIGO', True, ROJO_C)
        self.pantalla.blit(t2, (POS_ENE[0] + COLS * CELDA // 2 - t2.get_width() // 2 + sx,
                                105 + sy))

        # Indicador de turno
        if self.estado == JUGAR:
            if self.turno == 'jugador':
                hint, hcol = 'Haz click para disparar', ACENTO
            else:
                hint, hcol = 'Computadora pensando...', GRIS
            th = self.f_small.render(hint, True, hcol)
            self.pantalla.blit(th, (POS_ENE[0] + COLS * CELDA // 2 - th.get_width() // 2, 128))

        # Tableros con offset de sacudida
        jug_pos = (POS_JUG[0] + sx, POS_JUG[1] + sy)
        ene_pos = (POS_ENE[0] + sx, POS_ENE[1] + sy)

        self._dibujar_tablero(self.tablero_jug, *jug_pos, mostrar_barcos=True)
        self._dibujar_etiquetas(*jug_pos)
        self._dibujar_tablero(self.ia.tablero, *ene_pos, mostrar_barcos=False)
        self._dibujar_etiquetas(*ene_pos)

        # Hover pulsante sobre celda enemiga
        if self.estado == JUGAR and self.mouse_celda and self.turno == 'jugador':
            f, c = self.mouse_celda
            if (f, c) not in self.ia.tablero.disparos:
                px, py = self._celda_a_pixel(f, c, ene_pos)
                s = pygame.Surface((CELDA - 2, CELDA - 2), pygame.SRCALPHA)
                alpha = int(128 + 60 * math.sin(self.ticks * 0.15))
                s.fill((255, 255, 255, alpha))
                self.pantalla.blit(s, (px + 1, py + 1))
                # Coordenada sobre la celda
                ct = self.f_mini.render(f'{chr(65 + c)}{f + 1}', True, BLANCO)
                self.pantalla.blit(ct, (px + CELDA // 2 - ct.get_width() // 2,
                                        py + CELDA // 2 - ct.get_height() // 2))

        self._dibujar_panel()
        if self.estado == JUGAR:
            self._dibujar_msg()

    # ── TABLERO (renderizado con sprites) ──
    def _dibujar_tablero(self, tablero, ox, oy, mostrar_barcos):
        """
        Dibuja un tablero completo con agua animada, sprites de barcos,
        fuego en impactos, naufragios para barcos hundidos.
        """
        for f in range(FILAS):
            for c in range(COLS):
                px = ox + c * CELDA
                py = oy + f * CELDA
                estado = tablero.celdas[f][c]
                info   = tablero.mapa[f][c]   # (idx_barco, idx_seg, dir_h)
                rect   = pygame.Rect(px + 1, py + 1, CELDA - 2, CELDA - 2)

                # 1. Fondo de agua con animación de olas
                onda    = int(8 * math.sin(self.ticks * 0.04 + f * 0.5 + c * 0.3))
                col_agua = (AGUA[0], AGUA[1] + onda, min(255, AGUA[2] + onda))
                pygame.draw.rect(self.pantalla, col_agua, rect, border_radius=4)

                # 2. Contenido de la celda
                if estado == 'barco' and mostrar_barcos and info:
                    # ── Barco intacto: dibujar sprite pixel art ──
                    bi, si, dh = info
                    nombre = tablero.barcos[bi]['barco'].nombre
                    sprite = self.sprite_mgr.obtener(nombre, dh)[si]
                    self.pantalla.blit(sprite, (px, py))

                elif estado == 'impacto' and info:
                    bi, si, dh = info
                    barco_obj = tablero.barcos[bi]['barco']
                    nombre    = barco_obj.nombre

                    if barco_obj.hundido:
                        # ── Barco hundido: mostrar naufragio ──
                        nauf = self.sprite_mgr.obtener_naufragio(nombre, dh)[si]
                        self.pantalla.blit(nauf, (px, py))
                    elif mostrar_barcos:
                        # ── Barco dañado (tablero propio): sprite + fuego ──
                        sprite = self.sprite_mgr.obtener(nombre, dh)[si]
                        self.pantalla.blit(sprite, (px, py))
                    else:
                        # ── Tablero enemigo: solo celda roja ──
                        pygame.draw.rect(self.pantalla, IMPACTO, rect, border_radius=4)

                    # Fuego animado sobre celdas impactadas
                    self._dibujar_fuego(px, py, f, c)

                    # Marca X de impacto
                    txt = self.f_celda.render('X', True, BLANCO)
                    self.pantalla.blit(txt, (px + CELDA // 2 - txt.get_width() // 2,
                                            py + CELDA // 2 - txt.get_height() // 2))

                elif estado == 'impacto':
                    # Impacto sin info (fallback)
                    pygame.draw.rect(self.pantalla, IMPACTO, rect, border_radius=4)
                    txt = self.f_celda.render('X', True, BLANCO)
                    self.pantalla.blit(txt, (px + CELDA // 2 - txt.get_width() // 2,
                                            py + CELDA // 2 - txt.get_height() // 2))

                elif estado == 'fallo':
                    # Disparo fallido
                    pygame.draw.rect(self.pantalla, FALLO_C, rect, border_radius=4)
                    pygame.draw.circle(self.pantalla, (150, 180, 220),
                                       (px + CELDA // 2, py + CELDA // 2), 4)

                # 3. Borde de celda
                pygame.draw.rect(self.pantalla, BORDE, rect, 1, border_radius=4)

    def _dibujar_fuego(self, px, py, fila, col):
        """Llamas animadas sobre una celda dañada (determinísticas por posición)."""
        t = self.ticks
        for i in range(4):
            phase = fila * 13 + col * 7 + i * 23
            fx = px + CELDA // 2 + int(8 * math.sin(t * 0.08 + phase))
            fy = py + CELDA // 2 + int(6 * math.cos(t * 0.12 + phase)) - 5
            r  = 3 + int(2 * abs(math.sin(t * 0.15 + phase * 0.5)))
            bright = abs(math.sin(t * 0.1 + phase))
            color  = (255, int(80 + 100 * bright), 0)
            pygame.draw.circle(self.pantalla, color, (fx, fy), max(1, r))
        # Humo encima de las llamas
        for i in range(2):
            phase = fila * 17 + col * 11 + i * 31
            sx = px + CELDA // 2 + int(5 * math.sin(t * 0.05 + phase))
            sy = py + int(10 * abs(math.sin(t * 0.06 + phase)))
            gray = 45 + int(15 * math.sin(t * 0.04 + phase))
            pygame.draw.circle(self.pantalla, (gray, gray, gray + 5), (sx, sy), 4)

    # ── PANEL LATERAL (estado de barcos) ──
    def _dibujar_panel(self):
        bx = POS_ENE[0] + COLS * CELDA + 22
        by = 158

        self.pantalla.blit(self.f_small.render('TUS BARCOS', True, GRIS), (bx, by))
        by += 22
        for e in self.tablero_jug.barcos:
            b = e['barco']
            col = ROJO_C if b.hundido else VERDE
            est = 'Hundido' if b.hundido else f'{b.impactos}/{b.tamano}'
            self.pantalla.blit(self.f_mini.render(b.nombre[:12], True, col), (bx, by))
            self.pantalla.blit(self.f_mini.render(est, True, col), (bx + 115, by))
            by += 20

        by += 18
        self.pantalla.blit(self.f_small.render('ENEMIGOS', True, GRIS), (bx, by))
        by += 22
        for e in self.ia.tablero.barcos:
            b = e['barco']
            col = ROJO_C if b.hundido else GRIS
            est = 'Hundido' if b.hundido else '???'
            self.pantalla.blit(self.f_mini.render(b.nombre[:12], True, col), (bx, by))
            self.pantalla.blit(self.f_mini.render(est, True, col), (bx + 115, by))
            by += 20

    # ── FIN DEL JUEGO ──
    def _dibujar_fin(self):
        overlay = pygame.Surface((ANCHO, ALTO), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 175))
        self.pantalla.blit(overlay, (0, 0))

        caja = pygame.Rect(ANCHO // 2 - 320, ALTO // 2 - 170, 640, 300)
        pygame.draw.rect(self.pantalla, PANEL_C, caja, border_radius=18)
        pygame.draw.rect(self.pantalla, BORDE_H, caja, 2, border_radius=18)

        if self.ganador == 'jugador':
            titulo, col_t = 'GANASTE !!', VERDE
            sub = f'Hundiste todos los barcos en {self.ronda} rondas'
        else:
            titulo, col_t = 'PERDISTE !!', ROJO_C
            sub = f'La computadora gano en {self.ronda} rondas'

        t = self.f_grande.render(titulo, True, col_t)
        self.pantalla.blit(t, (ANCHO // 2 - t.get_width() // 2, ALTO // 2 - 145))
        s = self.f_norm.render(sub, True, TEXTO)
        self.pantalla.blit(s, (ANCHO // 2 - s.get_width() // 2, ALTO // 2 - 70))
        self._boton(self._r_btn_reiniciar(), 'JUGAR DE NUEVO', self.f_med)

    # ── UTILIDADES DE DIBUJO ──
    def _dibujar_etiquetas(self, ox, oy):
        for i, l in enumerate('ABCDEFGHIJ'):
            t = self.f_celda.render(l, True, GRIS)
            self.pantalla.blit(t, (ox + i * CELDA + CELDA // 2 - t.get_width() // 2, oy - 20))
        for i in range(FILAS):
            t = self.f_celda.render(str(i + 1), True, GRIS)
            self.pantalla.blit(t, (ox - 24, oy + i * CELDA + CELDA // 2 - t.get_height() // 2))

    def _dibujar_msg(self):
        if self.mensaje:
            t = self.f_norm.render(self.mensaje, True, self.msg_color)
            self.pantalla.blit(t, (ANCHO // 2 - t.get_width() // 2, ALTO - 36))

    def _boton(self, rect, texto, fuente):
        hover = rect.collidepoint(pygame.mouse.get_pos())
        col = BTN_H if hover else BTN
        pygame.draw.rect(self.pantalla, col, rect, border_radius=12)
        pygame.draw.rect(self.pantalla, BORDE_H if hover else BORDE, rect, 2, border_radius=12)
        t = fuente.render(texto, True, BTN_T)
        self.pantalla.blit(t, (rect.centerx - t.get_width() // 2,
                               rect.centery - t.get_height() // 2))

    # ── CONVERSIONES DE COORDENADAS ──
    def _celda_a_pixel(self, f, c, origen):
        return (origen[0] + c * CELDA, origen[1] + f * CELDA)

    def _pixel_a_celda(self, pos, origen):
        c = (pos[0] - origen[0]) // CELDA
        f = (pos[1] - origen[1]) // CELDA
        if 0 <= f < FILAS and 0 <= c < COLS:
            return (f, c)
        return None

    def _emit(self, x, y, color, n, tipo='normal'):
        for _ in range(n):
            self.particulas.append(Particula(x, y, color, tipo))

    def _msg(self, texto, color=TEXTO):
        self.mensaje   = texto
        self.msg_color = color

    # ── RECTÁNGULOS DE BOTONES ──
    def _r_btn_jugar(self):
        return pygame.Rect(ANCHO // 2 - 115, ALTO - 135, 230, 58)
    def _r_btn_auto(self):
        return pygame.Rect(80, ALTO - 68, 145, 44)
    def _r_btn_reset(self):
        return pygame.Rect(242, ALTO - 68, 165, 44)
    def _r_btn_reiniciar(self):
        return pygame.Rect(ANCHO // 2 - 145, ALTO // 2 + 55, 290, 58)


# ============================================================
# PUNTO DE ENTRADA
# ============================================================
if __name__ == '__main__':
    juego = BatallaNavalGUI()
    juego.ejecutar()
