# multijugador.py - Juego multijugador completo con rutas fijas, torres, inhibidores, nexos y minions
import pygame
import sys
import json
import socket
import random
from threading import Thread
from datetime import datetime

class Juego:
    def __init__(self):
        pygame.init()
        self.ANCHO = 800
        self.ALTO = 600
        self.pantalla = pygame.display.set_mode((self.ANCHO, self.ALTO))
        pygame.display.set_caption("Mundo Infinito Multijugador")
        self.reloj = pygame.time.Clock()
        self.estado = "menu"  # menu, seleccion, juego, fin
        self.mensaje_fin = ""
        self.jugador = {
            "nombre": "",
            "personaje": None,
            "vida": 100,
            "vida_max": 100,
            "pos": [self.ANCHO // 2, self.ALTO - 100],
            "velocidad": 5,
            "daño": 20,
            "nivel": 1,
            "experiencia": 0,
            "reduccion_daño": 0
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
        
        # Sistema de estructuras
        self.estructuras = {
            "torres": {
                "aliadas": [],
                "enemigas": []
            },
            "inhibidores": {
                "aliados": [],
                "enemigos": []
            },
            "nexos": {
                "aliados": [],
                "enemigos": []
            }
        }
        
        self.crear_rutas_fijas()  # Crear las rutas
        self.configurar_torres()  # Configurar las torres
        self.configurar_inhibidores()  # Configurar los inhibidores
        self.configurar_nexos()  # Configurar los nexos
        
        # Sistema de minions
        self.minions = {
            "aliados": [],
            "enemigos": []
        }
        self.oleadas = {
            "tiempo_ultima_oleada": 0,
            "intervalo": 30,  # segundos
            "contador_oleadas": 0,
            "tiempo_juego": 0,  # en segundos
            "primer_oleada": False
        }
        self.imagenes_minions = {}  # Para almacenar las imágenes de los minions
        
        # Cargar recursos
        self.cargar_recursos()
    
    def cargar_recursos(self):
        """Cargar imágenes y fuentes"""
        try:
            self.fuente_titulo = pygame.font.SysFont("Arial", 50, bold=True)
            self.fuente_normal = pygame.font.SysFont("Arial", 30)
            self.fuente_pequena = pygame.font.SysFont("Arial", 20)
            
            # Cargar imágenes de personajes
            try:
                self.personaje1_img = pygame.image.load("assets/personaje1.png").convert_alpha()
                self.personaje2_img = pygame.image.load("assets/personaje2.png").convert_alpha()
            except:
                # Crear imágenes por defecto si no se encuentran los archivos
                self.personaje1_img = pygame.Surface((70, 70), pygame.SRCALPHA)
                pygame.draw.circle(self.personaje1_img, (0, 0, 255), (35, 35), 35)
                self.personaje2_img = pygame.Surface((70, 70), pygame.SRCALPHA)
                pygame.draw.circle(self.personaje2_img, (255, 0, 0), (35, 35), 35)
            
            # Cargar imágenes de torres
            try:
                self.torre_aliada_img = pygame.image.load("assets/torre_aliada.png").convert_alpha()
                self.torre_enemiga_img = pygame.image.load("assets/torre_enemiga.png").convert_alpha()
            except:
                # Crear imágenes por defecto
                self.torre_aliada_img = pygame.Surface((60, 60), pygame.SRCALPHA)
                pygame.draw.rect(self.torre_aliada_img, (0, 255, 0), (0, 0, 60, 60), 0, 10)
                self.torre_enemiga_img = pygame.Surface((60, 60), pygame.SRCALPHA)
                pygame.draw.rect(self.torre_enemiga_img, (255, 0, 0), (0, 0, 60, 60), 0, 10)
            
            # Cargar imágenes de inhibidores
            try:
                self.inhibidor_aliado_img = pygame.image.load("assets/inhibidor_aliado.png").convert_alpha()
                self.inhibidor_enemigo_img = pygame.image.load("assets/inhibidor_enemigo.png").convert_alpha()
            except:
                # Crear imágenes por defecto
                self.inhibidor_aliado_img = pygame.Surface((50, 50), pygame.SRCALPHA)
                pygame.draw.polygon(self.inhibidor_aliado_img, (0, 255, 0), [(25, 0), (50, 50), (25, 40), (0, 50)])
                self.inhibidor_enemigo_img = pygame.Surface((50, 50), pygame.SRCALPHA)
                pygame.draw.polygon(self.inhibidor_enemigo_img, (255, 0, 0), [(25, 0), (50, 50), (25, 40), (0, 50)])
            
            # Cargar imágenes de nexos
            try:
                self.nexo_aliado_img = pygame.image.load("assets/nexo_aliado.png").convert_alpha()
                self.nexo_enemigo_img = pygame.image.load("assets/nexo_enemigo.png").convert_alpha()
            except:
                # Crear imágenes por defecto
                self.nexo_aliado_img = pygame.Surface((80, 80), pygame.SRCALPHA)
                pygame.draw.circle(self.nexo_aliado_img, (0, 200, 0), (40, 40), 40)
                pygame.draw.circle(self.nexo_aliado_img, (0, 255, 0), (40, 40), 30)
                self.nexo_enemigo_img = pygame.Surface((80, 80), pygame.SRCALPHA)
                pygame.draw.circle(self.nexo_enemigo_img, (200, 0, 0), (40, 40), 40)
                pygame.draw.circle(self.nexo_enemigo_img, (255, 0, 0), (40, 40), 30)
            
            # Cargar imágenes de minions
            try:
                self.imagenes_minions["melee"] = pygame.image.load("assets/minion_mele.png").convert_alpha()
                self.imagenes_minions["caster"] = pygame.image.load("assets/caster_minion.png").convert_alpha()
                self.imagenes_minions["siege"] = pygame.image.load("assets/cañon_minion.png").convert_alpha()
            except:
                # Crear imágenes por defecto
                self.imagenes_minions["melee"] = pygame.Surface((40, 40), pygame.SRCALPHA)
                pygame.draw.rect(self.imagenes_minions["melee"], (200, 0, 0), (0, 0, 40, 40))
                
                self.imagenes_minions["caster"] = pygame.Surface((40, 40), pygame.SRCALPHA)
                pygame.draw.rect(self.imagenes_minions["caster"], (0, 0, 200), (0, 0, 40, 40))
                
                self.imagenes_minions["siege"] = pygame.Surface((50, 50), pygame.SRCALPHA)
                pygame.draw.rect(self.imagenes_minions["siege"], (150, 150, 0), (0, 0, 50, 50))
            
            # Escalar imágenes
            self.personaje1_img = pygame.transform.scale(self.personaje1_img, (70, 70))
            self.personaje2_img = pygame.transform.scale(self.personaje2_img, (70, 70))
            self.torre_aliada_img = pygame.transform.scale(self.torre_aliada_img, (60, 60))
            self.torre_enemiga_img = pygame.transform.scale(self.torre_enemiga_img, (60, 60))
            self.inhibidor_aliado_img = pygame.transform.scale(self.inhibidor_aliado_img, (50, 50))
            self.inhibidor_enemigo_img = pygame.transform.scale(self.inhibidor_enemigo_img, (50, 50))
            self.nexo_aliado_img = pygame.transform.scale(self.nexo_aliado_img, (80, 80))
            self.nexo_enemigo_img = pygame.transform.scale(self.nexo_enemigo_img, (80, 80))
            self.imagenes_minions["melee"] = pygame.transform.scale(self.imagenes_minions["melee"], (40, 40))
            self.imagenes_minions["caster"] = pygame.transform.scale(self.imagenes_minions["caster"], (40, 40))
            self.imagenes_minions["siege"] = pygame.transform.scale(self.imagenes_minions["siege"], (50, 50))
            
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
        """Configura las torres con vida, daño y reducción de daño"""
        self.estructuras["torres"]["aliadas"] = [
            # Ruta roja (inferior) - 3 torres aliadas (orden invertido 3,2,1)
            {"pos": [200, 480], "vida": 2000, "vida_max": 2000, "daño": 15, "daño_base": 15, 
             "reduccion_daño": 20, "rango": 200, "ruta": 1, "orden": 3, "destruida": False, "ultimo_ataque": 0},
            {"pos": [400, 480], "vida": 2000, "vida_max": 2000, "daño": 10, "daño_base": 10, 
             "reduccion_daño": 10, "rango": 200, "ruta": 1, "orden": 2, "destruida": False, "ultimo_ataque": 0},
            {"pos": [600, 480], "vida": 2000, "vida_max": 2000, "daño": 5, "daño_base": 5, 
             "reduccion_daño": 0, "rango": 200, "ruta": 1, "orden": 1, "destruida": False, "ultimo_ataque": 0},
            
            # Ruta blanca izquierda - 3 torres aliadas (orden normal)
            {"pos": [50, 170], "vida": 2000, "vida_max": 2000, "daño": 5, "daño_base": 5, 
             "reduccion_daño": 0, "rango": 200, "ruta": 2, "orden": 1, "destruida": False, "ultimo_ataque": 0},
            {"pos": [50, 300], "vida": 2000, "vida_max": 2000, "daño": 10, "daño_base": 10, 
             "reduccion_daño": 10, "rango": 200, "ruta": 2, "orden": 2, "destruida": False, "ultimo_ataque": 0},
            {"pos": [50, 400], "vida": 2000, "vida_max": 2000, "daño": 15, "daño_base": 15, 
             "reduccion_daño": 20, "rango": 200, "ruta": 2, "orden": 3, "destruida": False, "ultimo_ataque": 0},
            
            # Ruta amarilla - 3 torres aliadas (orden invertido 3,2,1)
            {"pos": [160, 415], "vida": 2000, "vida_max": 2000, "daño": 15, "daño_base": 15, 
             "reduccion_daño": 20, "rango": 200, "ruta": 4, "orden": 3, "destruida": False, "ultimo_ataque": 0},
            {"pos": [275, 355], "vida": 2000, "vida_max": 2000, "daño": 10, "daño_base": 10, 
             "reduccion_daño": 10, "rango": 200, "ruta": 4, "orden": 2, "destruida": False, "ultimo_ataque": 0},
            {"pos": [375, 300], "vida": 2000, "vida_max": 2000, "daño": 5, "daño_base": 5, 
             "reduccion_daño": 0, "rango": 200, "ruta": 4, "orden": 1, "destruida": False, "ultimo_ataque": 0}
        ]
        
        self.estructuras["torres"]["enemigas"] = [
            # Ruta azul (superior) - 3 torres enemigas (orden normal)
            {"pos": [200, 80], "vida": 2000, "vida_max": 2000, "daño": 5, "daño_base": 5, 
             "reduccion_daño": 0, "rango": 200, "ruta": 0, "orden": 1, "destruida": False, "ultimo_ataque": 0},
            {"pos": [400, 80], "vida": 2000, "vida_max": 2000, "daño": 10, "daño_base": 10, 
             "reduccion_daño": 10, "rango": 200, "ruta": 0, "orden": 2, "destruida": False, "ultimo_ataque": 0},
            {"pos": [600, 80], "vida": 2000, "vida_max": 2000, "daño": 15, "daño_base": 15, 
             "reduccion_daño": 20, "rango": 200, "ruta": 0, "orden": 3, "destruida": False, "ultimo_ataque": 0},
            
            # Ruta blanca derecha - 3 torres enemigas (orden invertido 3,2,1)
            {"pos": [750, 170], "vida": 2000, "vida_max": 2000, "daño": 15, "daño_base": 15, 
             "reduccion_daño": 20, "rango": 200, "ruta": 3, "orden": 3, "destruida": False, "ultimo_ataque": 0},
            {"pos": [750, 300], "vida": 2000, "vida_max": 2000, "daño": 10, "daño_base": 10, 
             "reduccion_daño": 10, "rango": 200, "ruta": 3, "orden": 2, "destruida": False, "ultimo_ataque": 0},
            {"pos": [750, 400], "vida": 2000, "vida_max": 2000, "daño": 5, "daño_base": 5, 
             "reduccion_daño": 0, "rango": 200, "ruta": 3, "orden": 1, "destruida": False, "ultimo_ataque": 0},
            
            # Ruta amarilla - 3 torres enemigas
            {"pos": [495, 230], "vida": 2000, "vida_max": 2000, "daño": 5, "daño_base": 5, 
             "reduccion_daño": 0, "rango": 200, "ruta": 0, "orden": 1, "destruida": False, "ultimo_ataque": 0},
            {"pos": [575, 180], "vida": 2000, "vida_max": 2000, "daño": 10, "daño_base": 10, 
             "reduccion_daño": 10, "rango": 200, "ruta": 0, "orden": 2, "destruida": False, "ultimo_ataque": 0},
            {"pos": [655, 130], "vida": 2000, "vida_max": 2000, "daño": 15, "daño_base": 15, 
             "reduccion_daño": 20, "rango": 200, "ruta": 0, "orden": 3, "destruida": False, "ultimo_ataque": 0},
        ]

    def configurar_inhibidores(self):
        """Configura los inhibidores con vida y temporizador de reconstrucción"""
        self.estructuras["inhibidores"]["aliados"] = [
            {"pos": [150, 480], "vida": 2500, "vida_max": 2500, "daño": 0, "rango": 0, 
             "ruta": 1, "destruido": False, "tiempo_reconstruccion": 0},
            {"pos": [50, 435], "vida": 2500, "vida_max": 2500, "daño": 0, "rango": 0, 
             "ruta": 2, "destruido": False, "tiempo_reconstruccion": 0},
            {"pos": [140, 435], "vida": 2500, "vida_max": 2500, "daño": 0, "rango": 0, 
             "ruta": 4, "destruido": False, "tiempo_reconstruccion": 0}
        ]
        
        self.estructuras["inhibidores"]["enemigos"] = [
            {"pos": [685, 120], "vida": 2500, "vida_max": 2500, "daño": 0, "rango": 0, 
             "ruta": 0, "destruido": False, "tiempo_reconstruccion": 0},
            {"pos": [750, 145], "vida": 2500, "vida_max": 2500, "daño": 0, "rango": 0, 
             "ruta": 3, "destruido": False, "tiempo_reconstruccion": 0},
            {"pos": [655, 80], "vida": 2500, "vida_max": 2500, "daño": 0, "rango": 0, 
             "ruta": 4, "destruido": False, "tiempo_reconstruccion": 0}
        ]

    def configurar_nexos(self):
        """Configura los nexos con vida y capacidad de ataque"""
        self.estructuras["nexos"]["aliados"] = [
            {"pos": [40, 490], "vida": 5000, "vida_max": 5000, "daño": 30, "rango": 250, 
             "puede_atacar": False, "destruido": False}
        ]
        
        self.estructuras["nexos"]["enemigos"] = [
            {"pos": [750, 70], "vida": 5000, "vida_max": 5000, "daño": 30, "rango": 250, 
             "puede_atacar": False, "destruido": False}
        ]

    def crear_rutas_fijas(self):
        """Crea las rutas fijas en el mapa"""
        # Ruta roja (superior)
        ruta_roja = {
            "color": (255, 0, 0),  # Rojo
            "puntos": [
                (49, 100),  # inicio
                (self.ANCHO - 49, 100)  # fin
            ]
        }

        # Ruta azul (inferior)
        ruta_azul = {
            "color": (0, 0, 255),  # Azul
            "puntos": [
                (49, self.ALTO - 100),
                (self.ANCHO - 49, self.ALTO - 100)
            ]
        }

        # Ruta roja izquierda (conecta arriba e abajo)
        ruta_roja_izq = {
            "color": (255, 0, 0),
            "puntos": [
                (49, 100),
                (49, self.ALTO - 100)
            ]
        }

        # Ruta blanca derecha (conecta arriba e abajo)
        ruta_azul_der = {
            "color": (0, 0, 255),
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
            ruta_azul, ruta_roja, ruta_roja_izq, ruta_azul_der, ruta_amarilla
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
        """Dibuja todas las torres con sus barras de vida"""
        for equipo in ["aliadas", "enemigas"]:
            for torre in self.estructuras["torres"][equipo]:
                if torre["destruida"]:
                    continue
                    
                # Dibujar torre
                img = self.torre_aliada_img if equipo == "aliadas" else self.torre_enemiga_img
                self.pantalla.blit(img, (torre["pos"][0] - 30, torre["pos"][1] - 30))
                
                # Barra de vida
                vida_width = 60
                vida_actual = max(0, (torre["vida"] / torre["vida_max"])) * vida_width
                pygame.draw.rect(self.pantalla, (100, 0, 0), 
                                (torre["pos"][0] - vida_width//2, torre["pos"][1] - 40, vida_width, 5))
                pygame.draw.rect(self.pantalla, (0, 255, 0), 
                                (torre["pos"][0] - vida_width//2, torre["pos"][1] - 40, vida_actual, 5))
                
                # Indicador de orden de torre
                orden_texto = self.fuente_pequena.render(str(torre["orden"]), True, (255, 255, 255))
                self.pantalla.blit(orden_texto, (torre["pos"][0] - orden_texto.get_width()//2, 
                                               torre["pos"][1] - orden_texto.get_height()//2))

    def dibujar_inhibidores(self):
        """Dibuja todos los inhibidores con sus barras de vida"""
        for equipo in ["aliados", "enemigos"]:
            for inhib in self.estructuras["inhibidores"][equipo]:
                if inhib["destruido"]:
                    # Mostrar temporizador de reconstrucción
                    tiempo_restante = max(0, 60 - inhib["tiempo_reconstruccion"])
                    tiempo_texto = self.fuente_pequena.render(f"{int(tiempo_restante)}", True, (255, 255, 255))
                    self.pantalla.blit(tiempo_texto, (inhib["pos"][0] - tiempo_texto.get_width()//2, 
                                     inhib["pos"][1] - tiempo_texto.get_height()//2))
                    continue
                    
                # Dibujar inhibidor
                img = self.inhibidor_aliado_img if equipo == "aliados" else self.inhibidor_enemigo_img
                self.pantalla.blit(img, (inhib["pos"][0] - 25, inhib["pos"][1] - 25))
                
                # Barra de vida
                vida_width = 50
                vida_actual = max(0, (inhib["vida"] / inhib["vida_max"])) * vida_width
                pygame.draw.rect(self.pantalla, (100, 0, 0), 
                                (inhib["pos"][0] - vida_width//2, inhib["pos"][1] - 35, vida_width, 5))
                pygame.draw.rect(self.pantalla, (0, 255, 0), 
                                (inhib["pos"][0] - vida_width//2, inhib["pos"][1] - 35, vida_actual, 5))

    def dibujar_nexos(self):
        """Dibuja todos los nexos con sus barras de vida"""
        for equipo in ["aliados", "enemigos"]:
            for nexo in self.estructuras["nexos"][equipo]:
                if nexo["destruido"]:
                    continue
                    
                # Dibujar nexo
                img = self.nexo_aliado_img if equipo == "aliados" else self.nexo_enemigo_img
                self.pantalla.blit(img, (nexo["pos"][0] - 40, nexo["pos"][1] - 40))
                
                # Barra de vida
                vida_width = 80
                vida_actual = max(0, (nexo["vida"] / nexo["vida_max"])) * vida_width
                pygame.draw.rect(self.pantalla, (100, 0, 0), 
                                (nexo["pos"][0] - vida_width//2, nexo["pos"][1] - 50, vida_width, 8))
                pygame.draw.rect(self.pantalla, (0, 255, 0), 
                                (nexo["pos"][0] - vida_width//2, nexo["pos"][1] - 50, vida_actual, 8))
                
                # Indicador de si puede atacar
                if nexo["puede_atacar"]:
                    ataque_texto = self.fuente_pequena.render("ATK", True, (255, 0, 0))
                    self.pantalla.blit(ataque_texto, (nexo["pos"][0] - ataque_texto.get_width()//2, 
                                                   nexo["pos"][1] + 30))

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
        
        # Barra de vida
        vida_width = 70
        vida_actual = max(0, (self.jugador["vida"] / self.jugador["vida_max"])) * vida_width
        pygame.draw.rect(self.pantalla, (255, 0, 0), 
                        (self.jugador["pos"][0] - vida_width//2, self.jugador["pos"][1] - 50, vida_width, 5))
        pygame.draw.rect(self.pantalla, (0, 255, 0), 
                        (self.jugador["pos"][0] - vida_width//2, self.jugador["pos"][1] - 50, vida_actual, 5))
    
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
            
            # Barra de vida
            vida_width = 70
            vida_actual = max(0, (datos["vida"] / datos["vida_max"])) * vida_width
            pygame.draw.rect(self.pantalla, (255, 0, 0), 
                            (datos["pos"][0] - vida_width//2, datos["pos"][1] - 50, vida_width, 5))
            pygame.draw.rect(self.pantalla, (0, 255, 0), 
                            (datos["pos"][0] - vida_width//2, datos["pos"][1] - 50, vida_actual, 5))

    def generar_oleada(self, equipo):
        """Genera una oleada de minions (melee, caster, cañón) con las rutas definidas"""
        # Esta función ahora solo se usa localmente cuando no hay conexión
        # Cuando hay conexión, el servidor envía las oleadas completas
        
        if self.conectado:
            return []  # El servidor enviará los minions
            
        oleada = []
        tipos_minions = ["melee", "caster", "siege"]  # 1 minion de cada tipo por ruta
    
        # Configuración base según el equipo
        if equipo == "aliados":
            try:
                punto_inicio = self.estructuras["nexos"]["aliados"][0]["pos"]  # Base aliada
                destino_final = self.estructuras["nexos"]["enemigos"][0]["pos"]  # Base enemiga
            except (KeyError, IndexError):
                punto_inicio = [40, 490]  # Valores por defecto si hay error
                destino_final = [750, 70]
    
            # Rutas para aliados (3 rutas distintas)
            rutas = [
                {  # Ruta 1: Inferior Azul -> Derecha Azul -> Base Enemiga
                    "id": "aliados_ruta_azul",
                    "puntos": self.mapa["rutas"][0]["puntos"].copy() +  # Ruta azul inferior (0)
                              self.mapa["rutas"][3]["puntos"][1:],      # Ruta derecha azul (3)
                    "destino": destino_final
                },
                {  # Ruta 2: Diagonal Amarilla directa
                    "id": "aliados_ruta_amarilla",
                    "puntos": self.mapa["rutas"][4]["puntos"].copy(),  # Ruta amarilla (4)
                    "destino": destino_final
                },
                {  # Ruta 3: Izquierda Roja -> Superior Roja -> Base Enemiga
                    "id": "aliados_ruta_roja",
                    "puntos": [
                        (40, 490),  # Base aliada (punto_inicio)
                        (49, self.ALTO - 100),  # Inicio ruta izquierda roja
                        (49, 100),              # Fin ruta izquierda roja
                        (self.ANCHO - 49, 100)  # Fin ruta superior roja
                    ],
                    "destino": destino_final
                }
            ]
        else:  # Enemigos
            try:
                punto_inicio = self.estructuras["nexos"]["enemigos"][0]["pos"]  # Base enemiga
                destino_final = self.estructuras["nexos"]["aliados"][0]["pos"]   # Base aliada
            except (KeyError, IndexError):
                punto_inicio = [750, 70]  # Valores por defecto si hay error
                destino_final = [40, 490]
    
            # Rutas para enemigos (3 rutas distintas)
            rutas = [
                {  # Ruta 1: Superior Roja -> Izquierda Roja -> Base Aliada
                    "id": "enemigos_ruta_roja",
                    "puntos": [punto_inicio] +  # Base enemiga
                              [(self.ANCHO - 49, 100), (49, 100)] +  # Ruta superior roja
                              [(49, self.ALTO - 100)],  # Ruta izquierda roja
                    "destino": destino_final
                },
                {  # Ruta 2: Diagonal Amarilla directa (invertida)
                    "id": "enemigos_ruta_amarilla",
                    "puntos": [punto_inicio] +  # Base enemiga
                              [(self.ANCHO - 49, 100), (49, self.ALTO - 100)],  # Ruta amarilla
                    "destino": destino_final
                },
                {  # Ruta 3: Derecha Azul -> Inferior Azul -> Base Aliada
                    "id": "enemigos_ruta_azul",
                    "puntos": [
                        (750, 70),  # Base enemiga
                        (self.ANCHO - 49, 100),  # Inicio ruta derecha azul
                        (self.ANCHO - 49, self.ALTO - 100),  # Fin ruta derecha azul
                        (49, self.ALTO - 100)  # Base aliada
                    ],
                    "destino": destino_final
                }
            ]
    
        for ruta in rutas:
            for tipo in tipos_minions:
                stats = {
                    "melee": {"vida": 100, "daño": 15, "velocidad": 2, "rango_ataque": 40},
                    "caster": {"vida": 60, "daño": 25, "velocidad": 1.8, "rango_ataque": 80},
                    "siege": {"vida": 150, "daño": 40, "velocidad": 1.5, "rango_ataque": 120}
                }.get(tipo, {"vida": 100, "daño": 15, "velocidad": 2, "rango_ataque": 40})  # Default si no encuentra el tipo
    
                oleada.append({
                    "tipo": tipo,
                    "vida": stats["vida"],
                    "vida_max": stats["vida"],
                    "daño": stats["daño"],
                    "velocidad": stats["velocidad"],
                    "ruta_id": ruta["id"],
                    "pos": list(punto_inicio),
                    "objetivo": None,
                    "equipo": equipo,
                    "rango_ataque": stats["rango_ataque"],
                    "destino": ruta["destino"],
                    "puntos_ruta": ruta["puntos"].copy(),
                    "indice_punto_actual": 0,
                    "reduccion_daño": 0  # Añadido para consistencia
                })
    
        return oleada
    
    def calcular_velocidad(self, ruta, tiempo_objetivo_segundos):
        """Calcula la velocidad necesaria para llegar a la mitad de la ruta en el tiempo objetivo"""
        if len(ruta["puntos"]) < 2:
            return 2  # Valor por defecto
        
        # Calcular distancia total de la ruta
        x1, y1 = ruta["puntos"][0]
        x2, y2 = ruta["puntos"][-1]
        distancia_total = ((x2 - x1)**2 + (y2 - y1)**2)**0.5
        
        # Distancia a la mitad de la ruta
        distancia_mitad = distancia_total / 2
        
        # Velocidad = distancia / tiempo (convertir segundos a frames)
        velocidad = distancia_mitad / (tiempo_objetivo_segundos * 60)  # 60 FPS
        
        return max(velocidad, 0.5)  # Velocidad mínima

    def actualizar_oleadas(self, dt):
        """Actualiza el temporizador de oleadas y genera nuevas si es necesario"""
        # Solo actualizar localmente si no hay conexión al servidor
        if not self.conectado:
            self.oleadas["tiempo_juego"] += dt / 1000  # Convertir ms a segundos
            
            # La primera oleada sale a los 65 segundos (1:05)
            if not self.oleadas["primer_oleada"] and self.oleadas["tiempo_juego"] >= 65:
                self.oleadas["primer_oleada"] = True
                self.oleadas["tiempo_ultima_oleada"] = self.oleadas["tiempo_juego"]
                self.oleadas["contador_oleadas"] += 1
                
                # Generar oleadas para ambos equipos (solo en modo local)
                self.minions["aliados"].extend(self.generar_oleada("aliados"))
                self.minions["enemigos"].extend(self.generar_oleada("enemigos"))
                return
            
            tiempo_desde_ultima = self.oleadas["tiempo_juego"] - self.oleadas["tiempo_ultima_oleada"]
            
            if tiempo_desde_ultima >= self.oleadas["intervalo"] and self.oleadas["primer_oleada"]:
                self.oleadas["tiempo_ultima_oleada"] = self.oleadas["tiempo_juego"]
                self.oleadas["contador_oleadas"] += 1
                
                # Generar oleadas para ambos equipos (solo en modo local)
                self.minions["aliados"].extend(self.generar_oleada("aliados"))
                self.minions["enemigos"].extend(self.generar_oleada("enemigos"))
        else:
            # Cuando hay conexión, solo actualizamos el tiempo localmente
            # (el servidor enviará las oleadas completas cuando corresponda)
            self.oleadas["tiempo_juego"] += dt / 1000

    def actualizar_minions(self):
        """Actualiza el movimiento de los minions según sus rutas asignadas"""
        for equipo in ["aliados", "enemigos"]:
            for minion in self.minions[equipo][:]:
                # --- Movimiento ---
                puntos_ruta = minion["puntos_ruta"]
                indice_punto = minion["indice_punto_actual"]

                # Si no quedan puntos, ir al destino final
                if indice_punto >= len(puntos_ruta):
                    destino = minion["destino"]
                else:
                    destino = puntos_ruta[indice_punto]

                # Calcular dirección y mover
                dx = destino[0] - minion["pos"][0]
                dy = destino[1] - minion["pos"][1]
                distancia = (dx**2 + dy**2)**0.5

                if distancia > 5:  # Mover si no ha llegado al punto
                    minion["pos"][0] += (dx / distancia) * minion["velocidad"]
                    minion["pos"][1] += (dy / distancia) * minion["velocidad"]
                else:
                    minion["indice_punto_actual"] += 1  # Pasar al siguiente punto

                # --- Verificar si llegó al final de la ruta ---
                if indice_punto >= len(puntos_ruta):
                    distancia_final = ((minion["pos"][0] - minion["destino"][0])**2 + 
                                     (minion["pos"][1] - minion["destino"][1])**2)**0.5
                    if distancia_final < 10:  # Si llegó a la base enemiga
                        self.minions[equipo].remove(minion)
                        # Aquí podrías añadir daño al nexo si es necesario

                # --- Ataque a estructuras/enemigos (opcional) ---
                self.verificar_ataque(minion)

    def verificar_ataque(self, minion):
        """Verifica si el minion está en rango de ataque de una estructura enemiga"""
        estructuras_enemigas = []
        if minion["equipo"] == "aliados":
            # Aliados atacan torres, inhibidores y nexos enemigos
            estructuras_enemigas = (
                [(t["pos"][0], t["pos"][1], "torre") for t in self.estructuras["torres"]["enemigas"] if not t["destruida"]] +
                [(i["pos"][0], i["pos"][1], "inhibidor") for i in self.estructuras["inhibidores"]["enemigos"] if not i["destruido"]] +
                [(n["pos"][0], n["pos"][1], "nexo") for n in self.estructuras["nexos"]["enemigos"] if not n["destruido"]]
            )
        else:
            # Enemigos atacan torres, inhibidores y nexos aliados
            estructuras_enemigas = (
                [(t["pos"][0], t["pos"][1], "torre") for t in self.estructuras["torres"]["aliadas"] if not t["destruida"]] +
                [(i["pos"][0], i["pos"][1], "inhibidor") for i in self.estructuras["inhibidores"]["aliados"] if not i["destruido"]] +
                [(n["pos"][0], n["pos"][1], "nexo") for n in self.estructuras["nexos"]["aliados"] if not n["destruido"]]
            )
    
        for ex, ey, tipo in estructuras_enemigas:
            distancia = ((minion["pos"][0] - ex)**2 + 
                       (minion["pos"][1] - ey)**2)**0.5
            if distancia < minion["rango_ataque"]:
                minion["objetivo"] = (ex, ey, tipo)
                # Aquí podrías agregar lógica para dañar la estructura
                break

    def verificar_torres_ruta_destruidas(self, ruta, equipo):
        """Verifica si todas las torres de una ruta están destruidas"""
        torres_ruta = [t for t in self.estructuras["torres"][equipo] if t["ruta"] == ruta]
        return all(t["destruida"] for t in torres_ruta)


    def actualizar_estructuras(self, dt):
        """Actualización completa del estado de todas las estructuras"""
        # Actualizar tiempo de reconstrucción de inhibidores
        for equipo in ["aliados", "enemigos"]:
            for inhib in self.estructuras["inhibidores"][equipo]:
                if inhib["destruido"]:
                    inhib["tiempo_reconstruccion"] += dt / 1000  # ms a segundos
                    
                    # Reconstruir después de 60 segundos
                    if inhib["tiempo_reconstruccion"] >= 60:
                        inhib["vida"] = inhib["vida_max"]
                        inhib["destruido"] = False
                        inhib["tiempo_reconstruccion"] = 0
                        
                        # Verificar si debemos desactivar el nexo opuesto
                        equipo_opuesto = "enemigos" if equipo == "aliados" else "aliados"
                        for nexo in self.estructuras["nexos"][equipo_opuesto]:
                            # Verificar si quedan inhibidores destruidos
                            inhibidores_destruidos = [i for i in self.estructuras["inhibidores"][equipo]
                                            if i["destruido"]]
                            nexo["puede_atacar"] = len(inhibidores_destruidos) > 0
        
        # Actualizar estado de ataque de los nexos (por si algún cambio no fue detectado)
        for nexo in self.estructuras["nexos"]["aliados"]:
            inhibidores_destruidos = [i for i in self.estructuras["inhibidores"]["enemigos"] 
                                    if i["destruido"]]
            nexo["puede_atacar"] = len(inhibidores_destruidos) > 0
        
        for nexo in self.estructuras["nexos"]["enemigos"]:
            inhibidores_destruidos = [i for i in self.estructuras["inhibidores"]["aliados"] 
                                    if i["destruido"]]
            nexo["puede_atacar"] = len(inhibidores_destruidos) > 0
        
        # Actualizar cooldown de ataques de torres
        tiempo_actual = self.oleadas["tiempo_juego"]
        for equipo in ["aliadas", "enemigas"]:
            for torre in self.estructuras["torres"][equipo]:
                if not torre["destruida"] and tiempo_actual - torre["ultimo_ataque"] >= 10:
                    torre["puede_atacar"] = True
                else:
                    torre["puede_atacar"] = False

    def atacar_estructuras(self):
        """Las estructuras atacan a los objetivos en su rango con cooldown"""
        tiempo_actual = self.oleadas["tiempo_juego"]
        
        # Torres atacan
        for equipo in ["aliadas", "enemigas"]:
            for torre in self.estructuras["torres"][equipo]:
                if torre["destruida"]:
                    continue
                    
                # Verificar cooldown (10 segundos entre ataques)
                if tiempo_actual - torre["ultimo_ataque"] < 10:
                    continue
                    
                # Obtener posición de la torre como float
                try:
                    torre_x = float(torre["pos"][0])
                    torre_y = float(torre["pos"][1])
                except (KeyError, TypeError, ValueError):
                    continue
                    
                # Buscar objetivos (jugadores o minions enemigos)
                objetivos = []
                equipo_opuesto = "enemigos" if equipo == "aliadas" else "aliados"
                
                # Minions enemigos
                for minion in self.minions[equipo_opuesto][:]:  # Usamos [:] para hacer una copia
                    try:
                        minion_x = float(minion["pos"][0])
                        minion_y = float(minion["pos"][1])
                        
                        distancia = ((torre_x - minion_x)**2 + 
                                   (torre_y - minion_y)**2)**0.5
                        if distancia <= torre["rango"]:
                            objetivos.append(("minion", minion))
                    except (KeyError, TypeError, ValueError):
                        # Si hay un error con este minion, lo eliminamos
                        if minion in self.minions[equipo_opuesto]:
                            self.minions[equipo_opuesto].remove(minion)
                        continue
                    
                # Jugadores enemigos
                if equipo == "aliadas":
                    for jugador_id, jugador in self.otros_jugadores.items():
                        try:
                            jugador_x = float(jugador["pos"][0])
                            jugador_y = float(jugador["pos"][1])
                            distancia = ((torre_x - jugador_x)**2 + 
                                       (torre_y - jugador_y)**2)**0.5
                            if distancia <= torre["rango"]:
                                objetivos.append(("jugador", jugador))
                        except (KeyError, TypeError, ValueError):
                            continue
                else:
                    try:
                        jugador_x = float(self.jugador["pos"][0])
                        jugador_y = float(self.jugador["pos"][1])
                        distancia = ((torre_x - jugador_x)**2 + 
                                   (torre_y - jugador_y)**2)**0.5
                        if distancia <= torre["rango"]:
                            objetivos.append(("jugador", self.jugador))
                    except (KeyError, TypeError, ValueError):
                        pass
                    
                # Atacar al primer objetivo encontrado
                if objetivos:
                    tipo, objetivo = objetivos[0]
                    try:
                        daño_real = torre["daño"] * (1 - objetivo.get("reduccion_daño", 0) / 100)
                        
                        if tipo == "minion":
                            objetivo["vida"] -= daño_real
                            if objetivo["vida"] <= 0:
                                self.minions[equipo_opuesto].remove(objetivo)
                        else:  # jugador
                            objetivo["vida"] -= daño_real
                        
                        # Actualizar tiempo del último ataque
                        torre["ultimo_ataque"] = tiempo_actual
                        
                        # Notificar al servidor si la torre destruyó algo
                        if tipo == "minion" and objetivo["vida"] <= 0 and self.conectado:
                            self.enviar_mensaje("minion_destruido", {
                                "equipo": equipo_opuesto,
                                "tipo": objetivo["tipo"]
                            })
                    except (KeyError, TypeError, ValueError):
                        pass
            
        # Nexos atacan (si pueden)
        for equipo in ["aliados", "enemigos"]:
            for nexo in self.estructuras["nexos"][equipo]:
                if nexo["destruido"] or not nexo["puede_atacar"]:
                    continue
                    
                # Obtener posición del nexo como float
                try:
                    nexo_x = float(nexo["pos"][0])
                    nexo_y = float(nexo["pos"][1])
                except (KeyError, TypeError, ValueError):
                    continue
                    
                # Buscar objetivos
                objetivos = []
                equipo_opuesto = "enemigos" if equipo == "aliados" else "aliados"
                
                # Minions enemigos
                for minion in self.minions[equipo_opuesto][:]:
                    try:
                        minion_x = float(minion["pos"][0])
                        minion_y = float(minion["pos"][1])
                        
                        distancia = ((nexo_x - minion_x)**2 + 
                                   (nexo_y - minion_y)**2)**0.5
                        if distancia <= nexo["rango"]:
                            objetivos.append(("minion", minion))
                    except (KeyError, TypeError, ValueError):
                        if minion in self.minions[equipo_opuesto]:
                            self.minions[equipo_opuesto].remove(minion)
                        continue
                    
                # Jugadores enemigos
                if equipo == "aliados":
                    for jugador_id, jugador in self.otros_jugadores.items():
                        try:
                            jugador_x = float(jugador["pos"][0])
                            jugador_y = float(jugador["pos"][1])
                            distancia = ((nexo_x - jugador_x)**2 + 
                                       (nexo_y - jugador_y)**2)**0.5
                            if distancia <= nexo["rango"]:
                                objetivos.append(("jugador", jugador))
                        except (KeyError, TypeError, ValueError):
                            continue
                else:
                    try:
                        jugador_x = float(self.jugador["pos"][0])
                        jugador_y = float(self.jugador["pos"][1])
                        distancia = ((nexo_x - jugador_x)**2 + 
                                   (nexo_y - jugador_y)**2)**0.5
                        if distancia <= nexo["rango"]:
                            objetivos.append(("jugador", self.jugador))
                    except (KeyError, TypeError, ValueError):
                        pass
                    
                # Atacar al primer objetivo encontrado
                if objetivos:
                    tipo, objetivo = objetivos[0]
                    try:
                        daño_real = nexo["daño"] * (1 - objetivo.get("reduccion_daño", 0) / 100)
                        
                        if tipo == "minion":
                            objetivo["vida"] -= daño_real
                            if objetivo["vida"] <= 0:
                                self.minions[equipo_opuesto].remove(objetivo)
                                if self.conectado:
                                    self.enviar_mensaje("minion_destruido", {
                                        "equipo": equipo_opuesto,
                                        "tipo": objetivo["tipo"]
                                    })
                        else:  # jugador
                            objetivo["vida"] -= daño_real
                    except (KeyError, TypeError, ValueError):
                        pass

    def verificar_estado_juego(self):
        """Verificación completa del estado de victoria/derrota"""
        # Verificar nexo aliado
        for nexo in self.estructuras["nexos"]["aliados"]:
            if nexo["destruido"]:
                self.mostrar_mensaje_fin("¡Derrota! El nexo aliado fue destruido")
                return True
        
        # Verificar nexo enemigo
        for nexo in self.estructuras["nexos"]["enemigos"]:
            if nexo["destruido"]:
                self.mostrar_mensaje_fin("¡Victoria! El nexo enemigo fue destruido")
                return True
        
        return False

    def mostrar_mensaje_fin(self, mensaje):
        """Muestra un mensaje de fin de juego"""
        self.estado = "fin"
        self.mensaje_fin = mensaje

    def dibujar_minions(self):
        """Dibuja minions con barras de vida y colores de equipo"""
        for equipo in ["aliados", "enemigos"]:
            for minion in self.minions[equipo]:
                img = self.imagenes_minions.get(minion["tipo"], None)
                if img:
                    self.pantalla.blit(img, (minion["pos"][0] - img.get_width()//2, 
                                        minion["pos"][1] - img.get_height()//2))
                
                # Barra de vida
                vida_width = 40
                vida_actual = max(0, (minion["vida"] / minion["vida_max"])) * vida_width
                
                # Fondo rojo oscuro
                pygame.draw.rect(self.pantalla, (100, 0, 0), 
                                (minion["pos"][0] - vida_width//2, minion["pos"][1] - 30, vida_width, 5))
                
                # Vida (azul para aliados, rojo para enemigos)
                color_vida = (0, 100, 255) if equipo == "aliados" else (255, 50, 50)
                pygame.draw.rect(self.pantalla, color_vida, 
                                (minion["pos"][0] - vida_width//2, minion["pos"][1] - 30, vida_actual, 5))

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
                    if self.conectar_servidor("26.176.7.141", 5555):
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
        
        elif self.estado == "fin":
            # Botón para volver al menú
            if (self.ANCHO//2 - 100 <= x <= self.ANCHO//2 + 100 and 
                self.ALTO//2 + 50 <= y <= self.ALTO//2 + 100):
                self.estado = "menu"
                self.reiniciar_juego()

    def conectar_servidor(self, ip_servidor, puerto):
        """Conectar al servidor de juego"""
        try:
            self.socket_cliente = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.socket_cliente.connect((ip_servidor, puerto))
            self.conectado = True
            
            # Enviar mensaje inicial de conexión
            self.enviar_mensaje("conectar", {})
            
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
                print(f"Datos recibidos: {datos}")  # Debug
                if datos:
                    mensajes = datos.split('|')
                    for msg in mensajes:
                        if msg:
                            print(f"Procesando mensaje: {msg}")  # Debug
                            self.procesar_mensaje(json.loads(msg))
            except Exception as e:
                print(f"Error recibiendo datos: {e}")
                self.conectado = False
                break

    def actualizar_estado_juego(self, estado):
        """Actualiza el estado completo del juego con los datos del servidor"""
        try:
            # Actualizar mapa
            if "mapa" in estado:
                self.mapa["rutas"] = estado["mapa"].get("rutas", [])
                self.mapa["scroll_y"] = estado["mapa"].get("scroll_y", 0)
            
            # Actualizar estructuras
            if "estructuras" in estado:
                for tipo_estructura, equipos in estado["estructuras"].items():
                    if tipo_estructura in self.estructuras:
                        for equipo, estructuras in equipos.items():
                            if equipo in self.estructuras[tipo_estructura]:
                                # Actualizar solo si el número de estructuras coincide
                                if len(estructuras) == len(self.estructuras[tipo_estructura][equipo]):
                                    for i, estructura in enumerate(estructuras):
                                        if i < len(self.estructuras[tipo_estructura][equipo]):
                                            self.estructuras[tipo_estructura][equipo][i].update({
                                                "vida": float(estructura.get("vida", 100)),
                                                "destruida": bool(estructura.get("destruida", False)),
                                                "puede_atacar": bool(estructura.get("puede_atacar", False)),
                                                "tiempo_reconstruccion": float(estructura.get("tiempo_reconstruccion", 0))
                                            })
            
            # Actualizar minions
            if "minions" in estado:
                for equipo, minions in estado["minions"].items():
                    if equipo in self.minions:
                        self.minions[equipo] = []
                        for minion in minions:
                            try:
                                self.minions[equipo].append({
                                    "tipo": str(minion.get("tipo", "melee")),
                                    "vida": float(minion.get("vida", 100)),
                                    "vida_max": float(minion.get("vida_max", 100)),
                                    "daño": float(minion.get("daño", 15)),
                                    "velocidad": float(minion.get("velocidad", 2)),
                                    "ruta_id": str(minion.get("ruta_id", "")),
                                    "pos": [float(minion.get("pos", [0, 0])[0]), float(minion.get("pos", [0, 0])[1])],
                                    "objetivo": minion.get("objetivo"),
                                    "equipo": str(minion.get("equipo", "aliados")),
                                    "rango_ataque": float(minion.get("rango_ataque", 40)),
                                    "destino": [float(minion.get("destino", [0, 0])[0]), float(minion.get("destino", [0, 0])[1])],
                                    "puntos_ruta": [[float(p[0]), float(p[1])] for p in minion.get("puntos_ruta", [])],
                                    "indice_punto_actual": int(minion.get("indice_punto_actual", 0)),
                                    "reduccion_daño": float(minion.get("reduccion_daño", 0))
                                })
                            except (KeyError, TypeError, ValueError):
                                continue
            
            # Actualizar oleadas
            if "oleadas" in estado:
                self.oleadas.update({
                    "tiempo_ultima_oleada": float(estado["oleadas"].get("tiempo_ultima_oleada", 0)),
                    "intervalo": float(estado["oleadas"].get("intervalo", 30)),
                    "contador_oleadas": int(estado["oleadas"].get("contador_oleadas", 0)),
                    "tiempo_juego": float(estado["oleadas"].get("tiempo_juego", 0)),
                    "primer_oleada": bool(estado["oleadas"].get("primer_oleada", False))
                })
        
        except Exception as e:
            print(f"Error actualizando estado del juego: {e}")

    def procesar_mensaje(self, mensaje):
        """Procesar mensajes recibidos del servidor"""
        try:
            tipo = mensaje.get("tipo")
            
            if tipo == "bienvenida":
                print(f"Conectado al servidor: {mensaje.get('mensaje')}")
                self.id_cliente = mensaje.get("id")
                
                # Actualizar lista de jugadores con los datos recibidos
                if "jugadores" in mensaje:
                    self.otros_jugadores = {
                        id_jugador: {
                            "nombre": str(datos.get("nombre", f"Jugador{id_jugador}"))[:16],
                            "personaje": int(datos.get("personaje", 1)),
                            "vida": float(datos.get("vida", 100)),
                            "vida_max": float(datos.get("vida_max", 100)),
                            "pos": [float(datos.get("pos", [0, 0])[0]), float(datos.get("pos", [0, 0])[1])],
                            "velocidad": float(datos.get("velocidad", 5)),
                            "daño": float(datos.get("daño", 20)),
                            "nivel": int(datos.get("nivel", 1)),
                            "experiencia": float(datos.get("experiencia", 0)),
                            "reduccion_daño": float(datos.get("reduccion_daño", 0))
                        }
                        for id_jugador, datos in mensaje["jugadores"].items()
                    }
                
                # Actualizar estado completo del juego si está en el mensaje
                if "estado_juego" in mensaje:
                    self.actualizar_estado_juego(mensaje["estado_juego"])
                
                # Actualizar oleadas si están en el mensaje
                if "oleada" in mensaje:
                    self.oleadas.update({
                        "contador_oleadas": int(mensaje["oleada"].get("contador", 0)),
                        "tiempo_juego": float(mensaje["oleada"].get("tiempo", 0))
                    })
            
            elif tipo == "jugadores":
                # Validar estructura de los jugadores
                jugadores_validos = {}
                for id_jugador, datos in mensaje.get("jugadores", {}).items():
                    try:
                        jugadores_validos[id_jugador] = {
                            "nombre": str(datos.get("nombre", f"Jugador{id_jugador}"))[:16],
                            "personaje": int(datos.get("personaje", 1)),
                            "vida": float(datos.get("vida", 100)),
                            "vida_max": float(datos.get("vida_max", 100)),
                            "pos": [float(datos.get("pos", [0, 0])[0]), float(datos.get("pos", [0, 0])[1])],
                            "velocidad": float(datos.get("velocidad", 5)),
                            "daño": float(datos.get("daño", 20)),
                            "nivel": int(datos.get("nivel", 1)),
                            "experiencia": float(datos.get("experiencia", 0)),
                            "reduccion_daño": float(datos.get("reduccion_daño", 0))
                        }
                    except (KeyError, TypeError, ValueError):
                        continue
                self.otros_jugadores = jugadores_validos
            
            elif tipo == "nuevo_jugador":
                try:
                    self.otros_jugadores[mensaje["id"]] = {
                        "nombre": str(mensaje.get("nombre", f"Jugador{mensaje['id']}"))[:16],
                        "personaje": int(mensaje.get("personaje", 1)),
                        "vida": float(mensaje.get("vida", 100)),
                        "vida_max": float(mensaje.get("vida_max", 100)),
                        "pos": [float(mensaje.get("pos", [0, 0])[0]), float(mensaje.get("pos", [0, 0])[1])],
                        "velocidad": float(mensaje.get("velocidad", 5)),
                        "daño": float(mensaje.get("daño", 20)),
                        "nivel": int(mensaje.get("nivel", 1)),
                        "experiencia": float(mensaje.get("experiencia", 0)),
                        "reduccion_daño": float(mensaje.get("reduccion_daño", 0))
                    }
                except (KeyError, TypeError, ValueError):
                    pass
            
            elif tipo == "jugador_desconectado":
                if mensaje["id"] in self.otros_jugadores:
                    del self.otros_jugadores[mensaje["id"]]
            
            elif tipo == "actualizacion_posicion":
                if mensaje["id"] in self.otros_jugadores:
                    try:
                        self.otros_jugadores[mensaje["id"]]["pos"] = [
                            float(mensaje["pos"][0]),
                            float(mensaje["pos"][1])
                        ]
                    except (KeyError, TypeError, ValueError):
                        pass
            
            elif tipo == "nueva_oleada":
                try:
                    self.oleadas["contador_oleadas"] = int(mensaje.get("contador", 0))
                    self.oleadas["tiempo_juego"] = float(mensaje.get("tiempo", 0))
                    
                    # No limpiar minions aquí, el servidor enviará el estado completo
                except (KeyError, TypeError, ValueError):
                    pass
            
            elif tipo == "estado_juego":
                self.actualizar_estado_juego(mensaje)
            
            elif tipo == "estructura_destruida":
                try:
                    tipo_estructura = mensaje.get("tipo")
                    equipo = mensaje.get("equipo")
                    indice = mensaje.get("indice")
                    
                    if (tipo_estructura in self.estructuras and 
                        equipo in self.estructuras[tipo_estructura] and
                        indice < len(self.estructuras[tipo_estructura][equipo])):
                        
                        self.estructuras[tipo_estructura][equipo][indice]["destruida"] = True
                except (KeyError, TypeError, ValueError):
                    pass
        
        except Exception as e:
            print(f"Error procesando mensaje: {e}")

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

    def reiniciar_juego(self):
        """Reinicia el estado del juego para una nueva partida"""
        self.__init__()
    
    

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
                
                dt = self.reloj.get_time()  # Obtener tiempo desde el último frame
                self.actualizar_oleadas(dt)
                self.actualizar_estructuras(dt)
                self.atacar_estructuras()
                self.manejar_movimiento()
                self.actualizar_minions()
                self.dibujar_mapa()
                self.dibujar_torres()
                self.dibujar_inhibidores()
                self.dibujar_nexos()
                self.dibujar_minions()
                self.dibujar_jugador()
                self.dibujar_otros_jugadores()
                
                # Footer: Mostrar coordenadas, oleada y tiempo en la parte inferior
                footer_y = self.ALTO - 30
                coordenadas_texto = self.fuente_normal.render(
                    f"Posición: ({int(self.jugador['pos'][0])}, {int(self.jugador['pos'][1])})",
                    True,
                    (255, 255, 255)
                )
                self.pantalla.blit(coordenadas_texto, (20, footer_y))
                
                # Mostrar información de minions
                tiempo_minutos = int(self.oleadas["tiempo_juego"] // 60)
                tiempo_segundos = int(self.oleadas["tiempo_juego"] % 60)
                minions_texto = self.fuente_pequena.render(
                    f"Oleada: {self.oleadas['contador_oleadas']} | Tiempo: {tiempo_minutos}:{tiempo_segundos:02d}",
                    True, 
                    (255, 255, 255)
                )
                self.pantalla.blit(minions_texto, (self.ANCHO // 2 - minions_texto.get_width() // 2, footer_y + 5))
                
                # Mostrar estado de conexión
                if not self.conectado:
                    error_texto = self.fuente_normal.render("DESCONECTADO", True, (255, 0, 0))
                    self.pantalla.blit(error_texto, (self.ANCHO - error_texto.get_width() - 20, 20))
                
                # Verificar si el juego terminó
                self.verificar_estado_juego()
            
            elif self.estado == "fin":
                # Pantalla de fin de juego
                self.pantalla.fill((0, 0, 0))
                fin_texto = self.fuente_titulo.render(self.mensaje_fin, True, (255, 255, 255))
                self.pantalla.blit(fin_texto, (self.ANCHO//2 - fin_texto.get_width()//2, 
                                           self.ALTO//2 - fin_texto.get_height()//2))
                
                # Botón para volver al menú
                pygame.draw.rect(self.pantalla, (70, 130, 180), (self.ANCHO//2 - 100, self.ALTO//2 + 50, 200, 50))
                menu_texto = self.fuente_normal.render("Volver al menú", True, (255, 255, 255))
                self.pantalla.blit(menu_texto, (self.ANCHO//2 - menu_texto.get_width()//2, 
                                             self.ALTO//2 + 65))
            
            pygame.display.flip()
            self.reloj.tick(60)

if __name__ == "__main__":
    juego = Juego()
    juego.ejecutar()