# servidor.py - Servidor para el juego multijugador (versión completa)
import socket
import json
import threading
import time
from datetime import datetime

class Servidor:
    def __init__(self, host='0.0.0.0', port=5555):
        self.host = host
        self.port = port
        self.server = None
        self.clientes = {}
        self.lock = threading.Lock()
        
        # Estado completo del juego compartido
        self.estado_juego = {
            "mapa": {
                "rutas": [
                    # Ruta azul (inferior)
                    {"color": [0, 0, 255], "puntos": [(49, 500), (751, 500)]},
                    # Ruta roja (superior)
                    {"color": [255, 0, 0], "puntos": [(49, 100), (751, 100)]},
                    # Ruta izquierda (vertical)
                    {"color": [255, 0, 0], "puntos": [(49, 100), (49, 500)]},
                    # Ruta derecha (vertical)
                    {"color": [0, 0, 255], "puntos": [(751, 100), (751, 500)]},
                    # Ruta diagonal amarilla
                    {"color": [255, 255, 0], "puntos": [(49, 500), (751, 100)]}
                ],
                "scroll_y": 0
            },
            "estructuras": {
                "torres": {
                    "aliadas": [
                        {"pos": [200, 480], "vida": 2000, "destruida": False, "ruta": 1, "orden": 3},
                        {"pos": [400, 480], "vida": 2000, "destruida": False, "ruta": 1, "orden": 2},
                        {"pos": [600, 480], "vida": 2000, "destruida": False, "ruta": 1, "orden": 1},
                        {"pos": [50, 170], "vida": 2000, "destruida": False, "ruta": 2, "orden": 1},
                        {"pos": [50, 300], "vida": 2000, "destruida": False, "ruta": 2, "orden": 2},
                        {"pos": [50, 400], "vida": 2000, "destruida": False, "ruta": 2, "orden": 3},
                        {"pos": [160, 415], "vida": 2000, "destruida": False, "ruta": 4, "orden": 3},
                        {"pos": [275, 355], "vida": 2000, "destruida": False, "ruta": 4, "orden": 2},
                        {"pos": [375, 300], "vida": 2000, "destruida": False, "ruta": 4, "orden": 1}
                    ],
                    "enemigas": [
                        {"pos": [200, 80], "vida": 2000, "destruida": False, "ruta": 0, "orden": 1},
                        {"pos": [400, 80], "vida": 2000, "destruida": False, "ruta": 0, "orden": 2},
                        {"pos": [600, 80], "vida": 2000, "destruida": False, "ruta": 0, "orden": 3},
                        {"pos": [750, 170], "vida": 2000, "destruida": False, "ruta": 3, "orden": 3},
                        {"pos": [750, 300], "vida": 2000, "destruida": False, "ruta": 3, "orden": 2},
                        {"pos": [750, 400], "vida": 2000, "destruida": False, "ruta": 3, "orden": 1},
                        {"pos": [495, 230], "vida": 2000, "destruida": False, "ruta": 0, "orden": 1},
                        {"pos": [575, 180], "vida": 2000, "destruida": False, "ruta": 0, "orden": 2},
                        {"pos": [655, 130], "vida": 2000, "destruida": False, "ruta": 0, "orden": 3}
                    ]
                },
                "inhibidores": {
                    "aliados": [
                        {"pos": [150, 480], "vida": 2500, "destruido": False, "ruta": 1},
                        {"pos": [50, 435], "vida": 2500, "destruido": False, "ruta": 2},
                        {"pos": [140, 435], "vida": 2500, "destruido": False, "ruta": 4}
                    ],
                    "enemigos": [
                        {"pos": [685, 120], "vida": 2500, "destruido": False, "ruta": 0},
                        {"pos": [750, 145], "vida": 2500, "destruido": False, "ruta": 3},
                        {"pos": [655, 80], "vida": 2500, "destruido": False, "ruta": 4}
                    ]
                },
                "nexos": {
                    "aliados": [
                        {"pos": [40, 490], "vida": 5000, "destruido": False, "puede_atacar": False}
                    ],
                    "enemigos": [
                        {"pos": [750, 70], "vida": 5000, "destruido": False, "puede_atacar": False}
                    ]
                }
            },
            "minions": {
                "aliados": [],
                "enemigos": []
            },
            "oleadas": {
                "tiempo_ultima_oleada": 0,
                "intervalo": 30,
                "contador_oleadas": 0,
                "tiempo_juego": 0,
                "primer_oleada": False
            }
        }

        self.iniciar_servidor()

    def iniciar_servidor(self):
        """Inicia el servidor y acepta conexiones entrantes"""
        self.server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.server.bind((self.host, self.port))
        self.server.listen(5)
        print(f"Servidor iniciado en {self.host}:{self.port}")

        # Hilo para actualizar el tiempo del juego y oleadas
        threading.Thread(target=self.actualizar_tiempo_juego, daemon=True).start()

        # Aceptar conexiones entrantes
        while True:
            cliente, direccion = self.server.accept()
            print(f"Nueva conexión desde {direccion}")
            threading.Thread(target=self.manejar_cliente, args=(cliente,), daemon=True).start()

    def actualizar_tiempo_juego(self):
        """Actualiza el tiempo del juego y gestiona las oleadas"""
        while True:
            time.sleep(1)  # Actualizar cada segundo
            with self.lock:
                self.estado_juego["oleadas"]["tiempo_juego"] += 1
                tiempo = self.estado_juego["oleadas"]["tiempo_juego"]

                # Primera oleada a los 65 segundos (1:05)
                if not self.estado_juego["oleadas"]["primer_oleada"] and tiempo >= 65:
                    self.estado_juego["oleadas"]["primer_oleada"] = True
                    self.estado_juego["oleadas"]["tiempo_ultima_oleada"] = tiempo
                    self.estado_juego["oleadas"]["contador_oleadas"] += 1
                    self.generar_oleada("aliados")
                    self.generar_oleada("enemigos")
                    self.enviar_a_todos("nueva_oleada", {
                        "contador": self.estado_juego["oleadas"]["contador_oleadas"],
                        "tiempo": tiempo
                    })
                
                # Oleadas posteriores cada 30 segundos
                tiempo_desde_ultima = tiempo - self.estado_juego["oleadas"]["tiempo_ultima_oleada"]
                if (tiempo_desde_ultima >= self.estado_juego["oleadas"]["intervalo"] and 
                    self.estado_juego["oleadas"]["primer_oleada"]):
                    self.estado_juego["oleadas"]["tiempo_ultima_oleada"] = tiempo
                    self.estado_juego["oleadas"]["contador_oleadas"] += 1
                    self.generar_oleada("aliados")
                    self.generar_oleada("enemigos")
                    self.enviar_a_todos("nueva_oleada", {
                        "contador": self.estado_juego["oleadas"]["contador_oleadas"],
                        "tiempo": tiempo
                    })

                # Enviar estado completo cada 5 segundos
                if tiempo % 5 == 0:
                    self.enviar_a_todos("estado_juego", self.estado_juego)

    def generar_oleada(self, equipo):
        """Genera una oleada de minions para un equipo"""
        tipos_minions = ["melee", "caster", "siege"]
        punto_inicio = [40, 490] if equipo == "aliados" else [750, 70]
        destino_final = [750, 70] if equipo == "aliados" else [40, 490]

        for ruta_id in range(3):  # 3 rutas diferentes
            for tipo in tipos_minions:
                stats = {
                    "melee": {"vida": 100, "daño": 15, "velocidad": 2, "rango_ataque": 40},
                    "caster": {"vida": 60, "daño": 25, "velocidad": 1.8, "rango_ataque": 80},
                    "siege": {"vida": 150, "daño": 40, "velocidad": 1.5, "rango_ataque": 120}
                }.get(tipo, {"vida": 100, "daño": 15, "velocidad": 2, "rango_ataque": 40})

                minion = {
                    "tipo": tipo,
                    "vida": stats["vida"],
                    "vida_max": stats["vida"],
                    "daño": stats["daño"],
                    "velocidad": stats["velocidad"],
                    "ruta_id": f"{equipo}_ruta_{ruta_id}",
                    "pos": list(punto_inicio),
                    "objetivo": None,
                    "equipo": equipo,
                    "rango_ataque": stats["rango_ataque"],
                    "destino": destino_final,
                    "puntos_ruta": self.generar_ruta_minion(equipo, ruta_id),
                    "indice_punto_actual": 0,
                    "reduccion_daño": 0
                }
                self.estado_juego["minions"][equipo].append(minion)

    def generar_ruta_minion(self, equipo, ruta_id):
        """Genera los puntos de ruta para los minions según el equipo y ruta"""
        if equipo == "aliados":
            if ruta_id == 0:  # Ruta inferior -> derecha -> base enemiga
                return [(49, 500), (751, 500), (751, 100)]
            elif ruta_id == 1:  # Ruta diagonal directa
                return [(49, 500), (751, 100)]
            else:  # Ruta izquierda -> superior -> base enemiga
                return [(49, 500), (49, 100), (751, 100)]
        else:  # enemigos
            if ruta_id == 0:  # Ruta superior -> izquierda -> base aliada
                return [(751, 100), (49, 100), (49, 500)]
            elif ruta_id == 1:  # Ruta diagonal directa
                return [(751, 100), (49, 500)]
            else:  # Ruta derecha -> inferior -> base aliada
                return [(751, 100), (751, 500), (49, 500)]

    def manejar_cliente(self, cliente):
        """Maneja la comunicación con un cliente conectado"""
        id_cliente = None
        try:
            while True:
                datos = cliente.recv(4096).decode('utf-8')
                if not datos:
                    break

                # Procesar cada mensaje (pueden venir concatenados)
                mensajes = datos.split('|')
                for msg in mensajes:
                    if not msg:
                        continue

                    try:
                        mensaje = json.loads(msg)
                        tipo = mensaje.get("tipo")

                        if tipo == "conectar":
                            # Asignar ID al cliente
                            with self.lock:
                                id_cliente = str(len(self.clientes) + 1)
                                self.clientes[id_cliente] = {
                                    "socket": cliente,
                                    "nombre": f"Jugador{id_cliente}",
                                    "personaje": None,
                                    "pos": [400, 300],
                                    "vida": 100,
                                    "vida_max": 100,
                                    "velocidad": 5,
                                    "daño": 20,
                                    "nivel": 1,
                                    "experiencia": 0,
                                    "reduccion_daño": 0
                                }
                            
                            # Enviar bienvenida con ID asignado y estado completo
                            self.enviar_mensaje(cliente, "bienvenida", {
                                "id": id_cliente,
                                "mensaje": "Bienvenido al servidor",
                                "jugadores": self.obtener_datos_jugadores(),
                                "estado_juego": self.estado_juego,
                                "oleada": {
                                    "contador": self.estado_juego["oleadas"]["contador_oleadas"],
                                    "tiempo": self.estado_juego["oleadas"]["tiempo_juego"]
                                }
                            })

                            # Notificar a otros jugadores
                            self.enviar_a_todos_excepto(id_cliente, "nuevo_jugador", {
                                "id": id_cliente,
                                **self.clientes[id_cliente]
                            })

                        elif tipo == "nuevo_jugador" and id_cliente:
                            with self.lock:
                                if id_cliente in self.clientes:
                                    self.clientes[id_cliente].update({
                                        "nombre": mensaje.get("nombre", f"Jugador{id_cliente}")[:16],
                                        "personaje": mensaje.get("personaje", 1),
                                        "pos": mensaje.get("pos", [400, 300]),
                                        "vida": mensaje.get("vida", 100),
                                        "vida_max": mensaje.get("vida_max", 100),
                                        "velocidad": mensaje.get("velocidad", 5),
                                        "daño": mensaje.get("daño", 20),
                                        "nivel": mensaje.get("nivel", 1),
                                        "experiencia": mensaje.get("experiencia", 0),
                                        "reduccion_daño": mensaje.get("reduccion_daño", 0)
                                    })
                            
                            # Actualizar a todos los jugadores
                            self.enviar_a_todos("jugadores", {
                                "jugadores": self.obtener_datos_jugadores()
                            })

                        elif tipo == "movimiento" and id_cliente:
                            with self.lock:
                                if id_cliente in self.clientes:
                                    self.clientes[id_cliente]["pos"] = mensaje.get("pos", [400, 300])
                            
                            # Enviar actualización de posición a todos excepto al emisor
                            self.enviar_a_todos_excepto(id_cliente, "actualizacion_posicion", {
                                "id": id_cliente,
                                "pos": mensaje.get("pos", [400, 300])
                            })

                        elif tipo == "estructura_destruida" and id_cliente:
                            with self.lock:
                                tipo_estructura = mensaje.get("tipo")
                                equipo = mensaje.get("equipo")
                                indice = mensaje.get("indice")
                                
                                if (tipo_estructura in self.estado_juego["estructuras"] and 
                                    equipo in self.estado_juego["estructuras"][tipo_estructura] and
                                    indice < len(self.estado_juego["estructuras"][tipo_estructura][equipo])):
                                    
                                    self.estado_juego["estructuras"][tipo_estructura][equipo][indice]["destruida"] = True
                                    self.enviar_a_todos("estructura_destruida", mensaje)

                        elif tipo == "desconectar" and id_cliente:
                            with self.lock:
                                if id_cliente in self.clientes:
                                    del self.clientes[id_cliente]
                            
                            # Notificar a otros jugadores
                            self.enviar_a_todos("jugador_desconectado", {
                                "id": id_cliente
                            })
                            break

                    except json.JSONDecodeError:
                        print("Error decodificando mensaje JSON")
                    except Exception as e:
                        print(f"Error procesando mensaje: {e}")

        except ConnectionResetError:
            print("Cliente desconectado abruptamente")
        finally:
            if id_cliente:
                with self.lock:
                    if id_cliente in self.clientes:
                        del self.clientes[id_cliente]
                
                # Notificar a otros jugadores
                self.enviar_a_todos("jugador_desconectado", {
                    "id": id_cliente
                })
            cliente.close()

    def obtener_datos_jugadores(self):
        """Devuelve los datos de todos los jugadores para sincronización"""
        datos = {}
        for id_jugador, jugador in self.clientes.items():
            datos[id_jugador] = {
                "nombre": jugador["nombre"],
                "personaje": jugador["personaje"],
                "pos": jugador["pos"],
                "vida": jugador["vida"],
                "vida_max": jugador["vida_max"],
                "velocidad": jugador["velocidad"],
                "daño": jugador["daño"],
                "nivel": jugador["nivel"],
                "experiencia": jugador["experiencia"],
                "reduccion_daño": jugador["reduccion_daño"]
            }
        return datos

    def enviar_mensaje(self, cliente, tipo, contenido):
        """Envía un mensaje a un cliente específico"""
        try:
            mensaje = json.dumps({
                "tipo": tipo,
                **contenido
            })
            cliente.sendall((mensaje + '|').encode('utf-8'))
        except:
            pass

    def enviar_a_todos(self, tipo, contenido):
        """Envía un mensaje a todos los clientes conectados"""
        with self.lock:
            for id_jugador, datos in self.clientes.items():
                self.enviar_mensaje(datos["socket"], tipo, contenido)

    def enviar_a_todos_excepto(self, id_excluido, tipo, contenido):
        """Envía un mensaje a todos los clientes excepto al especificado"""
        with self.lock:
            for id_jugador, datos in self.clientes.items():
                if id_jugador != id_excluido:
                    self.enviar_mensaje(datos["socket"], tipo, contenido)

if __name__ == "__main__":
    # Usar la IP de Radmin VPN (26.176.7.141) o 0.0.0.0 para escuchar en todas las interfaces
    servidor = Servidor(host='26.176.7.141', port=5555)