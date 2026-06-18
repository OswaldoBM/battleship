# -*- coding: utf-8 -*-
"""
====================================================
  JUEGO DE BATALLA NAVAL - BATTLESHIP
  Programado con Programacion Orientada a Objetos (POO)
  Comentarios en Espanol para estudiantes de 2do semestre
====================================================

Conceptos de POO utilizados:
  - Clases y Objetos
  - Encapsulamiento (atributos y metodos)
  - Herencia (la IA hereda de Jugador)
  - Metodos especiales (__init__, __str__)
  - Composicion (el juego contiene jugadores y tableros)
"""

import random  # Modulo para generar numeros aleatorios
import os      # Modulo para limpiar la pantalla de la consola
import sys     # Modulo para configurar la codificacion de salida

# Configuramos la salida para soportar caracteres especiales en Windows
if sys.stdout.encoding != 'utf-8':
    try:
        sys.stdout.reconfigure(encoding='utf-8')
    except AttributeError:
        pass  # Python antiguo: no es posible reconfigurar, continuamos

# ============================================================
# CLASE: Barco
# Representa un barco del juego con nombre, tamaño y posición
# ============================================================
class Barco:
    """
    Clase que representa un barco en el tablero.
    
    Atributos:
        nombre  (str)  : El nombre del barco (ej. "Portaaviones")
        tamanio (int)  : Cuántas casillas ocupa el barco
        impactos(int)  : Cuántos impactos ha recibido el barco
        hundido (bool) : Si el barco ya fue hundido o no
    """

    def __init__(self, nombre, tamanio):
        """
        Constructor de la clase Barco.
        Se llama automáticamente al crear un objeto Barco.
        
        Parámetros:
            nombre  : Nombre del barco
            tamanio : Número de casillas que ocupa
        """
        self.nombre   = nombre   # Guardamos el nombre del barco
        self.tamanio  = tamanio  # Guardamos el tamaño del barco
        self.impactos = 0        # Al inicio no tiene impactos
        self.hundido  = False    # Al inicio no está hundido

    def recibir_impacto(self):
        """
        Registra un impacto en el barco.
        Si los impactos son iguales al tamaño, el barco se hunde.
        """
        self.impactos += 1  # Incrementamos el contador de impactos
        # Si los impactos llegan al tamaño máximo, el barco se hunde
        if self.impactos >= self.tamanio:
            self.hundido = True
            return True  # Retornamos True para indicar que se hundió
        return False  # El barco recibió impacto pero no se hundió

    def __str__(self):
        """
        Método especial que define cómo se muestra el barco como texto.
        Ejemplo: "Portaaviones (5 casillas)"
        """
        return f"{self.nombre} ({self.tamanio} casillas)"


