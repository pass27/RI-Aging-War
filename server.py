import tornado.ioloop
import tornado.web
import tornado.websocket
import json
import math
from collision import *
import os

v = Vector

clients = []
players = []

corrispondenzaIndex = [1, 0]

#Apre e inizializza il json
with open ("base.json", "w") as file:
    json.dump({
        "P1": {
            "x": 120,
            "y": 350,
            "prj": [],
            "dir": "right",
            "rifleAngle": 0
        },
        "P2": {
            "x": 840,
            "y": 220,
            "prj": [],
            "dir": "left",
            "rifleAngle": 3
        },
        "mappa": {
            "O1":{
                "x": 150,
                "y": 125,
                "w": 82,
                "h": 88
            },
            "O2":{
                "x": 480,
                "y": 250,
                "w": 82,
                "h": 88
            },
            "O3":{
                "x": 700,
                "y": 100,
                "w": 82,
                "h": 88
            },
            "O4":{
                "x": 780,
                "y": 330,
                "w": 82,
                "h": 88
            },
            "O5":{
                "x": 250,
                "y": 360,
                "w": 82,
                "h": 88
            },
            "O6":{
                "x": 400,
                "y": 100,
                "w": 32,
                "h": 56
            },
            "O7":{
                "x": 335,
                "y": 150,
                "w": 70,
                "h": 32
            },
            "O8":{
                "x": 605,
                "y": 380,
                "w": 32,
                "h": 56
            },
            "O9":{
                "x": 628,
                "y": 352,
                "w": 70,
                "h": 32
            },
            "O10":{
                "x": 300,
                "y": 260,
                "w": 40,
                "h": 32
            },
            "O11":{
                "x": 550,
                "y": 150,
                "w": 40,
                "h": 32
            },
            "O12":{
                "x": 440,
                "y": 400,
                "w": 40,
                "h": 32
            },
            "O13":{
                "x": 357,
                "y": 108,
                "w": 36,
                "h": 36
            },
            "O14":{
                "x": 643,
                "y": 389,
                "w": 36,
                "h": 36
            },
            
        }
    }, file)

game = {}
last_Key = ""

#Salva i dati del json in game
with open ("base.json", "r") as file:
        game = json.load(file)            
            
class Player:
    def __init__(self, x, y, ID, dir):
        self.x, self.y  = x, y
        self.old_x, self.old_y = 0, 0
        self.id = ID
        self.speed = 4
        self.vA, self.vD, self.vW, self.vS = 0, 0, 0, 0
        self.hitbox = Poly.from_box(v(self.x + 12.5, self.y + 19), 25, 38)
        self.prj = []
        self.hp = 5
        self.canTeleport = True
    
    #Controlla le collisioni e aggiorna la posizione del Player
    def updatePlayer(self):
        self.old_x, self.old_y = self.x, self.y

        self.x += (self.vA + self.vD) 
        self.y += (self.vW + self.vS) 

        #Ottiene l'hitbox del Player (gli sprite left/right hanno dimensioni diverse da up/down)
        if game["P" + str(self.id + 1)]["dir"] == "right" or game["P" + str(self.id + 1)]["dir"] == "left":
            self.hitbox = Poly.from_box(v(self.x + 13, self.y + 19), 21, 32)
        else: 
            self.hitbox = Poly.from_box(v(self.x + 12, self.y + 19), 21, 32)

        #Controlla le collisioni
        for i in range(1, 13):
            #Ottiene l'hitbox degli ostacoli
            obs = game["mappa"]["O" + str(i)]
            obsHitbox = Poly.from_box(v(obs["x"] + obs["w"] / 2, obs["y"] + obs["h"] / 2), obs["w"], obs["h"])

            if collide(self.hitbox, obsHitbox): #collisione ostacolo-player
                self.x = self.old_x 
                self.y = self.old_y

            for proiettile in self.prj: 
                if (collide(proiettile.hitbox, obsHitbox) #collisione ostacolo-proiettili
                    or proiettile.x < 38 or proiettile.x > 924 or proiettile.y < 50 or proiettile.y > 494): #proiettile esce dallo spazio
                    self.prj.remove(proiettile)               
                elif collide(proiettile.hitbox, players[corrispondenzaIndex[self.id]].hitbox): #collisione proiettile-avversario
                    self.prj.remove(proiettile)
                    players[corrispondenzaIndex[self.id]].hp -= 1
                    if players[corrispondenzaIndex[self.id]].hp == 0:
                        print("Giocatore %s ha vinto" % str(self.id + 1))
                else:
                    proiettile.updatePosizioneProiettile()
        
        #Collisione coi teletrasporti
        for i in range (13, 15):
            obs = game["mappa"]["O" + str(i)]
            obsHitbox = Poly.from_box(v(obs["x"] + obs["w"] / 2, obs["y"] + obs["h"] / 2), obs["w"], obs["h"])
            if collide(self.hitbox, obsHitbox) and self.canTeleport == True:
                if i == 13:
                    self.x = 643 
                    self.y = 389
                elif i == 14:
                    self.x = 357
                    self.y = 108
                self.canTeleport = False
                tornado.ioloop.IOLoop.current().call_later(2, lambda: setattr(self, 'canTeleport', True))
        
        #Collisione coi margini
        for i in range(4):
            if i == 0:
                borderHitbox = Poly.from_box(v(480, 25), 960, 50)
            elif i == 1:
                borderHitbox = Poly.from_box(v(480, 517), 960, 46)
            elif i == 2:
                borderHitbox = Poly.from_box(v(19, 270), 38, 540)
            elif i == 3:
                borderHitbox = Poly.from_box(v(942, 270), 36, 540)    
            
            if collide(self.hitbox, borderHitbox): 
                    self.x = self.old_x 
                    self.y = self.old_y

        #Aggiornamento posizione Players e proiettili nel json
        proiettili_dict = [proiettile.to_dict() for proiettile in self.prj]
        game["P" + str(self.id + 1)]["prj"] = proiettili_dict
        game["P" + str(self.id + 1)]["x"] = self.x
        game["P" + str(self.id + 1)]["y"] = self.y

