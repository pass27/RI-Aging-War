let data = {}
let mouseX = 0
let mouseY = 0

document.addEventListener("DOMContentLoaded", function () {
    //Ottenimento del canvas
    let c = document.getElementById("myCanvas")
    let ctx = c.getContext("2d")
    document.getElementById("myCanvas").width = 960
    document.getElementById("myCanvas").height = 540

    ctx.imageSmoothingEnabled = false //elimina l'anti-aliasing (sfocatura dei bordi) alle immagini

    let obs = []
    let started = false

    const ws = new WebSocket("ws://localhost:5555/game-ws")

    //Ottenimento dal server delle immagini necessarie 
    let playerImages = {
        "up": new Image(),
        "down": new Image(),
        "left": new Image(),
        "right": new Image(),
    }
    let rifleImages = {
        "up": new Image(),
        "down": new Image(),
        "left": new Image(),
        "right": new Image(),
    }
    for (let direction in playerImages) {
        playerImages[direction].src = `/image/${direction}`
        rifleImages[direction].src = `/image/rifle_${direction}`
    }
    let bordersImage = new Image();
    let treeImage = new Image();
    let groundImage = new Image();
    let longRockImg = new Image();
    let largeRockImg = new Image();
    let smallRockImg = new Image();
    let teleportImage = new Image();
    let prjImage = new Image();
    bordersImage.src = `/image/borders`
    treeImage.src = `/image/tree`
    groundImage.src = `/image/ground`
    longRockImg.src = `/image/rock_long`
    largeRockImg.src = `/image/rock_large`
    smallRockImg.src = `/image/rock_small`
    teleportImage.src = `/image/teleport`
    prjImage.src = `/image/prj`

    ws.addEventListener("open", function () {
        //Ogni 20ms le coordinate del mouse vengono inviate al server
        setInterval(sendMouse, 20)

        //Riceve dal server e disegna gli aggiornamenti del gioco
        ws.addEventListener("message", function (event) {
            let msg = JSON.parse(event.data)
            if (msg.type == "gameUpdate") {
                console.log("ws: game update")
                data = msg.data
                started = true
                animazione()
            }
        })

        //Rileva gli eventi di click e pressione/rilascio tasti e ne manda le informazioni al server
        window.addEventListener("click", (event) => {
            ws.send(JSON.stringify({ "type": "click", "data": [event.clientX, event.clientY] }))
        })
        window.addEventListener("keydown", (event) => {
            ws.send(JSON.stringify({ "type": "keydown", "data": event.code }))
            console.log()
        })
        window.addEventListener("keyup", (event) => {
            ws.send(JSON.stringify({ "type": "keyup", "data": event.code }))
        })

        //Al movimento del cursore ne aggiorna la posizione 
        window.addEventListener("mousemove", updateMouse)

    })

    //Disegna ogni elemento
    function animazione() {
        if (!started) {
            return
        }

        //Disegna gli elementi di sfondo
        ctx.clearRect(0, 0, window.innerWidth, window.innerHeight)
        ctx.drawImage(groundImage, 0, 0, 960, 540)
        ctx.drawImage(bordersImage, 0, 0, 960, 540)

        //Disegna gli ostacoli (alberi, rocce, teletrasporti)
        for (let i = 1; i <= 14; i++) {
            obs = data["mappa"]["O" + i]
            ctx.beginPath()
            if (i <= 5) {
                ctx.drawImage(treeImage, obs.x, obs.y, obs.w, obs.h)
            }
            if (i == 6 || i == 8) {
                ctx.drawImage(longRockImg, obs.x, obs.y, obs.w, obs.h)
            }
            if (i == 7 || i == 9) {
                ctx.drawImage(largeRockImg, obs.x, obs.y, obs.w, obs.h)
            }
            if (i == 10 || i == 11 || i == 12) {
                ctx.drawImage(smallRockImg, obs.x, obs.y, obs.w, obs.h)
            }
            if (i == 13 || i == 14) {
                ctx.drawImage(teleportImage, obs.x, obs.y, obs.w, obs.h)
            }
            ctx.stroke()
        }

        //Disegna i giocatori, il loro fucile e i proiettili    
        for (let i = 1; i <= 2; i++) {
            ctx.beginPath()
            if (data["P" + i].dir == "left") {
                ctx.drawImage(playerImages[data["P" + i].dir], data["P" + i].x, data["P" + i].y, 26, 38)
                drawRotatedImage(ctx, rifleImages[data["P" + i].dir], data["P" + i].x + 19, data["P" + i].y + 29, 0, 8, data["P" + i].rifleAngle, 2.5)
            }
            else if (data["P" + i].dir == "right") {
                ctx.drawImage(playerImages[data["P" + i].dir], data["P" + i].x, data["P" + i].y, 26, 38)
                drawRotatedImage(ctx, rifleImages[data["P" + i].dir], data["P" + i].x + 7, data["P" + i].y + 28, 0, 8, data["P" + i].rifleAngle, 2.5)
            }
            else if (data["P" + i].dir == "down") {
                ctx.drawImage(playerImages[data["P" + i].dir], data["P" + i].x, data["P" + i].y, 24, 38)
                drawRotatedImage(ctx, rifleImages[data["P" + i].dir], data["P" + i].x + 14, data["P" + i].y + 27, 0, 3, data["P" + i].rifleAngle, 2.5)
            }
            else if (data["P" + i].dir == "up") {
                drawRotatedImage(ctx, rifleImages[data["P" + i].dir], data["P" + i].x + 12, data["P" + i].y + 1, 0, 3, data["P" + i].rifleAngle, 2.5)
                ctx.drawImage(playerImages[data["P" + i].dir], data["P" + i].x, data["P" + i].y, 24, 38)
            }

            //Proiettili
            for (let j = 0; j < data["P" + i].prj.length; j++) {
                drawRotatedImage(ctx, prjImage, data["P" + i].prj[j].x, data["P" + i].prj[j].y, 0, 3, data["P" + i].rifleAngle, 1)
            }
            ctx.stroke()
        }
    }

    //Aggiorna le coordinate del mouse
    function updateMouse(event) {
        mouseX = event.clientX
        mouseY = event.clientY
    }

    //Invia le coordinate del mouse al server
    function sendMouse() {
        ws.send(JSON.stringify({ "type": "mouseMove", "data": [mouseX, mouseY] }))
    }

    //Permette di disegnare le immagini come ruotate di un dato angolo
    function drawRotatedImage(ctx, image, x, y, px, py, angle, scale) {
        ctx.save()
        ctx.translate(x, y) //x e y sono le coordinate del punto del canvas in cui deve essere disegnata l'immagine
        ctx.rotate(angle)
        ctx.drawImage(image, -px, -py, image.width * scale, image.height * scale) //px e py sono le coordinate del punto dell'immagine attorno a cui essa ruota
        ctx.restore()
    }

})
