# servidor.py - Servidor para el juego multijugador
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
        self.oleadas = {
            "tiempo_ultima_oleada": 0,
            "intervalo": 30,  # segundos
            "contador_oleadas": 0,
            "tiempo_juego": 0,  # en segundos
            "primer_oleada": False
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
                self.oleadas["tiempo_juego"] += 1

                # Primera oleada a los 65 segundos (1:05)
                if not self.oleadas["primer_oleada"] and self.oleadas["tiempo_juego"] >= 65:
                    self.oleadas["primer_oleada"] = True
                    self.oleadas["tiempo_ultima_oleada"] = self.oleadas["tiempo_juego"]
                    self.oleadas["contador_oleadas"] += 1
                    self.enviar_a_todos("nueva_oleada", {
                        "contador": self.oleadas["contador_oleadas"],
                        "tiempo": self.oleadas["tiempo_juego"]
                    })
                
                # Oleadas posteriores cada 30 segundos
                tiempo_desde_ultima = self.oleadas["tiempo_juego"] - self.oleadas["tiempo_ultima_oleada"]
                if tiempo_desde_ultima >= self.oleadas["intervalo"] and self.oleadas["primer_oleada"]:
                    self.oleadas["tiempo_ultima_oleada"] = self.oleadas["tiempo_juego"]
                    self.oleadas["contador_oleadas"] += 1
                    self.enviar_a_todos("nueva_oleada", {
                        "contador": self.oleadas["contador_oleadas"],
                        "tiempo": self.oleadas["tiempo_juego"]
                    })

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
                            
                            # Enviar bienvenida con ID asignado
                            self.enviar_mensaje(cliente, "bienvenida", {
                                "id": id_cliente,
                                "mensaje": "Bienvenido al servidor",
                                "jugadores": self.obtener_datos_jugadores(),
                                "oleada": {
                                    "contador": self.oleadas["contador_oleadas"],
                                    "tiempo": self.oleadas["tiempo_juego"]
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