# ============================================================
# CLASE: Tablero
# Representa el tablero de 10x10 donde se colocan los barcos
# ============================================================
class Tablero:
    """
    Clase que representa el tablero de juego (cuadrícula de 10x10).
    
    El tablero usa los siguientes símbolos:
        '~' : Agua (casilla vacía)
        'O' : Barco (visible solo en el tablero propio)
        'X' : Impacto (barco golpeado)
        '*' : Fallo (disparo al agua)
    """

    TAMANIO = 10  # Constante de clase: el tablero es siempre de 10x10

    def __init__(self):
        """
        Constructor del tablero.
        Inicializa la cuadrícula con agua ('~') en todas las casillas.
        """
        # Creamos una cuadrícula 10x10 llena de agua '~'
        # Esta es una lista de listas (matriz 2D)
        self.cuadricula = [['~'] * self.TAMANIO for _ in range(self.TAMANIO)]
        
        # Lista para guardar todos los barcos colocados en este tablero
        self.barcos = []
        
        # Conjunto de coordenadas que ya fueron disparadas (evita repetir)
        self.disparos_realizados = set()

    def colocar_barco(self, barco, fila, columna, direccion):
        """
        Coloca un barco en el tablero en la posición indicada.
        
        Parámetros:
            barco     : Objeto de tipo Barco a colocar
            fila      : Fila de inicio (0-9)
            columna   : Columna de inicio (0-9)
            direccion : 'H' para Horizontal, 'V' para Vertical
            
        Retorna:
            True  si el barco se colocó correctamente
            False si hay un error (sale del tablero o se solapa)
        """
        # Guardamos las casillas que ocupará el barco
        casillas = []

        for i in range(barco.tamanio):
            if direccion == 'H':
                # Si es horizontal, aumentamos la columna
                f, c = fila, columna + i
            else:
                # Si es vertical, aumentamos la fila
                f, c = fila + i, columna

            # Verificamos que la casilla esté dentro del tablero
            if f >= self.TAMANIO or c >= self.TAMANIO:
                return False  # Fuera del tablero

            # Verificamos que la casilla no esté ocupada por otro barco
            if self.cuadricula[f][c] != '~':
                return False  # Casilla ya ocupada

            casillas.append((f, c))  # Guardamos la casilla

        # Si todas las casillas son válidas, colocamos el barco
        for (f, c) in casillas:
            self.cuadricula[f][c] = 'O'  # Marcamos la casilla como ocupada

        # Guardamos el barco con sus coordenadas para registrar impactos
        self.barcos.append({'barco': barco, 'casillas': casillas})
        return True  # El barco se colocó exitosamente

    def recibir_disparo(self, fila, columna):
        """
        Procesa un disparo en la posición dada.
        
        Parámetros:
            fila    : Fila del disparo (0-9)
            columna : Columna del disparo (0-9)
            
        Retorna:
            Un diccionario con:
              'resultado' : 'AGUA', 'IMPACTO', 'HUNDIDO' o 'REPETIDO'
              'barco'     : El objeto Barco si hubo impacto (o None)
        """
        coord = (fila, columna)  # Guardamos la coordenada como tupla

        # Verificamos si ya se disparó a esta casilla antes
        if coord in self.disparos_realizados:
            return {'resultado': 'REPETIDO', 'barco': None}

        # Registramos el disparo para no repetirlo después
        self.disparos_realizados.add(coord)

        # Revisamos si el disparo golpeó algún barco
        for entrada in self.barcos:
            if coord in entrada['casillas']:
                # ¡Impacto! Notificamos al barco
                barco = entrada['barco']
                se_hundio = barco.recibir_impacto()
                self.cuadricula[fila][columna] = 'X'  # Marcamos el impacto

                if se_hundio:
                    return {'resultado': 'HUNDIDO', 'barco': barco}
                else:
                    return {'resultado': 'IMPACTO', 'barco': barco}

        # Si no golpeó ningún barco, es agua
        self.cuadricula[fila][columna] = '*'  # Marcamos el fallo
        return {'resultado': 'AGUA', 'barco': None}

    def todos_hundidos(self):
        """
        Verifica si todos los barcos del tablero fueron hundidos.
        
        Retorna:
            True  si todos los barcos están hundidos (el jugador perdió)
            False si aún quedan barcos en pie
        """
        # Usamos all() para verificar que todos los barcos estén hundidos
        return all(entrada['barco'].hundido for entrada in self.barcos)

    def mostrar(self, ocultar_barcos=False):
        """
        Muestra el tablero en la consola de forma visual.
        
        Parámetros:
            ocultar_barcos : Si es True, oculta los barcos ('O' aparece como '~')
                             Se usa para el tablero del enemigo
        """
        # Encabezado con letras de columnas (A-J)
        letras = '  A B C D E F G H I J'
        print(letras)
        print('  ' + '-' * 19)

        for i, fila in enumerate(self.cuadricula):
            # Número de fila al inicio (1-10 para hacerlo más legible)
            linea = f"{i + 1:2}|"

            for casilla in fila:
                # Si debemos ocultar barcos, cambiamos 'O' por '~'
                if ocultar_barcos and casilla == 'O':
                    linea += '~ '
                else:
                    # Damos color a los símbolos para que se vea mejor
                    linea += self._colorear(casilla) + ' '

            print(linea)

    def _colorear(self, simbolo):
        """
        Aplica color ANSI al símbolo para la consola.
        (Los colores solo funcionan en terminales que soporten ANSI)
        
        Parámetros:
            simbolo : El carácter a colorear
        Retorna:
            El símbolo con códigos de color ANSI
        """
        # Diccionario que mapea símbolos a colores ANSI
        colores = {
            '~': '\033[94m~\033[0m',   # Azul  -> Agua
            'O': '\033[92mO\033[0m',   # Verde -> Barco
            'X': '\033[91mX\033[0m',   # Rojo  -> Impacto
            '*': '\033[93m*\033[0m',   # Amarillo -> Fallo
        }
        # Retornamos el símbolo con color, o el símbolo original si no tiene color
        return colores.get(simbolo, simbolo)


