# -*- coding: utf-8 -*-
"""
====================================================
  BATALLA NAVAL - VERSIÓN GRÁFICA CON PYGAME
  Librería requerida: pip install pygame-ce
  Python 3.x

  Controles:
    - Click izquierdo  → Colocar barco / Disparar
    - Click derecho    → Rotar barco (al colocarlo)
    - Tecla R          → Rotar barco (al colocarlo)
    - ESC              → Salir

  Conceptos de POO:
    - Clases y Objetos
    - Herencia  (JugadorIA hereda de la lógica de Jugador)
    - Encapsulamiento (métodos privados con _)
    - Composición (BatallaNavalGUI contiene Tablero y JugadorIA)
====================================================
"""

import pygame   # Librería para gráficos, eventos y ventana
import sys      # Para cerrar el programa correctamente
import random   # Para posiciones y disparos aleatorios de la IA
import math     # Para cálculos matemáticos en animaciones

# ─────────────────────────────────────────────────────
#  INICIALIZACIÓN DE PYGAME
#  Siempre se debe llamar pygame.init() antes de usar
#  cualquier función de la librería.
# ─────────────────────────────────────────────────────
pygame.init()

# ── Dimensiones de la ventana ──
ANCHO = 1200
ALTO  = 720

# ── Tamaño en píxeles de cada celda del tablero ──
CELDA = 44
FILAS = 10
COLS  = 10

# ── Cuántos fotogramas por segundo (velocidad del juego) ──
FPS = 60

# ── Posición de inicio de cada tablero en pantalla ──
POS_JUG = (52, 160)    # Tablero del jugador (izquierda)
POS_ENE = (645, 160)   # Tablero del enemigo (derecha)

# ─────────────────────────────────────────────────────
#  PALETA DE COLORES (formato RGB: rojo, verde, azul)
#  Cada valor va de 0 a 255
# ─────────────────────────────────────────────────────
FONDO      = (8,   15,  40)    # Fondo oscuro de la pantalla
PANEL      = (12,  28,  68)    # Panel lateral
AGUA       = (18,  58, 138)    # Color de celdas vacías
AGUA_H     = (38, 108, 218)    # Agua con hover (mouse encima)
BARCO_OK   = (38, 172,  88)    # Barco colocado correctamente (verde)
BARCO_H    = (58, 215, 118)    # Preview válido de barco
BARCO_MAL  = (205,  55,  55)   # Preview inválido (rojo)
IMPACTO    = (228,  58,  48)   # Celda con impacto (X)
FALLO_C    = (72,  132, 198)   # Celda con disparo fallido
BORDE      = (28,  68, 158)    # Borde de celdas
BORDE_H    = (78, 158, 255)    # Borde activo/hover
TEXTO      = (205, 228, 255)   # Color de texto general
TITULO_C   = (92,  195, 255)   # Color de títulos
ACENTO     = (255, 202,  48)   # Color de acento (amarillo dorado)
BLANCO     = (255, 255, 255)
GRIS       = (112, 125, 152)   # Texto secundario
VERDE      = (45,  198, 102)   # Mensajes de éxito
ROJO_C     = (222,  48,  48)   # Mensajes de error/peligro
BTN        = (22,  58, 138)    # Botón normal
BTN_H      = (48, 108, 218)    # Botón con hover
BTN_T      = (195, 225, 255)   # Texto del botón
NEGRO      = (0,     0,   0)

# ─────────────────────────────────────────────────────
#  CONSTANTES DE ESTADO DEL JUEGO
#  El juego tiene 4 pantallas/estados diferentes
# ─────────────────────────────────────────────────────
MENU    = 'menu'      # Pantalla de bienvenida
COLOCAR = 'colocar'  # Fase de colocación de barcos
JUGAR   = 'jugar'    # Fase de batalla
FIN     = 'fin'      # Pantalla de fin de juego


# ============================================================
# CLASE: Barco
# Representa un barco del tablero
# ============================================================
class Barco:
    """
    Clase que modela un barco del juego.

    Atributos:
        nombre   : Nombre del barco (ej. "Portaaviones")
        tamano   : Cuántas celdas ocupa
        impactos : Cuántos impactos ha recibido
        hundido  : True si ya fue hundido
    """

    def __init__(self, nombre, tamano):
        """
        Constructor: se llama al crear un nuevo Barco.

        Parámetros:
            nombre : str  → Nombre del barco
            tamano : int  → Número de celdas que ocupa
        """
        self.nombre   = nombre
        self.tamano   = tamano
        self.impactos = 0       # Empieza sin impactos
        self.hundido  = False   # Al inicio no está hundido

    def recibir_impacto(self):
        """
        Registra un impacto en el barco.
        Si los impactos alcanzan el tamaño, el barco se hunde.

        Retorna:
            True  si el barco se hundió con este impacto
            False si sigue a flote
        """
        self.impactos += 1
        if self.impactos >= self.tamano:
            self.hundido = True
            return True
        return False

    def __str__(self):
        """Representación en texto del barco."""
        return f"{self.nombre} ({self.tamano} celdas)"


