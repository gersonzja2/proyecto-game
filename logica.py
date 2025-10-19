import random
import time


class Personaje:
    def __init__(self, x, y, vida):
        self.posicion_x = x
        self.posicion_y = y
        self.vida = vida
        self.salto = 5

    def mover_arriba(self):
        if (self.posicion_y > 0):
            self.posicion_y -= self.salto
        else:
            self.posicion_y = 200

    def mover_abajo(self):
        if (self.posicion_y < 365):
            self.posicion_y += self.salto
        else:
            self.posicion_y = 200

    def mover_izquierda(self):
        if (self.posicion_x > 0):
            self.posicion_x -= self.salto
        else:
            self.posicion_x = 250

    def mover_derecha(self):
        if (self.posicion_x < 480):
            self.posicion_x += self.salto
        else:
            self.posicion_x = 250


class Monstruo(Personaje):
    def __init__(self, x, y, vida, poder):
        super().__init__(x, y, vida)
        self.poder = poder

    def atacar_caballero(self, caballero):
        if (self.poder < caballero.vida):
            caballero.vida = caballero.vida - self.poder
        else:
            caballero.vida = 0


class Caballero(Personaje):
    def __init__(self, x, y, vida, defensa):
        super().__init__(x, y, vida)
        self.defensa = defensa

    def atacar_monstruo(self, monstruo):
        if (self.defensa < monstruo.vida):
            monstruo.vida = monstruo.vida - self.defensa
        else:
            monstruo.vida = 0


class Curador(Personaje):
    def __init__(self, x, y, vida, poder_curacion):
        super().__init__(x, y, vida)
        self.poder_curacion = poder_curacion

    def curar_caballero(self, caballero):
        caballero.vida = caballero.vida + self.poder_curacion
        if (caballero.vida > 500):
            caballero.vida = 500

    def envenenar_monstruo(self, monstruo):
        if (self.poder_curacion < monstruo.vida):
            monstruo.vida = monstruo.vida - self.poder_curacion
        else:
            monstruo.vida = 0


class Escenario:
    """Contiene el estado y la lógica de interacción entre personajes y puntos.

    La vista debe usar únicamente la API pública de esta clase para consultar
    el estado del juego y actualizar la interfaz.
    """
    def __init__(self):
        # personajes
        self.caballero = Caballero(250, 200, 500, 100)
        self.monstruo = Monstruo(150, 100, 500, 100)
        self.curador = Curador(350, 300, 500, 50)

        # recompensas y puntos negros
        self.recompensa = []
        self.crear_recompensa(3)
        self.puntos_negros = []
        self.crear_puntos_negros(2)

        # estadísticas
        self.puntos_caballero = 0
        self.puntos_curador = 0

        # eventos recientes (para que la vista los muestre)
        self.ultimo_recogido = None  # (valor, quien, timestamp)
        self.ultimo_recogido_pos = None
        self.ultimo_punto_negro = None  # (incremento, timestamp)
        self.ultimo_punto_negro_pos = None

    def crear_recompensa(self, cantidad):
        ancho = 480
        alto = 365
        self.recompensa = []
        for _ in range(cantidad):
            self.recompensa.append(self.crear_una_recompensa())

    def crear_una_recompensa(self):
        ancho = 480
        alto = 365
        x = random.randint(20, ancho - 20)
        y = random.randint(20, alto - 20)
        valor = random.choice([5, 10, 15])
        return {'x': x, 'y': y, 'valor': valor}

    def crear_un_punto_negro(self):
        ancho = 480
        alto = 365
        x = random.randint(20, ancho - 20)
        y = random.randint(20, alto - 20)
        incremento = random.choice([30, 50, 70])
        return {'x': x, 'y': y, 'inc': incremento}

    def crear_puntos_negros(self, cantidad):
        self.puntos_negros = []
        for _ in range(cantidad):
            self.puntos_negros.append(self.crear_un_punto_negro())

    def detectar_colision(self, obj1, obj2):
        try:
            dx = obj1.posicion_x - obj2['x'] if isinstance(obj2, dict) else obj1.posicion_x - obj2.posicion_x
            dy = obj1.posicion_y - obj2['y'] if isinstance(obj2, dict) else obj1.posicion_y - obj2.posicion_y
        except Exception:
            return False
        distancia2 = dx * dx + dy * dy
        return distancia2 <= (15 * 15)

    def manejar_colisiones(self):
        """Maneja interacciones entre personajes y elementos del escenario.

        No realiza efectos visuales ni reproduce sonidos. En su lugar, actualiza
        el estado y deja que la vista consulte los atributos públicos para mostrar
        efectos (por ejemplo, `ultimo_recogido`).
        """
        # recompensas
        for i in range(len(self.recompensa)):
            rec = self.recompensa[i]
            if self.detectar_colision(self.caballero, rec):
                self.puntos_caballero += rec['valor']
                self.caballero.vida = min(500, self.caballero.vida + rec['valor'])
                incremento_def = rec['valor'] // 2
                if hasattr(self.caballero, 'defensa'):
                    self.caballero.defensa = min(300, self.caballero.defensa + incremento_def)
                self.ultimo_recogido = (rec['valor'], 'Caballero', time.time())
                self.ultimo_recogido_pos = (rec['x'], rec['y'])
                self.recompensa[i] = self.crear_una_recompensa()
            elif self.detectar_colision(self.curador, rec):
                self.puntos_curador += rec['valor']
                self.curador.vida = min(500, self.curador.vida + rec['valor'] // 2)
                incremento_cur = rec['valor'] // 2
                if hasattr(self.curador, 'poder_curacion'):
                    self.curador.poder_curacion = min(200, self.curador.poder_curacion + incremento_cur)
                self.ultimo_recogido = (rec['valor'], 'Curador', time.time())
                self.ultimo_recogido_pos = (rec['x'], rec['y'])
                self.recompensa[i] = self.crear_una_recompensa()

        # puntos negros
        for j in range(len(self.puntos_negros)):
            pn = self.puntos_negros[j]
            if self.detectar_colision(self.monstruo, pn):
                inc = pn['inc']
                self.monstruo.vida = self.monstruo.vida + inc
                if self.monstruo.vida > 2000:
                    self.monstruo.vida = 2000
                self.ultimo_punto_negro = (inc, time.time())
                self.ultimo_punto_negro_pos = (pn['x'], pn['y'])
                self.puntos_negros[j] = self.crear_un_punto_negro()