# ============================================================
# CLASE: Jugador (clase base)
# Representa un jugador genérico del juego
# ============================================================
class Jugador:
    """
    Clase base que representa a un jugador en el juego.
    
    Atributos:
        nombre          : Nombre del jugador
        tablero_propio  : El tablero donde están sus barcos
        tablero_enemigo : El tablero del oponente (donde dispara)
    """

    # Lista de barcos del juego con sus nombres y tamaños
    BARCOS_DEL_JUEGO = [
        ('Portaaviones', 5),  # El barco más grande
        ('Acorazado',    4),
        ('Crucero',      3),
        ('Submarino',    3),
        ('Destructor',   2),  # El barco más pequeño
    ]

    def __init__(self, nombre):
        """
        Constructor del Jugador.
        
        Parámetros:
            nombre : Nombre del jugador
        """
        self.nombre         = nombre          # Nombre del jugador
        self.tablero_propio = Tablero()       # Crea su propio tablero vacío
        self.tablero_enemigo = None           # El tablero enemigo se asigna después

    def colocar_todos_los_barcos(self):
        """
        Método que debe ser implementado por las subclases.
        Define cómo se colocan los barcos (manualmente o aleatoriamente).
        """
        # raise NotImplementedError indica que las subclases DEBEN implementar esto
        raise NotImplementedError("Las subclases deben implementar este método")

    def hacer_disparo(self):
        """
        Método que debe ser implementado por las subclases.
        Define cómo el jugador elige dónde disparar.
        """
        raise NotImplementedError("Las subclases deben implementar este método")