# ============================================================
# CLASE: Tablero
# Cuadrícula 10x10 con lógica del juego
# ============================================================
class Tablero:
    """
    Tablero de juego de 10x10 celdas.

    Cada celda puede estar en uno de estos estados:
        'agua'    → Celda vacía
        'barco'   → Ocupada por un barco
        'impacto' → Barco golpeado
        'fallo'   → Disparo al agua
    """

    def __init__(self):
        """Constructor: crea una cuadrícula vacía de 10x10."""
        # Lista de listas (matriz 2D): 10 filas, cada una con 10 celdas 'agua'
        self.celdas   = [['agua'] * COLS for _ in range(FILAS)]

        # Lista de diccionarios: {'barco': Barco, 'casillas': [(f,c), ...]}
        self.barcos   = []

        # Conjunto de coordenadas ya disparadas (evita repetir)
        self.disparos = set()

    def _calcular_casillas(self, fila, col, tamano, dir_h):
        """
        Calcula las celdas que ocuparía un barco.

        Parámetros:
            fila, col : Celda inicial
            tamano    : Tamaño del barco
            dir_h     : True=Horizontal, False=Vertical

        Retorna:
            Lista de tuplas (fila, col) o None si sale del tablero
        """
        casillas = []
        for i in range(tamano):
            f = fila + (0 if dir_h else i)  # Si es vertical, incrementa fila
            c = col  + (i if dir_h else 0)  # Si es horizontal, incrementa columna

            # Verificamos que la celda esté dentro del tablero
            if not (0 <= f < FILAS and 0 <= c < COLS):
                return None  # Fuera del tablero
            casillas.append((f, c))
        return casillas

    def puede_colocar(self, fila, col, tamano, dir_h):
        """
        Verifica si se puede colocar un barco sin solapar ni salirse.

        Retorna:
            True  si es una posición válida
            False si no se puede colocar
        """
        casillas = self._calcular_casillas(fila, col, tamano, dir_h)
        if casillas is None:
            return False  # Sale del tablero

        for f, c in casillas:
            if self.celdas[f][c] != 'agua':
                return False  # Ya hay algo en esa celda
        return True

    def colocar(self, barco, fila, col, dir_h):
        """
        Coloca el barco en el tablero.

        Retorna:
            True  si se colocó correctamente
            False si hubo un error
        """
        casillas = self._calcular_casillas(fila, col, barco.tamano, dir_h)
        if casillas is None:
            return False

        for f, c in casillas:
            if self.celdas[f][c] != 'agua':
                return False

        # Marcamos todas las celdas del barco
        for f, c in casillas:
            self.celdas[f][c] = 'barco'

        # Guardamos el barco y sus casillas para registrar impactos
        self.barcos.append({'barco': barco, 'casillas': casillas})
        return True

    def disparar(self, fila, col):
        """
        Procesa un disparo en la celda indicada.

        Retorna:
            Diccionario con:
              'resultado' : 'agua', 'impacto', 'hundido' o 'repetido'
              'barco'     : Objeto Barco si hubo impacto (o None)
        """
        coord = (fila, col)

        if coord in self.disparos:
            return {'resultado': 'repetido', 'barco': None}

        self.disparos.add(coord)

        # Revisamos si el disparo golpeó algún barco
        for entrada in self.barcos:
            if coord in entrada['casillas']:
                barco   = entrada['barco']
                hundido = barco.recibir_impacto()
                self.celdas[fila][col] = 'impacto'
                resultado = 'hundido' if hundido else 'impacto'
                return {'resultado': resultado, 'barco': barco}

        # No golpeó ningún barco
        self.celdas[fila][col] = 'fallo'
        return {'resultado': 'agua', 'barco': None}

    def todos_hundidos(self):
        """Retorna True si todos los barcos están hundidos."""
        return all(e['barco'].hundido for e in self.barcos)


# ============================================================
# CLASE: JugadorIA
# Inteligencia Artificial con estrategia de ataque
# ============================================================
class JugadorIA:
    """
    IA del juego con dos modos de disparo:
      - BUSCAR : Dispara en celdas aleatorias
      - ATACAR : Cuando da un impacto, sigue atacando alrededor

    Atributos:
        tablero    : El tablero de la IA (donde están sus barcos)
        modo       : 'buscar' o 'atacar'
        pendientes : Lista de celdas a atacar próximamente
    """

    # Información de todos los barcos del juego (nombre, tamaño)
    BARCOS_INFO = [
        ('Portaaviones', 5),
        ('Acorazado',    4),
        ('Crucero',      3),
        ('Submarino',    3),
        ('Destructor',   2),
    ]

    def __init__(self):
        """Constructor: crea el tablero de la IA y coloca los barcos."""
        self.tablero    = Tablero()
        self.modo       = 'buscar'   # Empieza buscando
        self.pendientes = []         # Lista vacía de celdas pendientes
        self._colocar_barcos()       # Coloca todos los barcos automáticamente

    def _colocar_barcos(self):
        """Coloca todos los barcos en posiciones aleatorias."""
        for nombre, tam in self.BARCOS_INFO:
            barco    = Barco(nombre, tam)
            colocado = False
            while not colocado:
                f     = random.randint(0, 9)
                c     = random.randint(0, 9)
                dir_h = random.choice([True, False])
                colocado = self.tablero.colocar(barco, f, c, dir_h)

    def elegir_disparo(self, tablero_jugador):
        """
        Decide dónde disparar según la estrategia actual.

        Parámetros:
            tablero_jugador : El tablero del humano (donde disparará)

        Retorna:
            Tupla (fila, col) con la coordenada elegida
        """
        ya_disparados = tablero_jugador.disparos

        # Si está en modo ATACAR y hay celdas pendientes
        if self.modo == 'atacar' and self.pendientes:
            while self.pendientes:
                f, c = self.pendientes.pop(0)
                if (f, c) not in ya_disparados:
                    return (f, c)

        # Si no hay pendientes, volvemos a buscar aleatoriamente
        self.modo = 'buscar'
        while True:
            f = random.randint(0, 9)
            c = random.randint(0, 9)
            if (f, c) not in ya_disparados:
                return (f, c)

    def notificar(self, fila, col, resultado):
        """
        Recibe el resultado del último disparo y ajusta la estrategia.

        Parámetros:
            fila, col : Coordenadas del disparo
            resultado : 'agua', 'impacto' o 'hundido'
        """
        if resultado == 'impacto':
            # ¡Impacto! Cambiamos a modo ataque
            self.modo = 'atacar'
            # Agregamos las 4 celdas adyacentes a la lista de pendientes
            adyacentes = [(-1, 0), (1, 0), (0, -1), (0, 1)]
            for df, dc in adyacentes:
                nf, nc = fila + df, col + dc
                if 0 <= nf < 10 and 0 <= nc < 10:
                    if (nf, nc) not in self.tablero.disparos:
                        if (nf, nc) not in self.pendientes:
                            self.pendientes.append((nf, nc))

        elif resultado == 'hundido':
            # Barco hundido: reiniciamos el modo
            self.modo       = 'buscar'
            self.pendientes = []


