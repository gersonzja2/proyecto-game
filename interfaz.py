import wx
import time
import os
from pygame import mixer
mixer.init()
from logica import Escenario
try:
    import winsound
except Exception:
    winsound = None
    
#Interfaz del juego usando wxPython

# archivo de música de fondo (reproducir en bucle)
MEGALOVIA_FILE = "megalovia.mp3"
# archivo de efecto corto para acciones (si se desea mantendremos compatibilidad)
AUDIO_GAME = "audio_snake.mp3"

class VistaSimple:
    def __init__(self):
        self.app = wx.App()
        # Ventana ajustada a 800x600
        self.ventana = wx.Frame(None, title="Juego", size=wx.Size(800, 600))
        self.panel = wx.Panel(self.ventana)
        # reutilizando los eventos de teclado y de dibujar en pantalla
        # Usar EVT_CHAR_HOOK en el frame garantiza recibir teclas especiales (flechas, etc.) incluso si el foco
        # está en controles distintos. También mantenemos EVT_KEY_DOWN en el panel por compatibilidad.
        self.ventana.Bind(wx.EVT_CHAR_HOOK, self.on_key_down)
        self.panel.Bind(wx.EVT_KEY_DOWN, self.on_key_down)
        # Si el usuario hace clic en el panel, devolver el foco al panel para que reciba eventos de teclado
        self.panel.Bind(wx.EVT_LEFT_DOWN, lambda e: self.panel.SetFocus())
        # evento de pintado
        self.panel.Bind(wx.EVT_PAINT, self.on_paint)

        # Lógica del juego: crear la instancia de Escenario (módulo separado)
        # reset_game creará la instancia de Escenario
        self.reset_game()

        # bandera de estado de juego (Game Over)
        self.game_over = False
        self.who_died = None
        # --------------------------------
        self.instrucciones = wx.StaticText(self.panel, label="Usa las teclas para mover a los personajes", pos=wx.Point(10, 10))
        self.instrucciones.SetForegroundColour(wx.Colour(0, 0, 255))

        # Mostrar la ventana antes de pedir foco al panel
        self.ventana.Centre()
        self.ventana.Show()
        # Aseguramos que el panel tenga el foco para recibir eventos de teclado
        self.panel.SetFocus()
        # bandera/temporizador para indicar si mostrar el mensaje de contacto
        # usamos un temporizador (timestamp) para que el texto permanezca visible
        # durante un corto periodo tras detectar contacto
        self.mostrar_mensaje_contacto = False
        self.mensaje_contacto_until = 0.0  # timestamp unix en segundos
        # umbral (en píxeles) para considerar "contacto" con un punto
        self.contact_threshold = 10
        # intentar iniciar música de fondo en bucle (no bloqueante)
        try:
            if os.path.exists(MEGALOVIA_FILE):
                mixer.music.load(MEGALOVIA_FILE)
                # loops=-1 hace que la música se repita indefinidamente
                mixer.music.play(loops=-1)
            else:
                # si no existe, no hacemos nada; la vista puede seguir reproduciendo efectos
                pass
        except Exception:
            # Si falla el mixer o el archivo, seguimos sin música
            pass

    def reset_game(self):
        """Restablece el estado inicial del juego (personajes)."""
        # recrear escenario
        self.escenario = Escenario()
        # propagar atributos a nivel de vista para compatibilidad
        self.caballero = self.escenario.caballero
        self.monstruo = self.escenario.monstruo
        self.curador = self.escenario.curador
        self.game_over = False
        self.who_died = None
        # bandera que indica victoria (monstruo muerto)
        self.victoria = False
    
    def dibujar_barra_vida(self, dc, personaje, vida_maxima, color):
        """Dibuja una barra de vida sobre el personaje.
        
        Args:
            dc: Device Context de wxPython
            personaje: Objeto personaje con posicion_x, posicion_y y vida
            vida_maxima: Vida máxima del personaje
            color: Color de la barra (wx.Colour)
        """
        # Dimensiones de la barra
        ancho_total = 50
        alto_barra = 6
        offset_y = -30  # Distancia sobre el personaje
        
        # Posición de la barra (centrada sobre el personaje)
        x = personaje.posicion_x - ancho_total // 2
        y = personaje.posicion_y + offset_y
        
        # Calcular ancho de la barra según vida actual
        vida_actual = max(0, personaje.vida)
        porcentaje_vida = vida_actual / vida_maxima
        ancho_vida = int(ancho_total * porcentaje_vida)
        
        # Dibujar fondo de la barra (negro)
        dc.SetPen(wx.Pen(wx.Colour(0, 0, 0), 1))
        dc.SetBrush(wx.Brush(wx.Colour(40, 40, 40)))
        dc.DrawRectangle(x, y, ancho_total, alto_barra)
        
        # Dibujar vida actual
        if vida_actual > 0:
            # Color cambia según el porcentaje de vida
            if porcentaje_vida > 0.6:
                color_barra = color
            elif porcentaje_vida > 0.3:
                # Advertencia (amarillo/naranja)
                color_barra = wx.Colour(255, 200, 0)
            else:
                # Crítico (rojo)
                color_barra = wx.Colour(255, 50, 50)
            
            dc.SetBrush(wx.Brush(color_barra))
            dc.DrawRectangle(x, y, ancho_vida, alto_barra)
        
        # Dibujar borde de la barra
        dc.SetPen(wx.Pen(wx.Colour(255, 255, 255), 1))
        dc.SetBrush(wx.TRANSPARENT_BRUSH)
        dc.DrawRectangle(x, y, ancho_total, alto_barra)
        
        # Mostrar valor numérico de vida
        dc.SetTextForeground(wx.Colour(255, 255, 255))
        font_small = wx.Font(7, wx.FONTFAMILY_SWISS, wx.FONTSTYLE_NORMAL, wx.FONTWEIGHT_BOLD)
        dc.SetFont(font_small)
        texto_vida = f"{int(vida_actual)}"
        tw, th = dc.GetTextExtent(texto_vida)
        dc.DrawText(texto_vida, x + (ancho_total - tw) // 2, y - th - 2)
    
    def on_paint(self, event):
        dc = wx.PaintDC(self.panel)
        dc.SetBackground(wx.Brush(wx.Colour(255, 255, 255)))
        dc.Clear()

        # Mostrar posición del caballero/monstruo/curador - ajustadas para ventana más grande
        dc.DrawText(f"X: {self.escenario.caballero.posicion_x}, Y: {self.escenario.caballero.posicion_y}", 650, 60)
        dc.DrawText(f"X: {self.escenario.monstruo.posicion_x}, Y: {self.escenario.monstruo.posicion_y}", 650, 80)
        dc.DrawText(f"X: {self.escenario.curador.posicion_x}, Y: {self.escenario.curador.posicion_y}", 650, 100)

        # Dibujar caballero - Verde que se opaca con la pérdida de vida
        vida_porcentaje = self.escenario.caballero.vida / 500  # 500 es la vida máxima
        color_verde = max(0, min(255, int(255 * vida_porcentaje)))
        dc.SetBrush(wx.Brush(wx.Colour(0, color_verde, 0)))
        dc.DrawCircle(self.escenario.caballero.posicion_x, self.escenario.caballero.posicion_y, 20)
        
        # Barra de vida del caballero
        self.dibujar_barra_vida(dc, self.escenario.caballero, 500, wx.Colour(0, 255, 0))

        # Dibujar monstruo - Rojo que se opaca con la pérdida de vida
        vida_porcentaje = self.escenario.monstruo.vida / 500
        color_rojo = max(0, min(255, int(255 * vida_porcentaje)))
        dc.SetBrush(wx.Brush(wx.Colour(color_rojo, 0, 0)))
        # variar el radio del monstruo según su vida (más vida -> mayor tamaño)
        radio_monstruo = 20 + int(self.escenario.monstruo.vida / 200)
        dc.DrawCircle(self.escenario.monstruo.posicion_x, self.escenario.monstruo.posicion_y, radio_monstruo)
        
        # Barra de vida del monstruo (vida máxima puede ser hasta 2000)
        vida_max_monstruo = max(500, self.escenario.monstruo.vida)
        self.dibujar_barra_vida(dc, self.escenario.monstruo, vida_max_monstruo, wx.Colour(255, 0, 0))

        # Dibujar curador - Azul que se opaca con la pérdida de vida
        vida_porcentaje = self.escenario.curador.vida / 500
        color_azul = max(0, min(255, int(255 * vida_porcentaje)))
        dc.SetBrush(wx.Brush(wx.Colour(0, 0, color_azul)))
        dc.DrawCircle(self.escenario.curador.posicion_x, self.escenario.curador.posicion_y, 20)
        
        # Barra de vida del curador
        self.dibujar_barra_vida(dc, self.escenario.curador, 500, wx.Colour(0, 100, 255))

        # Dibujar recompensas actuales
        for rec in self.escenario.recompensa:
            dc.SetBrush(wx.Brush(wx.Colour(255, 215, 0)))  # dorado
            dc.DrawCircle(rec['x'], rec['y'], 6)

        # Dibujar puntos negros (beneficio para el monstruo)
        for pn in self.escenario.puntos_negros:
            dc.SetBrush(wx.Brush(wx.Colour(0, 0, 0)))
            dc.DrawCircle(pn['x'], pn['y'], 6)
        # Efecto visual: círculo expandiéndose al recoger recompensa
        if self.escenario.ultimo_recogido_pos and self.escenario.ultimo_recogido:
            _, _, ts = self.escenario.ultimo_recogido
            if time.time() - ts < 0.6:
                elapsed = time.time() - ts
                rx = int(6 + elapsed * 50)
                x, y = self.escenario.ultimo_recogido_pos
                try:
                    dc.SetPen(wx.Pen(wx.Colour(255, 0, 255), 2))
                    dc.SetBrush(wx.Brush(wx.Colour(255, 0, 255, 50)))
                except Exception:
                    dc.SetBrush(wx.Brush(wx.Colour(255, 0, 255)))
                dc.DrawCircle(x, y, rx)

        # Mostrar mensaje temporal si se recogió una recompensa recientemente
        if self.escenario.ultimo_recogido:
            valor, quien, ts = self.escenario.ultimo_recogido
            if time.time() - ts < 1.0:
                dc.SetTextForeground(wx.Colour(255, 0, 255))
                dc.DrawText(f"{quien} +{valor} pts!", 350, 10)
            else:
                self.escenario.ultimo_recogido = None

        # Mostrar mensaje temporal si el monstruo comió un punto negro
        if self.escenario.ultimo_punto_negro:
            inc, ts2 = self.escenario.ultimo_punto_negro
            if time.time() - ts2 < 1.0:
                dc.SetTextForeground(wx.Colour(0, 0, 0))
                dc.DrawText(f"Monstruo +{inc} vida!", 350, 30)
            else:
                self.escenario.ultimo_punto_negro = None

        # Efecto visual: círculo expandiéndose cuando el monstruo come el punto negro
        if self.escenario.ultimo_punto_negro_pos and self.escenario.ultimo_punto_negro:
            _, tsn = self.escenario.ultimo_punto_negro
            if time.time() - tsn < 0.8:
                elapsed = time.time() - tsn
                rx = int(8 + elapsed * 60)
                x, y = self.escenario.ultimo_punto_negro_pos
                try:
                    dc.SetPen(wx.Pen(wx.Colour(0, 0, 0), 2))
                    dc.SetBrush(wx.Brush(wx.Colour(0, 0, 0, 40)))
                except Exception:
                    dc.SetBrush(wx.Brush(wx.Colour(0, 0, 0)))
                dc.DrawCircle(x, y, rx)

        # Mostrar vidas y puntos
        dc.SetTextForeground(wx.Colour(0, 0, 0))
        dc.DrawText(f"Vida Caballero: {self.escenario.caballero.vida}", 10, 60)
        dc.DrawText(f"Vida Monstruo: {self.escenario.monstruo.vida}", 10, 40)
        dc.DrawText(f"Vida Curador: {self.escenario.curador.vida}", 10, 80)
        dc.DrawText(f"Puntos Caballero: {self.escenario.puntos_caballero}", 10, 220)
        dc.DrawText(f"Puntos Curador: {self.escenario.puntos_curador}", 10, 240)

        # Mostrar instrucciones de ataque y curacion
        dc.DrawText("WASD: Mover Caballero, X: Atacar Monstruo", 10, 120)
        dc.DrawText("Flechas: Mover Curador, Y: Curar Caballero, U: Autocuración, T: Envenenar Monstruo", 10, 140)
        dc.DrawText("IJKL: Mover Monstruo, M: Atacar Caballero, N: Atacar Curador", 10, 160)
        dc.DrawText("ESC: Salir", 10, 180)

        # Si el juego terminó mostrar pantalla Game Over o Victoria encima
        if self.game_over:
            try:
                overlay_brush = wx.Brush(wx.Colour(0, 0, 0, 120))
            except Exception:
                overlay_brush = wx.Brush(wx.Colour(0, 0, 0))
            dc.SetBrush(overlay_brush)
            w, h = self.panel.GetSize()
            dc.DrawRectangle(0, 0, w, h)
            font = wx.Font(28, wx.FONTFAMILY_SWISS, wx.FONTSTYLE_NORMAL, wx.FONTWEIGHT_BOLD)
            dc.SetFont(font)
            if self.who_died == 'Monstruo' or getattr(self, 'victoria', False):
                dc.SetTextForeground(wx.Colour(0, 200, 0))
                msg = "¡VICTORIA!"
            else:
                dc.SetTextForeground(wx.Colour(255, 0, 0))
                msg = "GAME OVER"
            tw, th = dc.GetTextExtent(msg)
            dc.DrawText(msg, (w - tw) // 2, (h - th) // 2 - 20)
            font2 = wx.Font(12, wx.FONTFAMILY_SWISS, wx.FONTSTYLE_NORMAL, wx.FONTWEIGHT_NORMAL)
            dc.SetFont(font2)
            dc.SetTextForeground(wx.Colour(255, 255, 255))
            if self.who_died == 'Monstruo' or getattr(self, 'victoria', False):
                sub = "Has derrotado al monstruo"
            else:
                sub = f"Ha muerto: {self.who_died}" if self.who_died else ""
            s2 = "Presiona R para reiniciar o ESC para salir"
            sw, sh = dc.GetTextExtent(sub)
            s2w, s2h = dc.GetTextExtent(s2)
            dc.DrawText(sub, (w - sw) // 2, (h - sh) // 2 + 10)
            dc.DrawText(s2, (w - s2w) // 2, (h - s2h) // 2 + 30)
            
    def sound(self, archivo):
        # reproducir efectos cortos sin detener la música de fondo
        try:
            if os.path.exists(archivo):
                s = mixer.Sound(archivo)
                s.play()
        except Exception:
            # fallback: intentar reproducir con music (puede detener la pista de fondo)
            try:
                mixer.music.load(archivo)
                mixer.music.play(loops=0)
            except Exception:
                pass

    def on_key_down(self, event):
        keycode = event.GetKeyCode()
        print(f"Tecla presionada: {keycode} ({chr(keycode) if 32 <= keycode <= 126 else ''})")
        # Si estamos en Game Over, aceptar sólo reinicio o salir
        if self.game_over:
            if keycode == ord('R') or keycode == ord('r'):
                print("Reiniciando juego...")
                self.reset_game()
                self.panel.Refresh()
                return
            elif keycode == wx.WXK_ESCAPE:
                self.ventana.Close()
                return
            else:
                return
        elif keycode == ord('W') or keycode == ord('w'):
            self.escenario.caballero.mover_arriba()
            self.sound(AUDIO_GAME)
        elif keycode == ord('S') or keycode == ord('s'):
            self.escenario.caballero.mover_abajo()
            self.sound(AUDIO_GAME)
        elif keycode == ord('A') or keycode == ord('a'):
            self.escenario.caballero.mover_izquierda()
            self.sound(AUDIO_GAME)
        elif keycode == ord('D') or keycode == ord('d'):
            self.escenario.caballero.mover_derecha()
            self.sound(AUDIO_GAME)
            self.escenario.caballero.mover_derecha()
            self.sound(AUDIO_GAME)
        elif keycode == ord('X') or keycode == ord('x'):
            self.escenario.caballero.atacar_monstruo(self.escenario.monstruo)
        elif keycode == wx.WXK_UP:
            print("Flecha Arriba!")
            self.escenario.curador.mover_arriba()
        elif keycode == wx.WXK_DOWN:
            print("Flecha Abajo!")
            self.escenario.curador.mover_abajo()
        elif keycode == wx.WXK_LEFT:
            print("Flecha Izquierda!")
            self.escenario.curador.mover_izquierda()
        elif keycode == wx.WXK_RIGHT:
            print("Flecha Derecha!")
            self.escenario.curador.mover_derecha()
        elif keycode == ord('Y') or keycode == ord('y'):
            self.escenario.curador.curar_caballero(self.escenario.caballero)
        elif keycode == ord('U') or keycode == ord('u'):
            self.escenario.curador.autocurarse()
        elif keycode == ord('T') or keycode == ord('t'):
            self.escenario.curador.envenenar_monstruo(self.escenario.monstruo)
        elif keycode == ord('I') or keycode == ord('i'):
            self.escenario.monstruo.mover_arriba()
        elif keycode == ord('K') or keycode == ord('k'):
            self.escenario.monstruo.mover_abajo()
        elif keycode == ord('J') or keycode == ord('j'):
            self.escenario.monstruo.mover_izquierda()
        elif keycode == ord('L') or keycode == ord('l'):
            self.escenario.monstruo.mover_derecha()
        elif keycode == ord('M') or keycode == ord('m'):
            self.escenario.monstruo.atacar_caballero(self.escenario.caballero)
        elif keycode == ord('N') or keycode == ord('n'):
            self.escenario.monstruo.atacar_caballero(self.escenario.curador)
        elif keycode == wx.WXK_ESCAPE:
            self.ventana.Close()
            return
        # después de cada acción del jugador, manejar colisiones y actualizar estado
        try:
            self.escenario.manejar_colisiones()
        except Exception:
            pass
        self.panel.Refresh()
        # Comprobar si alguno murió después de la acción
        # sincronizar referencias de personajes
        self.caballero = self.escenario.caballero
        self.monstruo = self.escenario.monstruo
        self.curador = self.escenario.curador
        self.check_game_over()
        event.Skip()

    def check_game_over(self):
        """
        Regla: si el monstruo muere -> VICTORIA.
               si el caballero o el curador mueren -> GAME OVER.
        """
        # Prioridad: victoria si el monstruo muere
        if self.escenario.monstruo.vida <= 0:
            self.game_over = True
            self.who_died = "Monstruo"
            self.victoria = True
            print("Victoria: Monstruo muerto")
            return

        # Si no hay victoria, comprobar muertes de aliados
        if self.escenario.caballero.vida <= 0:
            self.game_over = True
            self.who_died = "Caballero"
            # asegurar que la bandera de victoria esté desactivada
            self.victoria = False
            print("Game Over: Caballero muerto")
            return

        if self.escenario.curador.vida <= 0:
            self.game_over = True
            self.who_died = "Curador"
            self.victoria = False
            print("Game Over: Curador muerto")
            return
        
    def iniciar(self):
        self.app.MainLoop()
        
if __name__ == "__main__":
    print("==Juego en 2 capas logica y vista==")
    juego = VistaSimple()
    juego.iniciar()