# ============================================================
# CLASE: JugadorHumano (hereda de Jugador)
# Representa al jugador humano que da órdenes por teclado
# ============================================================
class JugadorHumano(Jugador):
    """
    Clase que representa al jugador humano.
    Hereda de la clase Jugador y permite la entrada por teclado.
    
    Herencia: JugadorHumano ES UN Jugador (relación "es-un")
    """

    def __init__(self, nombre):
        """
        Constructor del JugadorHumano.
        Llamamos al constructor de la clase padre con super()
        """
        super().__init__(nombre)  # Llamamos al __init__ de Jugador

    def colocar_todos_los_barcos(self):
        """
        Permite al jugador humano colocar sus barcos manualmente o de forma aleatoria.
        """
        print(f"\n{'='*50}")
        print(f"  📋 Fase de colocación de barcos - {self.nombre}")
        print(f"{'='*50}")
        
        # Preguntamos si quiere colocación manual o aleatoria
        opcion = input("\n¿Cómo deseas colocar tus barcos?\n  [1] Manual\n  [2] Aleatoria\nOpción: ").strip()

        if opcion == '1':
            self._colocar_manual()   # Colocación manual
        else:
            self._colocar_aleatorio()  # Colocación aleatoria
            print(f"\n✅ Barcos colocados aleatoriamente para {self.nombre}")

    def _colocar_manual(self):
        """
        Permite al jugador colocar cada barco de forma manual,
        eligiendo posición y dirección para cada uno.
        """
        for nombre_barco, tamanio in Jugador.BARCOS_DEL_JUEGO:
            barco = Barco(nombre_barco, tamanio)  # Creamos el objeto Barco
            colocado = False

            while not colocado:
                # Mostramos el tablero actual
                print(f"\n📍 Tu tablero actual:")
                self.tablero_propio.mostrar()

                print(f"\n🚢 Coloca tu {barco} (tamaño: {tamanio})")
                print("   Columnas: A-J | Filas: 1-10")

                try:
                    # Pedimos la posición al jugador
                    pos = input("   Ingresa posición (ej. A5): ").strip().upper()
                    if len(pos) < 2:
                        print("❌ Posición inválida. Intenta de nuevo.")
                        continue

                    # Convertimos la letra a índice de columna (A=0, B=1, ..., J=9)
                    columna = ord(pos[0]) - ord('A')
                    fila    = int(pos[1:]) - 1  # Restamos 1 porque la lista empieza en 0

                    # Verificamos rango válido
                    if not (0 <= fila < 10 and 0 <= columna < 10):
                        print("❌ Posición fuera del tablero. Intenta de nuevo.")
                        continue

                    # Pedimos la dirección
                    dir_input = input("   Dirección [H=Horizontal / V=Vertical]: ").strip().upper()
                    if dir_input not in ('H', 'V'):
                        print("❌ Dirección inválida. Usa H o V.")
                        continue

                    # Intentamos colocar el barco en el tablero
                    colocado = self.tablero_propio.colocar_barco(barco, fila, columna, dir_input)

                    if not colocado:
                        print("❌ No se puede colocar ahí. Verifica que no salga del tablero ni se solape.")

                except ValueError:
                    print("❌ Entrada inválida. Ejemplo correcto: A5")

    def _colocar_aleatorio(self):
        """
        Coloca todos los barcos en posiciones aleatorias válidas.
        Usa un ciclo que intenta posiciones hasta encontrar una válida.
        """
        for nombre_barco, tamanio in Jugador.BARCOS_DEL_JUEGO:
            barco   = Barco(nombre_barco, tamanio)
            colocado = False

            while not colocado:
                # Generamos posición y dirección aleatoria
                fila      = random.randint(0, 9)
                columna   = random.randint(0, 9)
                direccion = random.choice(['H', 'V'])

                # Intentamos colocarlo; si falla, el ciclo lo intenta de nuevo
                colocado = self.tablero_propio.colocar_barco(barco, fila, columna, direccion)

    def hacer_disparo(self):
        """
        Pide al jugador humano que ingrese las coordenadas de su disparo.
        
        Retorna:
            Una tupla (fila, columna) con las coordenadas del disparo
        """
        while True:
            try:
                # Pedimos la coordenada del disparo
                entrada = input(f"\n🎯 {self.nombre}, ¿Dónde disparas? (ej. B4): ").strip().upper()

                if len(entrada) < 2:
                    print("❌ Entrada inválida. Ejemplo: B4")
                    continue

                # Convertimos la entrada a índices de fila y columna
                columna = ord(entrada[0]) - ord('A')
                fila    = int(entrada[1:]) - 1

                # Verificamos que esté dentro del tablero
                if not (0 <= fila < 10 and 0 <= columna < 10):
                    print("❌ Coordenada fuera del tablero. Rango válido: A1 - J10")
                    continue

                return (fila, columna)  # Retornamos las coordenadas válidas

            except ValueError:
                print("❌ Formato incorrecto. Ejemplo correcto: B4")