class Proiettile:
    def __init__(self, Centrox, Centroy, vx, vy):
        self.x = Centrox - 5
        self.y = Centroy - 3
        self.vx = vx
        self.vy = vy
        self.hitbox = Poly.from_box(v(Centrox, Centroy), 10, 6)
    
    #Aggiornamento posizione del proiettile
    def updatePosizioneProiettile(self):
        self.x += self.vx
        self.y += self.vy
        self.hitbox = Poly.from_box(v(self.x, self.y), 10, 6)

    def to_dict(self):
        return {
            "x": self.x,
            "y": self.y,
            "vx": self.vx,
            "vy": self.vy
        }

players.append(Player(120, 350, 0, "right"))
players.append(Player(840, 220, 1, "left"))

print("Game server started.")

#Inizializza il file json
class JsonHandler(tornado.web.RequestHandler):
    def get(self):
        self.set_header('Cache-Control', 'no-store, no-cache, must-revalidate, max-age=0')
        self.write(game)
            
class GameHandler(tornado.websocket.WebSocketHandler):
    #Apertura del gioco da parte di un client
    def open(self):
        clients.append(self)
        self.id = clients.index(self)
        self.write_message(json.dumps({"type": "clientId", "data": {"clientId" : self.id}}))
        self.write_message(json.dumps({"type": "gameUpdate", "data": game}))

    #Ricezione di un messaggio e sua implememtazione
    def on_message(self, messaggio):
        #Il messaggio viene ricevuto e interpretato
        global last_Key
        msg = json.loads(messaggio)
        last_Key = msg["data"]

        #Gestione del movimento dei Players, se il messaggio è la pressione di un tasto
        if msg["type"] == "keydown":
            if msg["data"] == "KeyW":
                players[self.id].vW = -5
            if msg["data"] == "KeyS":
                players[self.id].vS = +5
            if msg["data"] == "KeyA":
                players[self.id].vA = -5
            if msg["data"] == "KeyD":
                players[self.id].vD = +5
        elif msg["type"] == "keyup":
            if msg["data"] == "KeyW":
                players[self.id].vW = 0
            if msg["data"] == "KeyS":
                players[self.id].vS = 0
            if msg["data"] == "KeyA":
                players[self.id].vA = 0
            if msg["data"] == "KeyD":
                players[self.id].vD = 0

        if msg["type"] == "mouseMove" or (msg["type"] == "click" and len(players[self.id].prj) < 5):            
            #Se il messaggio è un click viene generato un proiettile (max 5 per Player)
            if msg["type"] == "click" and len(players[self.id].prj) < 5:
                vecX = msg["data"][0] - (players[self.id].x + 20)
                vecY = msg["data"][1] - (players[self.id].y + 40)
                modulo = math.sqrt(vecX ** 2 + vecY ** 2)
                velNorm = [vecX / modulo, vecY / modulo]
                players[self.id].prj.append(Proiettile(players[self.id].x + 20 + vecX / modulo * 43, players[self.id].y + 30 + vecY / modulo * 43, velNorm[0] * 2, velNorm[1] * 2))

            #Se il messagio è il movimento del mouse, calcola il suo angolo rispetto al Player e la conseguente direzione del Player
            else:
                if game["P" + str(self.id + 1)]["dir"] == "right" or game["P" + str(self.id + 1)]["dir"] == "left":
                    angle = math.atan2(msg["data"][1] - (players[self.id].y + 13), msg["data"][0] - (players[self.id].x + 19))
                else:
                    angle = math.atan2(msg["data"][1] - (players[self.id].y + 12), msg["data"][0] - (players[self.id].x + 19))

                game["P" + str(self.id + 1)]["rifleAngle"] = angle
                angle /= math.pi

                if angle >= -0.25 and angle <= 0.25:
                    game["P" + str(self.id + 1)]["dir"] = "right"
                
                elif angle > 0.25 and angle <= 0.75:
                    game["P" + str(self.id + 1)]["dir"] = "down"

                elif angle < -0.25 and angle >= -0.75:
                    game["P" + str(self.id + 1)]["dir"] = "up" 
                
                else:
                    game["P" + str(self.id + 1)]["dir"] = "left" 

    #Chiusura di un client
    def on_close(self):
        x = self.id
        clients.remove(self)
        for i in range(x, len(clients) - x):
            clients[i].id -= 1

