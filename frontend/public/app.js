async function getstream() {
    try {
        const stream = await navigator.mediaDevices.getUserMedia({
            video: true,
        });
        console.log("Got MediaStream:", stream);
        return stream;
    } catch (error) {
        console.error("Error opening video camera.", error);
        return null;
    }
}

const FPS = 5;

const bstart = document.getElementById("bstart");
const bstop = document.getElementById("bstop");
const video = document.getElementById("video_frame");
const image = document.getElementById("image");

let interval;

/*
var xhr = new XMLHttpRequest();
console.log("a");
// xhr.open("POST", "http://localhost:8000/connect", true);
xhr.open("POST", "/connect", true);
console.log("b");
// xhr.setRequestHeader("Content-type", "application/octet-stream");
xhr.setRequestHeader("Content-type", "text/plain");
xhr.setRequestHeader("Accept", "text/json");
console.log("c");

xhr.withCredentials = false;

xhr.send("hello from client");
console.log(xhr.getAllResponseHeaders());

xhr.onload = () => {
    if (xhr.readyState == 4 && xhr.status == 201) {
        console.log(JSON.parse(xhr.responseText));
    } else {
        console.log(`Error: ${xhr.status}`);
    }
};
*/

// fetch("/connect", {
//     method: "POST",
//     body: JSON.stringify({
//         data: "blob data 1",
//     }),
//     headers: {
//         "Content-type": "application/json",
//     },
// })
//     .then((resp) => resp.json())
//     .then((json) => console.log(json));

// const socket = new WebSocket("ws://localhost:65432");
// socket.onopen = () => {
//     console.log("WebSocket connection opened");
//     socket.send("hello from client");
// };

let canvas, ctx;

function capture() {
    ctx.drawImage(video, 0, 0, canvas.width, canvas.height);
    dataurl = canvas.toDataURL("image/png");
    image.src = dataurl;

    fetch("/connect", {
        method: "POST",
        body: JSON.stringify({
            data: dataurl,
        }),
        headers: {
            "Content-type": "application/json",
        },
    });
}

video.oncanplay = () => {
    bstart.onclick = () => {
        video.play();
        interval = setInterval(capture, 1000 / FPS);
    };

    bstop.onclick = () => {
        clearInterval(interval);
        video.pause();
    };
};

getstream()
    .then((stream) => {
        video.srcObject = stream;

        video.onloadeddata = () => {
            console.log("loaded data");

            canvas = document.createElement("canvas");
            canvas.width = video.width;
            canvas.height = video.height;
            ctx = canvas.getContext("2d");
        };
    })
    .catch((err) => console.error(err));