# ============================================================
# CLASE: JugadorIA (hereda de Jugador)
# Representa a la computadora como oponente
# ============================================================
class JugadorIA(Jugador):
    """
    Clase que representa a la Inteligencia Artificial (computadora).
    Hereda de Jugador e implementa estrategia automática de disparo.
    
    La IA tiene dos modos:
      - BUSCAR  : Dispara aleatoriamente hasta encontrar un barco
      - ATACAR  : Una vez que da en un barco, ataca casillas adyacentes
    """

    def __init__(self):
        """
        Constructor de la IA.
        Inicializa el estado interno de la estrategia.
        """
        super().__init__("Computadora")  # Nombre fijo: "Computadora"

        # Estado de la IA: 'BUSCAR' o 'ATACAR'
        self.modo = 'BUSCAR'

        # Lista de casillas pendientes por atacar (cuando encuentra un barco)
        self.casillas_pendientes = []

        # Coordenadas del primer impacto exitoso (para orientar el ataque)
        self.primer_impacto = None

    def colocar_todos_los_barcos(self):
        """
        La IA coloca todos sus barcos de forma aleatoria automáticamente.
        """
        for nombre_barco, tamanio in Jugador.BARCOS_DEL_JUEGO:
            barco   = Barco(nombre_barco, tamanio)
            colocado = False

            while not colocado:
                fila      = random.randint(0, 9)
                columna   = random.randint(0, 9)
                direccion = random.choice(['H', 'V'])
                colocado  = self.tablero_propio.colocar_barco(barco, fila, columna, direccion)

    def hacer_disparo(self):
        """
        La IA decide automáticamente dónde disparar.
        
        Estrategia:
          1. Si está en modo BUSCAR: dispara aleatoriamente
          2. Si está en modo ATACAR: dispara en casillas adyacentes al impacto
          
        Retorna:
            Una tupla (fila, columna) con las coordenadas elegidas
        """
        disparos_usados = self.tablero_enemigo.disparos_realizados

        if self.modo == 'ATACAR' and self.casillas_pendientes:
            # Tomamos la próxima casilla de la lista de pendientes
            while self.casillas_pendientes:
                fila, columna = self.casillas_pendientes.pop(0)
                if (fila, columna) not in disparos_usados:
                    return (fila, columna)

        # Si no hay pendientes o estamos en modo BUSCAR, disparamos aleatorio
        self.modo = 'BUSCAR'
        while True:
            fila    = random.randint(0, 9)
            columna = random.randint(0, 9)
            if (fila, columna) not in disparos_usados:
                return (fila, columna)

    def notificar_resultado(self, fila, columna, resultado):
        """
        Recibe el resultado del último disparo para ajustar la estrategia.
        
        Parámetros:
            fila, columna : Coordenadas del disparo
            resultado     : 'AGUA', 'IMPACTO' o 'HUNDIDO'
        """
        if resultado == 'IMPACTO':
            # ¡Impacto! Cambiamos a modo ATACAR
            self.modo = 'ATACAR'
            if self.primer_impacto is None:
                self.primer_impacto = (fila, columna)  # Guardamos el primer impacto

            # Agregamos las casillas adyacentes (arriba, abajo, izquierda, derecha)
            adyacentes = [
                (fila - 1, columna),  # Arriba
                (fila + 1, columna),  # Abajo
                (fila, columna - 1),  # Izquierda
                (fila, columna + 1),  # Derecha
            ]
            for f, c in adyacentes:
                # Solo agregamos si está dentro del tablero y no se ha disparado
                if (0 <= f < 10 and 0 <= c < 10 and
                        (f, c) not in self.tablero_enemigo.disparos_realizados):
                    if (f, c) not in self.casillas_pendientes:
                        self.casillas_pendientes.append((f, c))

        elif resultado == 'HUNDIDO':
            # Barco hundido: reiniciamos el estado de ataque
            self.modo = 'BUSCAR'
            self.casillas_pendientes = []
            self.primer_impacto      = None


