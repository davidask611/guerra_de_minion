# multijugador.py - Juego multijugador completo con rutas fijas, torres, inhibidores y nexos
import pygame
import sys
import json
import socket
import random
from threading import Thread
class Juego:
    def __init__(self):
        pygame.init()
        self.ANCHO = 800
        self.ALTO = 600
        self.pantalla = pygame.display.set_mode((self.ANCHO, self.ALTO))
        pygame.display.set_caption("Mundo Infinito Multijugador")
        self.reloj = pygame.time.Clock()
        self.estado = "menu"  # menu, seleccion, juego
        self.jugador = {
            "nombre": "",
            "personaje": None,
            "vida": 100,
            "pos": [self.ANCHO // 2, self.ALTO - 100],
            "velocidad": 5
        }
        self.otros_jugadores = {}
        self.socket_cliente = None
        self.conectado = False
        self.id_cliente = None
        
        # Configuración del mapa
        self.mapa = {
            "scroll_y": 0,
            "velocidad_scroll": 3,
            "rutas": []  # Almacenará las rutas fijas
        }
        self.crear_rutas_fijas()  # Crear las rutas
        self.configurar_torres()  # Configurar las torres
        self.configurar_inhibidores()  # Configurar los inhibidores
        self.configurar_nexos()  # Configurar los nexos
        
        # Cargar recursos
        self.cargar_recursos()
    
    def cargar_recursos(self):
        """Cargar imágenes y fuentes"""
        try:
            self.fuente_titulo = pygame.font.SysFont("Arial", 50, bold=True)
            self.fuente_normal = pygame.font.SysFont("Arial", 30)
            self.fuente_pequena = pygame.font.SysFont("Arial", 20)
            
            # Cargar imágenes de personajes (usar imágenes por defecto si no existen)
            try:
                self.personaje1_img = pygame.image.load("assets/personaje1.png").convert_alpha()
                self.personaje2_img = pygame.image.load("assets/personaje2.png").convert_alpha()
            except:
                # Crear imágenes por defecto si no se encuentran los archivos
                self.personaje1_img = pygame.Surface((70, 70), pygame.SRCALPHA)
                pygame.draw.circle(self.personaje1_img, (0, 0, 255), (35, 35), 35)
                self.personaje2_img = pygame.Surface((70, 70), pygame.SRCALPHA)
                pygame.draw.circle(self.personaje2_img, (255, 0, 0), (35, 35), 35)
            
            # Cargar imágenes de torres (usar imágenes por defecto si no existen)
            try:
                self.torre_aliada_img = pygame.image.load("assets/torre_aliada.png").convert_alpha()
                self.torre_enemiga_img = pygame.image.load("assets/torre_enemiga.png").convert_alpha()
            except:
                # Crear imágenes por defecto si no se encuentran los archivos
                self.torre_aliada_img = pygame.Surface((60, 60), pygame.SRCALPHA)
                pygame.draw.rect(self.torre_aliada_img, (0, 255, 0), (0, 0, 60, 60), 0, 10)
                self.torre_enemiga_img = pygame.Surface((60, 60), pygame.SRCALPHA)
                pygame.draw.rect(self.torre_enemiga_img, (255, 0, 0), (0, 0, 60, 60), 0, 10)
            
            # Cargar imágenes de inhibidores
            try:
                self.inhibidor_aliado_img = pygame.image.load("assets/inhibidor_aliado.png").convert_alpha()
                self.inhibidor_enemigo_img = pygame.image.load("assets/inhibidor_enemigo.png").convert_alpha()
            except:
                # Crear imágenes por defecto si no se encuentran los archivos
                self.inhibidor_aliado_img = pygame.Surface((50, 50), pygame.SRCALPHA)
                pygame.draw.polygon(self.inhibidor_aliado_img, (0, 255, 0), [(25, 0), (50, 50), (25, 40), (0, 50)])
                self.inhibidor_enemigo_img = pygame.Surface((50, 50), pygame.SRCALPHA)
                pygame.draw.polygon(self.inhibidor_enemigo_img, (255, 0, 0), [(25, 0), (50, 50), (25, 40), (0, 50)])
            
            # Cargar imágenes de nexos
            try:
                self.nexo_aliado_img = pygame.image.load("assets/nexo_aliado.png").convert_alpha()
                self.nexo_enemigo_img = pygame.image.load("assets/nexo_enemigo.png").convert_alpha()
            except:
                # Crear imágenes por defecto si no se encuentran los archivos
                self.nexo_aliado_img = pygame.Surface((80, 80), pygame.SRCALPHA)
                pygame.draw.circle(self.nexo_aliado_img, (0, 200, 0), (40, 40), 40)
                pygame.draw.circle(self.nexo_aliado_img, (0, 255, 0), (40, 40), 30)
                self.nexo_enemigo_img = pygame.Surface((80, 80), pygame.SRCALPHA)
                pygame.draw.circle(self.nexo_enemigo_img, (200, 0, 0), (40, 40), 40)
                pygame.draw.circle(self.nexo_enemigo_img, (255, 0, 0), (40, 40), 30)
            
            # Escalar imágenes
            self.personaje1_img = pygame.transform.scale(self.personaje1_img, (70, 70))
            self.personaje2_img = pygame.transform.scale(self.personaje2_img, (70, 70))
            self.torre_aliada_img = pygame.transform.scale(self.torre_aliada_img, (60, 60))
            self.torre_enemiga_img = pygame.transform.scale(self.torre_enemiga_img, (60, 60))
            self.inhibidor_aliado_img = pygame.transform.scale(self.inhibidor_aliado_img, (50, 50))
            self.inhibidor_enemigo_img = pygame.transform.scale(self.inhibidor_enemigo_img, (50, 50))
            self.nexo_aliado_img = pygame.transform.scale(self.nexo_aliado_img, (80, 80))
            self.nexo_enemigo_img = pygame.transform.scale(self.nexo_enemigo_img, (80, 80))
            
            # Fondos
            self.fondo_menu = pygame.Surface((self.ANCHO, self.ALTO))
            self.fondo_menu.fill((50, 120, 80))
            self.fondo = pygame.Surface((self.ANCHO, self.ALTO))
            self.fondo.fill((60, 60, 120))
            
            # Texturas simples
            self.textura_roca = pygame.Surface((self.ANCHO, self.ALTO))
            self.textura_roca.fill((70, 70, 70))
    
        except Exception as e:
            print(f"Error cargando recursos: {e}")
            sys.exit()

    def configurar_torres(self):
        """Configura las posiciones de las torres en las rutas con coordenadas exactas"""
        self.torres = {
            "aliadas": [],
            "enemigas": []
        }
        
        # Ruta azul (superior) - 3 torres enemigas
        self.torres["enemigas"].extend([
            (200, 80),  # Torre 1 ruta azul
            (400, 80),  # Torre 2 ruta azul
            (600, 80)   # Torre 3 ruta azul
        ])
        
        # Ruta roja (inferior) - 3 torres aliadas
        self.torres["aliadas"].extend([
            (200, 480),  # Torre 1 ruta roja
            (400, 480),  # Torre 2 ruta roja
            (600, 480)   # Torre 3 ruta roja
        ])
        
        # Ruta blanca izquierda - 3 torres aliadas
        self.torres["aliadas"].extend([
            (50, 170),   # Torre superior
            (50, 300),   # Torre media
            (50, 400)    # Torre inferior
        ])
        
        # Ruta blanca derecha - 3 torres enemigas
        self.torres["enemigas"].extend([
            (750, 170),  # Torre superior
            (750, 300),  # Torre media
            (750, 400)   # Torre inferior
        ])
        
        # Ruta amarilla (diagonal) - 3 aliadas y 3 enemigas
        self.torres["aliadas"].extend([
            (160, 415),  # Torre 1 aliada diagonal
            (275, 355),  # Torre 2 aliada diagonal
            (375, 300)   # Torre 3 aliada diagonal
        ])
        
        self.torres["enemigas"].extend([
            (495, 230),  # Torre 1 enemiga diagonal
            (575, 180),  # Torre 2 enemiga diagonal
            (655, 130)   # Torre 3 enemiga diagonal
        ])

    def configurar_inhibidores(self):
        """Configura las posiciones de los inhibidores en las rutas"""
        self.inhibidores = {
            "aliados": [
                (150, 480),  # Inhibidor aliado 1
                (50, 435),   # Inhibidor aliado 2
                (140, 435)   # Inhibidor aliado 3
            ],
            "enemigos": [
                (685, 120),  # Inhibidor enemigo 1
                (750, 145),  # Inhibidor enemigo 2
                (655, 80)    # Inhibidor enemigo 3
            ]
        }

    def configurar_nexos(self):
        """Configura las posiciones de los nexos en las rutas"""
        self.nexos = {
            "aliados": [
                (40, 490)  # Nexo aliado (base aliada)
            ],
            "enemigos": [
                (750, 70)  # Nexo enemigo (base enemiga)
            ]
        }

    def crear_rutas_fijas(self):
        """Crea las rutas fijas en el mapa"""
        # Ruta azul (superior)
        ruta_azul = {
            "color": (0, 0, 255),
            "puntos": [
                (49, 100),  # inicio
                (self.ANCHO - 49, 100)  # fin
            ]
        }
        
        # Ruta roja (inferior)
        ruta_roja = {
            "color": (255, 0, 0),
            "puntos": [
                (49, self.ALTO - 100),
                (self.ANCHO - 49, self.ALTO - 100)
            ]
        }

        # Ruta blanca izquierda (conecta arriba e abajo)
        ruta_blanca_izq = {
            "color": (255, 255, 255),
            "puntos": [
                (49, 100),
                (49, self.ALTO - 100)
            ]
        }

        # Ruta blanca derecha (conecta arriba e abajo)
        ruta_blanca_der = {
            "color": (255, 255, 255),
            "puntos": [
                (self.ANCHO - 49, 100),
                (self.ANCHO - 49, self.ALTO - 100)
            ]
        }
        
        # Ruta diagonal amarilla (de abajo izquierda a arriba derecha)
        ruta_amarilla = {
            "color": (255, 255, 0),
            "puntos": [
                (49, self.ALTO - 100),
                (self.ANCHO - 49, 100)
            ]
        }

        self.mapa["rutas"] = [
            ruta_azul, ruta_roja, ruta_blanca_izq, ruta_blanca_der, ruta_amarilla
        ]

    def dibujar_mapa(self):
        """Dibuja las rutas fijas"""
        self.pantalla.blit(self.textura_roca, (0, 0))  # Fondo de rocas
        
        # Dibujar cada ruta
        for ruta in self.mapa["rutas"]:
            if len(ruta["puntos"]) > 1:
                pygame.draw.lines(self.pantalla, ruta["color"], False, 
                                ruta["puntos"], 60)
            
            # Dibujar puntos de inicio/fin como cuadrados
            size = 60  # Lado del cuadrado (igual al diámetro del círculo anterior)
            offset_x = 1  # Cantidad de píxeles a la derecha
            offset_y = 1  # Cantidad de píxeles hacia abajo
            for punto in [ruta["puntos"][0], ruta["puntos"][-1]]:
                pygame.draw.rect(
                    self.pantalla,
                    ruta["color"],
                    (punto[0] - size // 2 + offset_x, punto[1] - size // 2 + offset_y, size, size)
                )

    def dibujar_torres(self):
        """Dibuja todas las torres en el mapa"""
        for x, y in self.torres["aliadas"]:
            self.pantalla.blit(self.torre_aliada_img, (x - 30, y - 30))
        
        for x, y in self.torres["enemigas"]:
            self.pantalla.blit(self.torre_enemiga_img, (x - 30, y - 30))

    def dibujar_inhibidores(self):
        """Dibuja todos los inhibidores en el mapa"""
        for x, y in self.inhibidores["aliados"]:
            self.pantalla.blit(self.inhibidor_aliado_img, (x - 25, y - 25))
        
        for x, y in self.inhibidores["enemigos"]:
            self.pantalla.blit(self.inhibidor_enemigo_img, (x - 25, y - 25))

    def dibujar_nexos(self):
        """Dibuja todos los nexos en el mapa"""
        for x, y in self.nexos["aliados"]:
            self.pantalla.blit(self.nexo_aliado_img, (x - 40, y - 40))
        
        for x, y in self.nexos["enemigos"]:
            self.pantalla.blit(self.nexo_enemigo_img, (x - 40, y - 40))

    def dibujar_jugador(self):
        """Dibuja al jugador principal"""
        if self.jugador["personaje"] == 1:
            imagen = self.personaje1_img
        elif self.jugador["personaje"] == 2:
            imagen = self.personaje2_img
        else:
            # Imagen por defecto si no hay personaje seleccionado
            imagen = pygame.Surface((50, 50), pygame.SRCALPHA)
            imagen.fill((0, 255, 0))
        
        # Dibujar la imagen del personaje
        self.pantalla.blit(imagen, (self.jugador["pos"][0] - 35, self.jugador["pos"][1] - 35))

        # Nombre del jugador
        nombre_texto = self.fuente_normal.render(self.jugador["nombre"], True, (255, 255, 255))
        self.pantalla.blit(nombre_texto, (self.jugador["pos"][0] - nombre_texto.get_width() // 2, 
                           self.jugador["pos"][1] - 40))
    
    def dibujar_otros_jugadores(self):
        """Dibuja a los otros jugadores conectados"""
        for jugador_id, datos in self.otros_jugadores.items():
            if datos["personaje"] == 1:
                imagen = self.personaje1_img
            elif datos["personaje"] == 2:
                imagen = self.personaje2_img
            else:
                # Imagen por defecto si no hay personaje seleccionado
                imagen = pygame.Surface((50, 50), pygame.SRCALPHA)
                imagen.fill((0, 255, 0))
            
            # Dibujar la imagen del personaje
            self.pantalla.blit(imagen, (datos["pos"][0] - 35, datos["pos"][1] - 35))

            # Nombre del jugador
            nombre_texto = self.fuente_normal.render(datos["nombre"], True, (255, 255, 255))
            self.pantalla.blit(nombre_texto, (datos["pos"][0] - nombre_texto.get_width() // 2, 
                               datos["pos"][1] - 40))

    def manejar_movimiento(self):
        """Permite movimiento por todas las rutas fijas y centra al jugador en la ruta"""
        keys = pygame.key.get_pressed()
        movimiento = False
    
        x, y = self.jugador["pos"]
        vel = self.jugador["velocidad"]
        tolerancia = 5
    
        # Detección mejorada de esquinas
        en_esquina = False
        esquina_actual = None
        
        # Coordenadas exactas de las esquinas
        esquinas = {
            "izq_sup": (50, 100),
            "der_sup": (self.ANCHO - 50, 100),
            "izq_inf": (50, self.ALTO - 100),
            "der_inf": (self.ANCHO - 50, self.ALTO - 100)
        }
    
        # Verificar si estamos en una esquina
        for nombre, (ex, ey) in esquinas.items():
            if abs(x - ex) < tolerancia and abs(y - ey) < tolerancia:
                en_esquina = True
                esquina_actual = nombre
                break
    
        # Si está en una esquina
        if en_esquina:
            # Snap exacto a la esquina
            self.jugador["pos"] = list(esquinas[esquina_actual])
            x, y = self.jugador["pos"]
    
            # Si presiona ESPACIO y está en una esquina conectada a la ruta amarilla
            if keys[pygame.K_SPACE] and esquina_actual in ["izq_inf", "der_sup"]:
                # Moverse un poco hacia la diagonal (entrar a la ruta amarilla)
                if esquina_actual == "izq_inf":
                    self.jugador["pos"][0] += vel * 0.5  # Mitad de velocidad para ajuste fino
                    self.jugador["pos"][1] -= vel * 0.5
                elif esquina_actual == "der_sup":
                    self.jugador["pos"][0] -= vel * 0.5
                    self.jugador["pos"][1] += vel * 0.5
                movimiento = True
            else:
                # Movimiento normal desde esquinas
                if esquina_actual == "izq_sup":
                    if keys[pygame.K_d]:  # Derecha
                        self.jugador["pos"][0] += vel
                    if keys[pygame.K_s]:  # Abajo
                        self.jugador["pos"][1] += vel
                elif esquina_actual == "der_sup":
                    if keys[pygame.K_a]:  # Izquierda
                        self.jugador["pos"][0] -= vel
                    if keys[pygame.K_s]:  # Abajo
                        self.jugador["pos"][1] += vel
                elif esquina_actual == "izq_inf":
                    if keys[pygame.K_d]:  # Derecha
                        self.jugador["pos"][0] += vel
                    if keys[pygame.K_w]:  # Arriba
                        self.jugador["pos"][1] -= vel
                elif esquina_actual == "der_inf":
                    if keys[pygame.K_a]:  # Izquierda
                        self.jugador["pos"][0] -= vel
                    if keys[pygame.K_w]:  # Arriba
                        self.jugador["pos"][1] -= vel
    
                movimiento = any([keys[pygame.K_a], keys[pygame.K_d], keys[pygame.K_w], keys[pygame.K_s]])
        else:
            # Movimiento en rutas horizontales (azul/roja)
            if abs(y - 100) < tolerancia:  # Ruta superior
                self.jugador["pos"][1] = 100  # Snap a la ruta
                if keys[pygame.K_a] and x > 50:
                    self.jugador["pos"][0] -= vel
                if keys[pygame.K_d] and x < self.ANCHO - 50:
                    self.jugador["pos"][0] += vel
                movimiento = keys[pygame.K_a] or keys[pygame.K_d]
                
            elif abs(y - (self.ALTO - 100)) < tolerancia:  # Ruta inferior
                self.jugador["pos"][1] = self.ALTO - 100  # Snap a la ruta
                if keys[pygame.K_a] and x > 50:
                    self.jugador["pos"][0] -= vel
                if keys[pygame.K_d] and x < self.ANCHO - 50:
                    self.jugador["pos"][0] += vel
                movimiento = keys[pygame.K_a] or keys[pygame.K_d]
    
            # Movimiento en rutas verticales (blancas)
            elif abs(x - 50) < tolerancia:  # Ruta izquierda
                self.jugador["pos"][0] = 50  # Snap a la ruta
                if keys[pygame.K_w] and y > 100:
                    self.jugador["pos"][1] -= vel
                if keys[pygame.K_s] and y < self.ALTO - 100:
                    self.jugador["pos"][1] += vel
                movimiento = keys[pygame.K_w] or keys[pygame.K_s]
                
            elif abs(x - (self.ANCHO - 50)) < tolerancia:  # Ruta derecha
                self.jugador["pos"][0] = self.ANCHO - 50  # Snap a la ruta
                if keys[pygame.K_w] and y > 100:
                    self.jugador["pos"][1] -= vel
                if keys[pygame.K_s] and y < self.ALTO - 100:
                    self.jugador["pos"][1] += vel
                movimiento = keys[pygame.K_w] or keys[pygame.K_s]
    
            # Movimiento en ruta diagonal amarilla
            else:
                # Calculamos la posición esperada en la diagonal
                m = (100 - (self.ALTO - 100)) / ((self.ANCHO - 50) - 50)
                b = (self.ALTO - 100) - m * 50
                y_esperado = m * x + b
    
                # Verificar si estamos cerca de la diagonal
                if abs(y - y_esperado) < tolerancia * 2:
                    # Snap a la diagonal
                    self.jugador["pos"][1] = y_esperado
                    
                    # Movimiento en la diagonal con cualquier combinación de teclas
                    if (keys[pygame.K_w] or keys[pygame.K_s]) and (keys[pygame.K_a] or keys[pygame.K_d]):
                        if keys[pygame.K_d] and x < self.ANCHO - 50 and y > 100:  # Arriba-derecha
                            self.jugador["pos"][0] += vel
                            self.jugador["pos"][1] = m * (x + vel) + b
                        elif keys[pygame.K_a] and x > 50 and y < self.ALTO - 100:  # Abajo-izquierda
                            self.jugador["pos"][0] -= vel
                            self.jugador["pos"][1] = m * (x - vel) + b
                        movimiento = True
    
        # Enviar actualización si hubo movimiento
        if movimiento and self.conectado:
            self.enviar_mensaje("movimiento", {
                "pos": self.jugador["pos"],
                "scroll_y": self.mapa["scroll_y"]
            })

    def dibujar_menu(self):
        """Dibujar el menú principal"""
        self.pantalla.blit(self.fondo_menu, (0, 0))
        
        titulo = self.fuente_titulo.render("Mundo Infinito Multijugador", True, (255, 255, 255))
        self.pantalla.blit(titulo, (self.ANCHO//2 - titulo.get_width()//2, 100))
        
        # Botones
        pygame.draw.rect(self.pantalla, (70, 130, 180), (self.ANCHO//2 - 150, 250, 300, 60))
        texto_jugar = self.fuente_normal.render("Jugar", True, (255, 255, 255))
        self.pantalla.blit(texto_jugar, (self.ANCHO//2 - texto_jugar.get_width()//2, 265))
        
        pygame.draw.rect(self.pantalla, (180, 70, 70), (self.ANCHO//2 - 150, 350, 300, 60))
        texto_salir = self.fuente_normal.render("Salir", True, (255, 255, 255))
        self.pantalla.blit(texto_salir, (self.ANCHO//2 - texto_salir.get_width()//2, 365))
        
        if self.conectado:
            estado = self.fuente_normal.render("Conectado al servidor", True, (0, 255, 0))
        else:
            estado = self.fuente_normal.render("No conectado", True, (255, 0, 0))
        self.pantalla.blit(estado, (20, self.ALTO - 40))

    def dibujar_seleccion(self):
        """Pantalla de selección de personaje y nombre"""
        self.pantalla.blit(self.fondo, (0, 0))
        
        titulo = self.fuente_titulo.render("Elige tu personaje", True, (255, 255, 255))
        self.pantalla.blit(titulo, (self.ANCHO//2 - titulo.get_width()//2, 50))
        
        # Dibujar opciones de personaje (usando imágenes)
        pygame.draw.rect(self.pantalla, 
                         (255, 255, 0) if self.jugador["personaje"] == 1 else (200, 200, 200), 
                         (self.ANCHO//2 - 200, 150, 180, 200), 3)
        self.pantalla.blit(pygame.transform.scale(self.personaje1_img, (150, 150)), 
                           (self.ANCHO//2 - 200 + 15, 160))
        
        pygame.draw.rect(self.pantalla, 
                         (255, 255, 0) if self.jugador["personaje"] == 2 else (200, 200, 200), 
                         (self.ANCHO//2 + 20, 150, 180, 200), 3)
        self.pantalla.blit(pygame.transform.scale(self.personaje2_img, (150, 150)), 
                           (self.ANCHO//2 + 20 + 15, 160))
        
        # Campo de texto para nombre
        pygame.draw.rect(self.pantalla, (255, 255, 255), (self.ANCHO//2 - 150, 400, 300, 40))
        texto_nombre = self.fuente_normal.render(self.jugador["nombre"] or "Tu nombre", True, 
                                                (100, 100, 100) if not self.jugador["nombre"] else (0, 0, 0))
        self.pantalla.blit(texto_nombre, (self.ANCHO//2 - 140, 405))
        
        # Botón de empezar
        if self.jugador["nombre"] and self.jugador["personaje"]:
            pygame.draw.rect(self.pantalla, (70, 180, 70), (self.ANCHO//2 - 100, 470, 200, 50))
        else:
            pygame.draw.rect(self.pantalla, (150, 150, 150), (self.ANCHO//2 - 100, 470, 200, 50))
            
        texto_empezar = self.fuente_normal.render("Empezar", True, (255, 255, 255))
        self.pantalla.blit(texto_empezar, (self.ANCHO//2 - texto_empezar.get_width()//2, 480))

    def manejar_eventos(self):
        """Manejar eventos de pygame"""
        for evento in pygame.event.get():
            if evento.type == pygame.QUIT:
                if self.conectado:
                    self.enviar_mensaje("desconectar", {})
                pygame.quit()
                sys.exit()
                
            if evento.type == pygame.MOUSEBUTTONDOWN:
                x, y = pygame.mouse.get_pos()
                self.manejar_click(x, y)
                
            if evento.type == pygame.KEYDOWN and self.estado == "seleccion":
                if evento.key == pygame.K_BACKSPACE:
                    self.jugador["nombre"] = self.jugador["nombre"][:-1]
                elif evento.key == pygame.K_RETURN and self.jugador["nombre"] and self.jugador["personaje"]:
                    self.enviar_mensaje("nuevo_jugador", self.jugador)
                    self.estado = "juego"
                elif len(self.jugador["nombre"]) < 16:
                    self.jugador["nombre"] += evento.unicode

    def manejar_click(self, x, y):
        """Manejar clicks del mouse"""
        if self.estado == "menu":
            # Botón Jugar
            if self.ANCHO//2 - 150 <= x <= self.ANCHO//2 + 150 and 250 <= y <= 310:
                if not self.conectado:
                    if self.conectar_servidor("localhost", 5555):
                        self.estado = "seleccion"
                else:
                    self.estado = "seleccion"
                    
            # Botón Salir
            elif self.ANCHO//2 - 150 <= x <= self.ANCHO//2 + 150 and 350 <= y <= 410:
                pygame.quit()
                sys.exit()
                
        elif self.estado == "seleccion":
            # Selección personaje 1
            if self.ANCHO//2 - 200 <= x <= self.ANCHO//2 - 20 and 150 <= y <= 350:
                self.jugador["personaje"] = 1
                
            # Selección personaje 2
            elif self.ANCHO//2 + 20 <= x <= self.ANCHO//2 + 200 and 150 <= y <= 350:
                self.jugador["personaje"] = 2
                
            # Botón Empezar
            elif (self.ANCHO//2 - 100 <= x <= self.ANCHO//2 + 100 and 
                  470 <= y <= 520 and self.jugador["nombre"] and self.jugador["personaje"]):
                self.enviar_mensaje("nuevo_jugador", self.jugador)
                self.estado = "juego"

    def conectar_servidor(self, ip_servidor, puerto):
        """Conectar al servidor de juego"""
        try:
            self.socket_cliente = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.socket_cliente.connect((ip_servidor, puerto))
            self.conectado = True
            
            # Hilo para recibir datos
            Thread(target=self.recibir_datos, daemon=True).start()
            return True
        except Exception as e:
            print(f"Error conectando al servidor: {e}")
            return False

    def recibir_datos(self):
        """Recibir datos del servidor"""
        while self.conectado:
            try:
                datos = self.socket_cliente.recv(4096).decode('utf-8')
                if datos:
                    mensajes = datos.split('|')  # Separar mensajes en caso de concatenación
                    for msg in mensajes:
                        if msg:
                            self.procesar_mensaje(json.loads(msg))
            except Exception as e:
                print(f"Error recibiendo datos: {e}")
                self.conectado = False
                break

    def procesar_mensaje(self, mensaje):
        """Procesar mensajes recibidos del servidor"""
        tipo = mensaje.get("tipo")
        
        if tipo == "bienvenida":
            print(f"Conectado al servidor: {mensaje.get('mensaje')}")
            self.id_cliente = mensaje.get("id")
        elif tipo == "jugadores":
            self.otros_jugadores = mensaje.get("jugadores", {})
        elif tipo == "nuevo_jugador":
            self.otros_jugadores[mensaje["id"]] = mensaje
        elif tipo == "jugador_desconectado":
            if mensaje["id"] in self.otros_jugadores:
                del self.otros_jugadores[mensaje["id"]]
        elif tipo == "actualizacion_posicion":
            if mensaje["id"] in self.otros_jugadores:
                self.otros_jugadores[mensaje["id"]]["pos"] = mensaje["pos"]

    def enviar_mensaje(self, tipo, contenido):
        """Enviar mensaje al servidor"""
        if self.conectado:
            mensaje = json.dumps({
                "tipo": tipo,
                "id": self.id_cliente,
                **contenido
            })
            try:
                self.socket_cliente.sendall((mensaje + '|').encode('utf-8'))  # Separador para múltiples mensajes
            except:
                self.conectado = False

    def ejecutar(self):
        """Bucle principal del juego"""
        while True:
            self.manejar_eventos()
            
            if self.estado == "menu":
                self.dibujar_menu()
            elif self.estado == "seleccion":
                self.dibujar_seleccion()
            elif self.estado == "juego":
                self.pantalla.fill((0, 0, 0))  # Fondo negro
                
                self.manejar_movimiento()
                self.dibujar_mapa()
                self.dibujar_torres()  # Dibujar torres
                self.dibujar_inhibidores()  # Dibujar inhibidores
                self.dibujar_nexos()  # Dibujar nexos
                self.dibujar_jugador()
                self.dibujar_otros_jugadores()
                
                # UI - Información del jugador
                vida_texto = self.fuente_normal.render(f"Vida: {self.jugador['vida']}", True, (255, 255, 255))
                self.pantalla.blit(vida_texto, (20, 20))
                
                # Mostrar coordenadas
                coordenadas_texto = self.fuente_normal.render(
                    f"Posición: ({int(self.jugador['pos'][0])}, {int(self.jugador['pos'][1])})", 
                    True, 
                    (255, 255, 255)
                )
                self.pantalla.blit(coordenadas_texto, (20, 50))
                
                # Mostrar estado de conexión
                if not self.conectado:
                    error_texto = self.fuente_normal.render("DESCONECTADO", True, (255, 0, 0))
                    self.pantalla.blit(error_texto, (self.ANCHO - error_texto.get_width() - 20, 20))
            
            pygame.display.flip()
            self.reloj.tick(60)

if __name__ == "__main__":
    juego = Juego()
    juego.ejecutar()