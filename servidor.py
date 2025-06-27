import socket
import json
from threading import Thread

class Servidor:
    def __init__(self, host='localhost', port=5555):
        self.host = host
        self.port = port
        self.clientes = {}
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.socket.bind((self.host, self.port))
        self.socket.listen(5)
        print(f"Servidor escuchando en {self.host}:{self.port}")

    def manejar_cliente(self, cliente, direccion):
        print(f"Conexión establecida con {direccion}")
        try:
            while True:
                datos = cliente.recv(4096).decode('utf-8')
                if not datos:
                    break
                mensaje = json.loads(datos)
                self.procesar_mensaje(cliente, mensaje)
        except Exception as e:
            print(f"Error con {direccion}: {e}")
        finally:
            cliente.close()
            if direccion in self.clientes:
                del self.clientes[direccion]
            print(f"Conexión cerrada con {direccion}")

    def procesar_mensaje(self, cliente, mensaje):
        tipo = mensaje.get("tipo")
        if tipo == "nuevo_jugador":
            self.clientes[cliente] = mensaje
            respuesta = {"tipo": "bienvenida", "mensaje": "¡Bienvenido al servidor!"}
            cliente.sendall(json.dumps(respuesta).encode('utf-8'))
        elif tipo == "desconectar":
            cliente.close()

    def iniciar(self):
        while True:
            cliente, direccion = self.socket.accept()
            Thread(target=self.manejar_cliente, args=(cliente, direccion), daemon=True).start()

if __name__ == "__main__":
    servidor = Servidor()
    servidor.iniciar()