# ============================================================
# CLASE: Juego
# Clase principal que controla el flujo completo del juego
# ============================================================
class Juego:
    """
    Clase principal que orquesta toda la partida de Battleship.
    
    Gestiona:
      - La creación de los jugadores
      - El turno de cada jugador
      - La visualización de los tableros
      - La detección del ganador
    """

    def __init__(self):
        """
        Constructor del Juego.
        Inicializa el jugador humano y la IA.
        """
        # Pedimos el nombre del jugador humano
        nombre = input("¡Bienvenido a Batalla Naval! 🚢\n\nIngresa tu nombre: ").strip()
        if not nombre:
            nombre = "Jugador"  # Nombre por defecto si no ingresa ninguno

        # Creamos los dos jugadores
        self.humano      = JugadorHumano(nombre)
        self.computadora = JugadorIA()

        # Cada jugador "ve" el tablero del otro para poder disparar
        self.humano.tablero_enemigo      = self.computadora.tablero_propio
        self.computadora.tablero_enemigo = self.humano.tablero_propio

        # Contador de rondas
        self.ronda = 0

    def limpiar_pantalla(self):
        """
        Limpia la pantalla de la consola para una mejor presentación.
        Usa el comando correcto según el sistema operativo.
        """
        # 'nt' es el nombre del sistema operativo Windows
        os.system('cls' if os.name == 'nt' else 'clear')

    def mostrar_tableros(self):
        """
        Muestra ambos tableros lado a lado de forma organizada.
        """
        print(f"\n{'='*50}")
        print(f"  🌊 TU TABLERO ({self.humano.nombre})")
        print(f"{'='*50}")
        # Mostramos nuestro tablero (sin ocultar barcos)
        self.humano.tablero_propio.mostrar(ocultar_barcos=False)

        print(f"\n{'='*50}")
        print(f"  🎯 TABLERO ENEMIGO (Computadora)")
        print(f"{'='*50}")
        # Mostramos el tablero enemigo (ocultamos sus barcos)
        self.computadora.tablero_propio.mostrar(ocultar_barcos=True)

    def mostrar_bienvenida(self):
        """
        Muestra el mensaje de bienvenida y las instrucciones del juego.
        """
        self.limpiar_pantalla()
        print("""
╔══════════════════════════════════════════════════╗
║          🚢  BATALLA NAVAL - BATTLESHIP  🚢        ║
╠══════════════════════════════════════════════════╣
║  REGLAS DEL JUEGO:                               ║
║  • Cada jugador tiene un tablero de 10x10        ║
║  • Debes hundir todos los barcos del enemigo     ║
║  • Por turno se realiza un disparo               ║
║                                                  ║
║  BARCOS:                                         ║
║  🚢 Portaaviones  ████████████ (5 casillas)      ║
║  ⚓ Acorazado     ████████████ (4 casillas)      ║
║  🛳  Crucero       ██████████   (3 casillas)      ║
║  🔱 Submarino     ██████████   (3 casillas)      ║
║  💣 Destructor    ████████     (2 casillas)      ║
║                                                  ║
║  SÍMBOLOS:                                       ║
║  ~ = Agua  |  O = Barco  |  X = Impacto         ║
║  * = Disparo fallido                             ║
╚══════════════════════════════════════════════════╝
        """)

    def turno_humano(self):
        """
        Ejecuta el turno del jugador humano.
        Pide coordenadas y procesa el disparo.
        
        Retorna:
            True si el humano ganó (hundió todos los barcos), False si no
        """
        # El humano elige dónde disparar
        fila, columna = self.humano.hacer_disparo()

        # Procesamos el disparo en el tablero de la computadora
        resultado = self.computadora.tablero_propio.recibir_disparo(fila, columna)

        # Mostramos el resultado del disparo
        tipo = resultado['resultado']
        if tipo == 'AGUA':
            print(f"\n💧 ¡AGUA! Tu disparo cayó al mar.")
        elif tipo == 'IMPACTO':
            print(f"\n🔥 ¡IMPACTO! Golpeaste el {resultado['barco'].nombre}!")
        elif tipo == 'HUNDIDO':
            print(f"\n💥 ¡HUNDIDO! Destruiste el {resultado['barco'].nombre}!")
        elif tipo == 'REPETIDO':
            print(f"\n⚠️  Ya disparaste a esa casilla. Pierdes el turno.")

        # Verificamos si el humano ganó (todos los barcos hundidos)
        if self.computadora.tablero_propio.todos_hundidos():
            return True  # El humano ganó

        return False  # El juego continúa

    def turno_computadora(self):
        """
        Ejecuta el turno de la computadora (IA).
        La IA elige automáticamente dónde disparar.
        
        Retorna:
            True si la computadora ganó, False si no
        """
        # La IA elige las coordenadas del disparo
        fila, columna = self.computadora.hacer_disparo()

        # Convertimos los índices a notación visual (ej. fila=0, columna=2 -> "C1")
        letra = chr(ord('A') + columna)
        numero = fila + 1
        print(f"\n🤖 La computadora dispara en {letra}{numero}...")

        # Procesamos el disparo en el tablero del humano
        resultado = self.humano.tablero_propio.recibir_disparo(fila, columna)

        # La IA ajusta su estrategia según el resultado
        self.computadora.notificar_resultado(fila, columna, resultado['resultado'])

        # Mostramos el resultado del disparo de la IA
        tipo = resultado['resultado']
        if tipo == 'AGUA':
            print(f"   💧 La computadora falló. ¡El disparo cayó al agua!")
        elif tipo == 'IMPACTO':
            print(f"   🔥 ¡La computadora golpeó tu {resultado['barco'].nombre}!")
        elif tipo == 'HUNDIDO':
            print(f"   💥 ¡La computadora hundió tu {resultado['barco'].nombre}!")

        # Verificamos si la computadora ganó
        if self.humano.tablero_propio.todos_hundidos():
            return True  # La computadora ganó

        return False  # El juego continúa

    def jugar(self):
        """
        Método principal que ejecuta el ciclo completo del juego.
        
        El flujo es:
          1. Mostrar bienvenida
          2. Colocar barcos
          3. Ciclo de turnos hasta que alguien gane
          4. Mostrar ganador
        """
        # Paso 1: Mostramos la pantalla de bienvenida
        self.mostrar_bienvenida()
        input("\nPresiona ENTER para comenzar...")

        # Paso 2: Colocamos los barcos de ambos jugadores
        print("\n📦 La computadora está colocando sus barcos...")
        self.computadora.colocar_todos_los_barcos()  # IA coloca sus barcos

        self.humano.colocar_todos_los_barcos()  # Humano coloca sus barcos

        # Paso 3: Ciclo principal del juego
        juego_terminado = False

        while not juego_terminado:
            self.ronda += 1  # Incrementamos el contador de rondas

            self.limpiar_pantalla()
            print(f"\n{'='*50}")
            print(f"  ⚓ RONDA {self.ronda}")
            print(f"{'='*50}")

            # Mostramos el estado actual de los tableros
            self.mostrar_tableros()

            # ---- TURNO DEL HUMANO ----
            print(f"\n{'─'*50}")
            print(f"  🎮 TURNO DE {self.humano.nombre.upper()}")
            print(f"{'─'*50}")
            gano_humano = self.turno_humano()

            if gano_humano:
                # El humano ganó; mostramos el mensaje de victoria
                self.limpiar_pantalla()
                self.mostrar_tableros()
                print(f"""
╔══════════════════════════════════════════════════╗
║  🏆  ¡¡FELICIDADES, {self.humano.nombre.upper()}!!            ║
║  ¡Hundiste todos los barcos enemigos en {self.ronda} rondas!║
╚══════════════════════════════════════════════════╝
                """)
                juego_terminado = True
                break

            # Pausa breve para que el humano vea el resultado de su turno
            input("\nPresiona ENTER para el turno de la computadora...")

            # ---- TURNO DE LA COMPUTADORA ----
            print(f"\n{'─'*50}")
            print(f"  🤖 TURNO DE LA COMPUTADORA")
            print(f"{'─'*50}")
            gano_computadora = self.turno_computadora()

            if gano_computadora:
                # La computadora ganó
                self.limpiar_pantalla()
                self.mostrar_tableros()
                print(f"""
╔══════════════════════════════════════════════════╗
║  💀  ¡LA COMPUTADORA GANÓ!                       ║
║  Todos tus barcos fueron hundidos en {self.ronda} rondas. ║
║  ¡Mejor suerte la próxima vez!                  ║
╚══════════════════════════════════════════════════╝
                """)
                juego_terminado = True
                break

            # Pausa para que el humano vea el resultado de la IA
            input("\nPresiona ENTER para la siguiente ronda...")

        # Paso 4: Preguntamos si desea jugar de nuevo
        self.preguntar_revancha()

    def preguntar_revancha(self):
        """
        Al final del juego, pregunta al jugador si desea jugar otra partida.
        """
        respuesta = input("\n¿Deseas jugar de nuevo? [S/N]: ").strip().upper()
        if respuesta == 'S':
            # Creamos un nuevo juego y lo iniciamos
            nuevo_juego = Juego()
            nuevo_juego.jugar()
        else:
            print("\n¡Gracias por jugar Batalla Naval! 🚢 ¡Hasta pronto!\n")


# ============================================================
# PUNTO DE ENTRADA DEL PROGRAMA
# El bloque if __name__ == '__main__' asegura que el código
# solo se ejecute si corremos este archivo directamente,
# y no si lo importamos como módulo en otro programa.
# ============================================================
if __name__ == '__main__':
    # Creamos una instancia de la clase Juego y llamamos al método jugar()
    partida = Juego()
    partida.jugar()