#Aggiorna il gioco e invia un Update al client
def update():
    for player in players:
        player.updatePlayer()

    for client in clients:
        client.write_message(json.dumps({"type": "gameUpdate", "data": game}))

#Fornisce la pagina home
class MainHandler(tornado.web.RequestHandler):
    def get(self):
        self.render("home.html")

#Fornisce la pagina di gioco
class ClientHandler(tornado.web.RequestHandler):
    def get(self):
        self.render("client.html")

class GameScriptHandler(tornado.web.RequestHandler):
    def get(self):
        self.render("game.js")

#Fornisce le immagini
class ImageHandler(tornado.web.RequestHandler):
    def get(self, image_key):
        image_paths = {
            'down': 'images/soldier_down.png',
            'up': 'images/soldier_up.png',
            'left': 'images/soldier_left.png',
            'right': 'images/soldier_right.png',
            'borders': 'images/borders.png',
            'tree': 'images/tree.png',
            'rifle_down': 'images/rifle_down.png',
            'rifle_up': 'images/rifle_up.png',
            'rifle_left': 'images/rifle_left.png',
            'rifle_right': 'images/rifle_right.png',
            'ground': 'images/ground.png',
            'rock_large': 'images/rock_large.png',
            'rock_long': 'images/rock_long.png',
            'rock_small': 'images/rock_small.png',
            'teleport': 'images/teleport.png',
            'prj': 'images/projectile.png',
        }
        image_path = os.path.join(os.path.dirname(__file__), image_paths.get(image_key))
        if not os.path.exists(image_path):
            raise tornado.web.HTTPError(404, "File not found")
        self.set_header('Content-Type', 'image/png')
        with open(image_path, 'rb') as f:
            self.write(f.read())

#Esegue nel momento adatto i vari handler
application = tornado.web.Application([
    (r"/", MainHandler),
    (r"/game.js", GameScriptHandler),
    (r"/game-ws", GameHandler),
    (r"/image/(.*)", ImageHandler),
    (r"/client", ClientHandler),
    
])

#Se il file è il principlae fa partire il programma
if __name__ == "__main__":
    application.listen(5555)
    tornado.ioloop.PeriodicCallback(update, 20).start()
    tornado.ioloop.IOLoop.current().start()