# ============================================================
# CLASE: Particula
# Efecto visual de explosión al disparar
# ============================================================
class Particula:
    """
    Pequeña partícula que crea efectos de explosión o salpicadura.
    Tiene posición, velocidad, vida y color.
    """

    def __init__(self, x, y, color):
        """
        Constructor de la partícula.

        Parámetros:
            x, y  : Posición inicial en píxeles
            color : Tupla RGB del color
        """
        self.x     = float(x)
        self.y     = float(y)
        self.vx    = random.uniform(-4.5, 4.5)   # Velocidad horizontal
        self.vy    = random.uniform(-7.0, -1.0)  # Velocidad vertical (sube)
        self.vida  = random.randint(20, 45)       # Cuántos frames dura
        self.vida_max = self.vida
        self.radio = random.randint(2, 6)         # Tamaño de la partícula
        self.color = color

    def actualizar(self):
        """Actualiza la posición y vida de la partícula cada frame."""
        self.x    += self.vx
        self.y    += self.vy
        self.vy   += 0.35   # Gravedad: la jala hacia abajo
        self.vida -= 1

    def dibujar(self, superficie):
        """Dibuja la partícula en la superficie de pygame."""
        # La partícula se desvanece al final de su vida (efecto fade)
        alfa = self.vida / self.vida_max
        r, g, b = self.color
        color_actual = (int(r * alfa), int(g * alfa), int(b * alfa))
        radio_actual = max(1, int(self.radio * alfa))
        pygame.draw.circle(superficie, color_actual,
                           (int(self.x), int(self.y)), radio_actual)

    @property
    def vivo(self):
        """Propiedad que indica si la partícula sigue activa."""
        return self.vida > 0


# ============================================================
# CLASE: BatallaNavalGUI
# Clase principal del juego gráfico
# ============================================================
class BatallaNavalGUI:
    """
    Clase principal que maneja la ventana de pygame,
    los eventos del mouse/teclado y el renderizado visual.

    Contiene (Composición):
      - tablero_jug : Tablero del jugador humano
      - ia          : Objeto JugadorIA con su propio tablero
      - particulas  : Lista de efectos visuales
    """

    # Lista de barcos del juego (clase compartida por todos)
    BARCOS_INFO = [
        ('Portaaviones', 5),
        ('Acorazado',    4),
        ('Crucero',      3),
        ('Submarino',    3),
        ('Destructor',   2),
    ]

    def __init__(self):
        """Constructor: crea la ventana y los objetos del juego."""

        # Creamos la ventana con el tamaño definido
        self.pantalla = pygame.display.set_mode((ANCHO, ALTO))
        pygame.display.set_caption('Batalla Naval  |  BattleShip')

        # Reloj para controlar los FPS (fotogramas por segundo)
        self.reloj = pygame.time.Clock()

        # Fuentes de texto en diferentes tamaños
        self.f_grande = pygame.font.SysFont('Segoe UI', 52, bold=True)
        self.f_med    = pygame.font.SysFont('Segoe UI', 28, bold=True)
        self.f_norm   = pygame.font.SysFont('Segoe UI', 20)
        self.f_small  = pygame.font.SysFont('Segoe UI', 16)
        self.f_celda  = pygame.font.SysFont('Segoe UI', 14, bold=True)
        self.f_mini   = pygame.font.SysFont('Segoe UI', 13)

        # Iniciamos la primera partida
        self._iniciar_partida()

    # ────────────────────────────────────
    #  INICIALIZACIÓN DE PARTIDA
    # ────────────────────────────────────
    def _iniciar_partida(self):
        """
        Inicializa (o reinicia) todos los datos de la partida.
        Se llama al inicio y cuando el jugador quiere jugar de nuevo.
        """
        self.tablero_jug   = Tablero()   # Tablero del jugador
        self.ia            = JugadorIA() # IA con su tablero ya colocado

        self.estado        = MENU        # Empieza en el menú
        self.idx_barco     = 0           # Índice del barco que se está colocando
        self.dir_h         = True        # Dirección: True=Horizontal, False=Vertical
        self.mouse_celda   = None        # Celda bajo el cursor del mouse
        self.turno         = 'jugador'   # De quién es el turno
        self.ronda         = 0           # Contador de rondas
        self.ganador       = None        # Quién ganó ('jugador' o 'ia')
        self.particulas    = []          # Lista de partículas activas
        self.esperando_ia  = 0           # Delay del turno de la IA (en frames)
        self.mensaje       = ''          # Texto del mensaje de estado
        self.msg_color     = TEXTO       # Color del mensaje
        self.ticks         = 0           # Contador de frames (para animaciones)

    # ────────────────────────────────────
    #  BUCLE PRINCIPAL DEL JUEGO
    # ────────────────────────────────────
    def ejecutar(self):
        """
        Bucle principal (game loop).
        Se ejecuta continuamente hasta que el jugador cierra la ventana.
        Cada iteración del ciclo es un fotograma.
        """
        while True:
            self.reloj.tick(FPS)        # Limitamos a 60 FPS
            self.ticks += 1             # Incrementamos el contador de frames

            self._manejar_eventos()     # Procesamos inputs del usuario
            self._actualizar()          # Actualizamos la lógica
            self._dibujar()             # Dibujamos todo en pantalla
            pygame.display.flip()       # Mostramos el frame dibujado

    # ────────────────────────────────────
    #  MANEJO DE EVENTOS
    # ────────────────────────────────────
    def _manejar_eventos(self):
        """
        Lee y procesa todos los eventos del sistema
        (cierre de ventana, teclado, mouse).
        """
        pos_mouse = pygame.mouse.get_pos()  # Posición actual del cursor

        for evento in pygame.event.get():

            # ── Cierre de ventana ──
            if evento.type == pygame.QUIT:
                pygame.quit()
                sys.exit()

            # ── Teclado ──
            if evento.type == pygame.KEYDOWN:
                if evento.key == pygame.K_ESCAPE:
                    pygame.quit()
                    sys.exit()
                # Tecla R: rotar barco durante la colocación
                if self.estado == COLOCAR and evento.key == pygame.K_r:
                    self.dir_h = not self.dir_h

            # ── Clicks del mouse ──
            if evento.type == pygame.MOUSEBUTTONDOWN:
                if evento.button == 1:        # Botón izquierdo
                    self._click_izq(pos_mouse)
                elif evento.button == 3:      # Botón derecho → rotar
                    if self.estado == COLOCAR:
                        self.dir_h = not self.dir_h

        # Actualizamos la celda bajo el cursor según el estado
        if self.estado == COLOCAR:
            self.mouse_celda = self._pixel_a_celda(pos_mouse, POS_JUG)
        elif self.estado == JUGAR and self.turno == 'jugador':
            self.mouse_celda = self._pixel_a_celda(pos_mouse, POS_ENE)
        else:
            self.mouse_celda = None

    def _click_izq(self, pos):
        """
        Procesa el click izquierdo dependiendo del estado del juego.
        """
        # ── MENÚ: botón Jugar ──
        if self.estado == MENU:
            if self._r_btn_jugar().collidepoint(pos):
                self.estado = COLOCAR
                self._mensaje('Coloca tus barcos  |  Clic derecho o R para rotar', ACENTO)

        # ── COLOCAR: colocar barcos con el mouse ──
        elif self.estado == COLOCAR:
            if self._r_btn_auto().collidepoint(pos):
                self._auto_colocar()
                return
            if self._r_btn_reset().collidepoint(pos) and self.idx_barco > 0:
                self.tablero_jug = Tablero()
                self.idx_barco   = 0
                self._mensaje('Tablero reiniciado', ACENTO)
                return
            # Clic en el tablero
            celda = self._pixel_a_celda(pos, POS_JUG)
            if celda and self.idx_barco < len(self.BARCOS_INFO):
                self._colocar_barco(*celda)

        # ── JUGAR: disparar ──
        elif self.estado == JUGAR:
            if self.turno == 'jugador' and self.esperando_ia == 0:
                celda = self._pixel_a_celda(pos, POS_ENE)
                if celda:
                    self._disparar_jugador(*celda)

        # ── FIN: botón jugar de nuevo ──
        elif self.estado == FIN:
            if self._r_btn_reiniciar().collidepoint(pos):
                self._iniciar_partida()
                self.estado = MENU

    # ────────────────────────────────────
    #  LÓGICA DE COLOCACIÓN DE BARCOS
    # ────────────────────────────────────
    def _colocar_barco(self, fila, col):
        """Intenta colocar el barco actual en la celda (fila, col)."""
        nombre, tam = self.BARCOS_INFO[self.idx_barco]
        barco = Barco(nombre, tam)

        if self.tablero_jug.colocar(barco, fila, col, self.dir_h):
            self.idx_barco += 1
            if self.idx_barco >= len(self.BARCOS_INFO):
                # Todos los barcos colocados: comenzamos la batalla
                self.estado = JUGAR
                self.ronda  = 0
                self._mensaje('¡Todos colocados! ¡Que comience la batalla!', VERDE)
            else:
                sig_n, sig_t = self.BARCOS_INFO[self.idx_barco]
                self._mensaje(f'¡Colocado! Siguiente: {sig_n} ({sig_t} celdas)', VERDE)
        else:
            self._mensaje('No se puede colocar ahí. Intenta otro lugar.', ROJO_C)

    def _auto_colocar(self):
        """Coloca todos los barcos restantes de forma aleatoria automática."""
        while self.idx_barco < len(self.BARCOS_INFO):
            nombre, tam = self.BARCOS_INFO[self.idx_barco]
            barco    = Barco(nombre, tam)
            colocado = False
            intentos = 0
            while not colocado and intentos < 2000:
                f     = random.randint(0, 9)
                c     = random.randint(0, 9)
                dh    = random.choice([True, False])
                colocado = self.tablero_jug.colocar(barco, f, c, dh)
                intentos += 1
            if colocado:
                self.idx_barco += 1

        if self.idx_barco >= len(self.BARCOS_INFO):
            self.estado = JUGAR
            self.ronda  = 0
            self._mensaje('¡Barcos colocados automáticamente! ¡A jugar!', VERDE)

    # ────────────────────────────────────
    #  LÓGICA DE DISPARO
    # ────────────────────────────────────
    def _disparar_jugador(self, fila, col):
        """Procesa el disparo del jugador en el tablero de la IA."""
        res  = self.ia.tablero.disparar(fila, col)
        tipo = res['resultado']

        if tipo == 'repetido':
            self._mensaje('Ya disparaste ahí. Elige otra celda.', GRIS)
            return

        self.ronda += 1
        # Calculamos el centro de la celda para las partículas
        cx, cy = self._celda_a_pixel(fila, col, POS_ENE)
        cx += CELDA // 2
        cy += CELDA // 2

        if tipo == 'agua':
            self._emit_particulas(cx, cy, FALLO_C, 10)
            self._mensaje('Agua... Tu disparo cayó al mar.', FALLO_C)
        elif tipo == 'impacto':
            self._emit_particulas(cx, cy, IMPACTO, 22)
            self._mensaje(f'IMPACTO en el {res["barco"].nombre}!', ACENTO)
        elif tipo == 'hundido':
            self._emit_particulas(cx, cy, IMPACTO, 38)
            self._emit_particulas(cx, cy, ACENTO, 18)
            self._mensaje(f'HUNDISTE el {res["barco"].nombre}!', VERDE)

        # ¿Ganó el jugador?
        if self.ia.tablero.todos_hundidos():
            self.ganador = 'jugador'
            self.estado  = FIN
            return

        # Pasamos el turno a la IA (con delay de ~1.5 s)
        self.turno        = 'ia'
        self.esperando_ia = 90
        self._mensaje('La computadora está pensando...', GRIS)

    def _turno_ia(self):
        """Ejecuta el disparo de la IA en el tablero del jugador."""
        fila, col = self.ia.elegir_disparo(self.tablero_jug)
        res  = self.tablero_jug.disparar(fila, col)
        tipo = res['resultado']
        self.ia.notificar(fila, col, tipo)

        cx, cy = self._celda_a_pixel(fila, col, POS_JUG)
        cx += CELDA // 2
        cy += CELDA // 2

        if tipo == 'agua':
            self._emit_particulas(cx, cy, FALLO_C, 10)
            self._mensaje('La computadora falló. ¡Al agua!', VERDE)
        elif tipo == 'impacto':
            self._emit_particulas(cx, cy, IMPACTO, 22)
            self._mensaje(f'¡La compu golpeó tu {res["barco"].nombre}!', ROJO_C)
        elif tipo == 'hundido':
            self._emit_particulas(cx, cy, IMPACTO, 38)
            self._mensaje(f'¡La compu hundió tu {res["barco"].nombre}!', ROJO_C)

        # ¿Ganó la IA?
        if self.tablero_jug.todos_hundidos():
            self.ganador = 'ia'
            self.estado  = FIN
            return

        self.turno = 'jugador'

    # ────────────────────────────────────
    #  ACTUALIZACIÓN LÓGICA
    # ────────────────────────────────────
    def _actualizar(self):
        """
        Actualiza la lógica del juego cada frame.
        Se llama 60 veces por segundo.
        """
        # Actualizar y limpiar partículas muertas
        self.particulas = [p for p in self.particulas if p.vivo]
        for p in self.particulas:
            p.actualizar()

        # Temporizador del turno de la IA
        if self.estado == JUGAR and self.turno == 'ia' and self.esperando_ia > 0:
            self.esperando_ia -= 1
            if self.esperando_ia == 0:
                self._turno_ia()

    # ────────────────────────────────────
    #  RENDERIZADO (DIBUJO)
    # ────────────────────────────────────
    def _dibujar(self):
        """Dibuja todos los elementos visuales en pantalla."""
        self.pantalla.fill(FONDO)          # Fondo oscuro
        self._dibujar_fondo()              # Líneas decorativas

        # Cada estado tiene su propia pantalla
        if self.estado == MENU:
            self._dibujar_menu()
        elif self.estado == COLOCAR:
            self._dibujar_colocar()
        elif self.estado == JUGAR:
            self._dibujar_juego()
        elif self.estado == FIN:
            self._dibujar_juego()          # El juego de fondo
            self._dibujar_fin()            # Overlay de fin encima

        # Las partículas van siempre en el frente
        for p in self.particulas:
            p.dibujar(self.pantalla)

    def _dibujar_fondo(self):
        """Dibuja líneas diagonales decorativas en el fondo."""
        t = self.ticks * 0.3
        for i in range(-5, 25):
            x = int((i * 55 + t) % (ANCHO + 100)) - 50
            pygame.draw.line(self.pantalla, (16, 30, 75),
                             (x, 0), (x + 300, ALTO), 1)

    # ── MENÚ ──────────────────────────────
    def _dibujar_menu(self):
        """Pantalla de bienvenida con título y botón de inicio."""

        # Título principal
        t = self.f_grande.render('BATALLA NAVAL', True, TITULO_C)
        self.pantalla.blit(t, (ANCHO//2 - t.get_width()//2, 95))

        sub = self.f_med.render('B A T T L E S H I P', True, ACENTO)
        self.pantalla.blit(sub, (ANCHO//2 - sub.get_width()//2, 162))

        # Línea separadora
        pygame.draw.line(self.pantalla, BORDE,
                         (ANCHO//2 - 280, 205), (ANCHO//2 + 280, 205), 1)

        # Lista de barcos con representación visual
        info_barcos = [
            ('Portaaviones', 5, BARCO_OK),
            ('Acorazado',    4, (50, 190, 100)),
            ('Crucero',      3, (65, 205, 115)),
            ('Submarino',    3, (80, 180, 90)),
            ('Destructor',   2, (95, 195, 105)),
        ]
        y0 = 225
        bw = 28   # Ancho de cada bloque visual
        for nombre, tam, color in info_barcos:
            # Nombre del barco
            tn = self.f_norm.render(nombre, True, TEXTO)
            self.pantalla.blit(tn, (ANCHO//2 - 240, y0))
            # Bloques de color que representan el tamaño
            for b in range(tam):
                r = pygame.Rect(ANCHO//2 - 20 + b * (bw + 3), y0 + 2, bw, 20)
                pygame.draw.rect(self.pantalla, color, r, border_radius=4)
            # Texto del tamaño
            ts = self.f_small.render(f'{tam} celdas', True, GRIS)
            self.pantalla.blit(ts, (ANCHO//2 + 165, y0 + 2))
            y0 += 38

        # Instrucciones de control
        inst = [
            'Click izquierdo → Colocar barco / Disparar',
            'Click derecho  o  R → Rotar barco',
            'ESC → Salir del juego',
        ]
        y0 += 15
        for ln in inst:
            ti = self.f_small.render(ln, True, GRIS)
            self.pantalla.blit(ti, (ANCHO//2 - ti.get_width()//2, y0))
            y0 += 24

        # Botón de inicio
        self._boton(self._r_btn_jugar(), 'COMENZAR JUEGO', self.f_med)

    # ── COLOCAR ───────────────────────────
    def _dibujar_colocar(self):
        """Pantalla de colocación manual de barcos."""

        # Título
        t = self.f_med.render('COLOCA TUS BARCOS', True, TITULO_C)
        self.pantalla.blit(t, (ANCHO//2 - t.get_width()//2, 12))

        # Tablero del jugador (centrado horizontalmente)
        ox, oy = 365, 108
        self._dibujar_tablero(self.tablero_jug, ox, oy, mostrar_barcos=True)
        self._dibujar_etiquetas(ox, oy)

        # Preview del barco mientras el mouse está sobre el tablero
        if self.mouse_celda and self.idx_barco < len(self.BARCOS_INFO):
            nombre, tam = self.BARCOS_INFO[self.idx_barco]
            f, c = self.mouse_celda
            valido    = self.tablero_jug.puede_colocar(f, c, tam, self.dir_h)
            col_prev  = BARCO_H if valido else BARCO_MAL
            casillas  = self.tablero_jug._calcular_casillas(f, c, tam, self.dir_h)
            if casillas:
                for cf, cc in casillas:
                    if 0 <= cf < FILAS and 0 <= cc < COLS:
                        px, py = self._celda_a_pixel(cf, cc, (ox, oy))
                        s = pygame.Surface((CELDA - 2, CELDA - 2), pygame.SRCALPHA)
                        s.fill((*col_prev, 180))
                        self.pantalla.blit(s, (px + 1, py + 1))

        # Info del barco actual
        if self.idx_barco < len(self.BARCOS_INFO):
            nombre, tam = self.BARCOS_INFO[self.idx_barco]
            dir_txt = '→ Horizontal' if self.dir_h else '↓ Vertical'
            info = f'Colocando:  {nombre}  ({tam} celdas)    |    Dirección: {dir_txt}'
            ti   = self.f_norm.render(info, True, ACENTO)
            self.pantalla.blit(ti, (ANCHO//2 - ti.get_width()//2, 75))
        else:
            ti = self.f_norm.render('¡Todos los barcos colocados!', True, VERDE)
            self.pantalla.blit(ti, (ANCHO//2 - ti.get_width()//2, 75))

        # Lista lateral de barcos
        xl, yl = 75, 125
        th = self.f_small.render('BARCOS:', True, GRIS)
        self.pantalla.blit(th, (xl, yl))
        for i, (nb, tam) in enumerate(self.BARCOS_INFO):
            if i < self.idx_barco:
                col_item, marca = VERDE, '✓'
            elif i == self.idx_barco:
                col_item, marca = ACENTO, '▶'
            else:
                col_item, marca = GRIS, '○'
            ti = self.f_small.render(f'{marca}  {nb}  ({tam})', True, col_item)
            self.pantalla.blit(ti, (xl, yl + 24 + i * 26))

        # Botones
        self._boton(self._r_btn_auto(), 'AUTO', self.f_norm)
        if self.idx_barco > 0:
            self._boton(self._r_btn_reset(), 'REINICIAR', self.f_norm)

        self._dibujar_msg()

    # ── JUEGO ─────────────────────────────
    def _dibujar_juego(self):
        """Pantalla principal de batalla con los dos tableros."""

        # Encabezado con el número de ronda
        t = self.f_med.render(f'RONDA  {self.ronda}', True, ACENTO)
        self.pantalla.blit(t, (ANCHO//2 - t.get_width()//2, 8))

        # Etiqueta del tablero del jugador
        t1 = self.f_norm.render('TU TABLERO', True, VERDE)
        self.pantalla.blit(t1, (POS_JUG[0] + COLS*CELDA//2 - t1.get_width()//2, 118))

        # Etiqueta del tablero enemigo
        t2 = self.f_norm.render('TABLERO ENEMIGO', True, ROJO_C)
        self.pantalla.blit(t2, (POS_ENE[0] + COLS*CELDA//2 - t2.get_width()//2, 105))

        # Indicador de turno
        if self.estado == JUGAR:
            if self.turno == 'jugador':
                hint = 'Click para disparar'
                hcol = ACENTO
            else:
                hint = 'Computadora pensando...'
                hcol = GRIS
            th = self.f_small.render(hint, True, hcol)
            self.pantalla.blit(th, (POS_ENE[0] + COLS*CELDA//2 - th.get_width()//2, 128))

        # Tablero del jugador (barcos visibles)
        self._dibujar_tablero(self.tablero_jug, *POS_JUG, mostrar_barcos=True)
        self._dibujar_etiquetas(*POS_JUG)

        # Tablero del enemigo (barcos ocultos)
        self._dibujar_tablero(self.ia.tablero, *POS_ENE, mostrar_barcos=False)
        self._dibujar_etiquetas(*POS_ENE)

        # Hover en el tablero enemigo durante el turno del jugador
        if self.estado == JUGAR and self.mouse_celda and self.turno == 'jugador':
            f, c = self.mouse_celda
            if (f, c) not in self.ia.tablero.disparos:
                px, py = self._celda_a_pixel(f, c, POS_ENE)
                s = pygame.Surface((CELDA - 2, CELDA - 2), pygame.SRCALPHA)
                # Efecto de pulso con seno
                alpha = int(128 + 60 * math.sin(self.ticks * 0.15))
                s.fill((255, 255, 255, alpha))
                self.pantalla.blit(s, (px + 1, py + 1))

                # Coordenada de la celda sobre el hover
                letra = chr(ord('A') + c)
                ct = self.f_mini.render(f'{letra}{f+1}', True, BLANCO)
                self.pantalla.blit(ct, (px + CELDA//2 - ct.get_width()//2,
                                        py + CELDA//2 - ct.get_height()//2))

        # Panel lateral con estado de los barcos
        self._dibujar_panel()

        # Mensaje de estado
        if self.estado == JUGAR:
            self._dibujar_msg()

    def _dibujar_panel(self):
        """Panel lateral derecho que muestra el estado de los barcos."""
        bx = POS_ENE[0] + COLS * CELDA + 22
        by = 158

        # ─ Tus barcos ─
        th = self.f_small.render('TUS BARCOS', True, GRIS)
        self.pantalla.blit(th, (bx, by))
        by += 22

        for entrada in self.tablero_jug.barcos:
            b = entrada['barco']
            if b.hundido:
                color = ROJO_C
                estado_txt = 'Hundido'
            else:
                color = VERDE
                estado_txt = f'{b.impactos}/{b.tamano}'
            tn = self.f_mini.render(f'{b.nombre[:12]}', True, color)
            ts = self.f_mini.render(estado_txt, True, color)
            self.pantalla.blit(tn, (bx, by))
            self.pantalla.blit(ts, (bx + 115, by))
            by += 20

        by += 18
        # ─ Barcos enemigos ─
        th = self.f_small.render('BARCOS ENEMIGOS', True, GRIS)
        self.pantalla.blit(th, (bx, by))
        by += 22

        for entrada in self.ia.tablero.barcos:
            b = entrada['barco']
            if b.hundido:
                color = ROJO_C
                estado_txt = 'Hundido'
            else:
                color = GRIS
                estado_txt = '???'
            tn = self.f_mini.render(f'{b.nombre[:12]}', True, color)
            ts = self.f_mini.render(estado_txt, True, color)
            self.pantalla.blit(tn, (bx, by))
            self.pantalla.blit(ts, (bx + 115, by))
            by += 20

    # ── FIN ───────────────────────────────
    def _dibujar_fin(self):
        """Pantalla de fin de juego con overlay oscuro."""
        # Capa semitransparente oscura sobre el juego
        overlay = pygame.Surface((ANCHO, ALTO), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 175))
        self.pantalla.blit(overlay, (0, 0))

        # Caja central
        caja = pygame.Rect(ANCHO//2 - 320, ALTO//2 - 170, 640, 300)
        pygame.draw.rect(self.pantalla, PANEL, caja, border_radius=18)
        pygame.draw.rect(self.pantalla, BORDE_H, caja, 2, border_radius=18)

        if self.ganador == 'jugador':
            titulo  = '¡¡ GANASTE !!'
            color_t = VERDE
            sub_txt = f'Hundiste todos los barcos enemigos en {self.ronda} rondas'
        else:
            titulo  = '¡¡ PERDISTE !!'
            color_t = ROJO_C
            sub_txt = f'La computadora hundió todos tus barcos en {self.ronda} rondas'

        t = self.f_grande.render(titulo, True, color_t)
        self.pantalla.blit(t, (ANCHO//2 - t.get_width()//2, ALTO//2 - 145))

        s = self.f_norm.render(sub_txt, True, TEXTO)
        self.pantalla.blit(s, (ANCHO//2 - s.get_width()//2, ALTO//2 - 70))

        self._boton(self._r_btn_reiniciar(), 'JUGAR DE NUEVO', self.f_med)

    # ────────────────────────────────────
    #  DIBUJO DEL TABLERO
    # ────────────────────────────────────
    def _dibujar_tablero(self, tablero, ox, oy, mostrar_barcos):
        """
        Dibuja un tablero en la posición (ox, oy) de la pantalla.

        Parámetros:
            tablero        : Objeto Tablero a dibujar
            ox, oy         : Posición de origen en píxeles
            mostrar_barcos : Si False, oculta los barcos (tablero enemigo)
        """
        for f in range(FILAS):
            for c in range(COLS):
                px, py = self._celda_a_pixel(f, c, (ox, oy))
                estado = tablero.celdas[f][c]

                # Elegimos el color según el estado de la celda
                if estado == 'agua':
                    # Efecto de onda suave en el agua
                    onda = int(8 * math.sin(self.ticks * 0.04 + f * 0.5 + c * 0.3))
                    color = (AGUA[0], AGUA[1] + onda, min(255, AGUA[2] + onda))
                elif estado == 'barco':
                    color = BARCO_OK if mostrar_barcos else AGUA
                elif estado == 'impacto':
                    color = IMPACTO
                elif estado == 'fallo':
                    color = FALLO_C
                else:
                    color = AGUA

                # Rectángulo de la celda con bordes redondeados
                rect = pygame.Rect(px + 1, py + 1, CELDA - 2, CELDA - 2)
                pygame.draw.rect(self.pantalla, color, rect, border_radius=4)

                # Símbolo dentro de la celda
                if estado == 'impacto':
                    txt = self.f_celda.render('X', True, BLANCO)
                    self.pantalla.blit(txt, (px + CELDA//2 - txt.get_width()//2,
                                            py + CELDA//2 - txt.get_height()//2))
                elif estado == 'fallo':
                    pygame.draw.circle(self.pantalla, (150, 180, 220),
                                       (px + CELDA//2, py + CELDA//2), 4)

                # Borde de la celda
                pygame.draw.rect(self.pantalla, BORDE, rect, 1, border_radius=4)

    def _dibujar_etiquetas(self, ox, oy):
        """Dibuja letras A-J (columnas) y números 1-10 (filas) del tablero."""
        letras = 'ABCDEFGHIJ'
        for i, l in enumerate(letras):
            t = self.f_celda.render(l, True, GRIS)
            self.pantalla.blit(t, (ox + i * CELDA + CELDA//2 - t.get_width()//2, oy - 20))
        for i in range(FILAS):
            t = self.f_celda.render(str(i + 1), True, GRIS)
            self.pantalla.blit(t, (ox - 24, oy + i * CELDA + CELDA//2 - t.get_height()//2))

    def _dibujar_msg(self):
        """Dibuja el mensaje de estado en la parte inferior de la pantalla."""
        if self.mensaje:
            t = self.f_norm.render(self.mensaje, True, self.msg_color)
            self.pantalla.blit(t, (ANCHO//2 - t.get_width()//2, ALTO - 36))

    def _boton(self, rect, texto, fuente):
        """
        Dibuja un botón con efecto hover (cambia de color al pasar el mouse).
        """
        pos_m = pygame.mouse.get_pos()
        hover = rect.collidepoint(pos_m)
        col   = BTN_H if hover else BTN

        # Cuerpo del botón
        pygame.draw.rect(self.pantalla, col, rect, border_radius=12)
        # Borde
        pygame.draw.rect(self.pantalla, BORDE_H if hover else BORDE, rect, 2, border_radius=12)
        # Texto centrado
        t = fuente.render(texto, True, BTN_T)
        self.pantalla.blit(t, (rect.centerx - t.get_width()//2,
                               rect.centery - t.get_height()//2))

    # ────────────────────────────────────
    #  UTILIDADES
    # ────────────────────────────────────
    def _celda_a_pixel(self, fila, col, origen):
        """
        Convierte índices de celda (fila, col) a coordenadas de píxel.

        Ejemplo: celda (0, 0) con origen (50, 160) → píxel (50, 160)
        """
        ox, oy = origen
        return (ox + col * CELDA, oy + fila * CELDA)

    def _pixel_a_celda(self, pos, origen):
        """
        Convierte coordenadas de píxel a índices de celda (fila, col).
        Retorna None si el píxel está fuera del tablero.
        """
        ox, oy = origen
        px, py = pos
        c = (px - ox) // CELDA
        f = (py - oy) // CELDA
        if 0 <= f < FILAS and 0 <= c < COLS:
            return (f, c)
        return None

    def _emit_particulas(self, x, y, color, cantidad):
        """Crea partículas de efecto visual en la posición (x, y)."""
        for _ in range(cantidad):
            self.particulas.append(Particula(x, y, color))

    def _mensaje(self, texto, color=TEXTO):
        """Establece el mensaje de estado que se muestra en la parte inferior."""
        self.mensaje   = texto
        self.msg_color = color

    # ────────────────────────────────────
    #  RECTÁNGULOS DE LOS BOTONES
    #  Definidos como métodos para reutilizarlos en
    #  la detección de clicks y en el renderizado
    # ────────────────────────────────────
    def _r_btn_jugar(self):
        return pygame.Rect(ANCHO//2 - 115, ALTO - 135, 230, 58)

    def _r_btn_auto(self):
        return pygame.Rect(80, ALTO - 68, 145, 44)

    def _r_btn_reset(self):
        return pygame.Rect(242, ALTO - 68, 165, 44)

    def _r_btn_reiniciar(self):
        return pygame.Rect(ANCHO//2 - 145, ALTO//2 + 55, 290, 58)


# ============================================================
# PUNTO DE ENTRADA DEL PROGRAMA
# ============================================================
if __name__ == '__main__':
    # Creamos el objeto del juego y arrancamos el bucle principal
    juego = BatallaNavalGUI()
    juego.ejecutar()
