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

/** @param {ImageBitmap} bitmap */
async function toblob(bitmap) {
    const ocanvas = new OffscreenCanvas(bitmap.width, bitmap.height);
    ocanvas.getContext("bitmaprenderer").transferFromImageBitmap(bitmap);
    return await ocanvas.convertToBlob({ type: "image/png" });
}

const FPS = 1;

const video = document.getElementById("video");
const bstart = document.getElementById("bstart");
const bstop = document.getElementById("bstop");

let capture, interval;

var xhr = new XMLHttpRequest();
console.log("a");
xhr.open("POST", "https://7a96-128-54-33-224.ngrok-free.app", true);
console.log("b");
xhr.setRequestHeader("Content-Type", "application/octet-stream");
// xhr.setRequestHeader("Access-Control-Allow-Origin", "http://127.0.0.1:8000");
// xhr.setRequestHeader("Access-Control-Allow-Credentials", "true");
console.log("c");

xhr.onload = () => {
    if (xhr.readyState == 4 && xhr.status == 201) {
        console.log(JSON.parse(xhr.responseText));
    } else {
        console.log(`Error: ${xhr.status}`);
    }
};

getstream()
    .then((stream) => {
        video.srcObject = stream;
        bstart.onclick = () => (video.srcObject = stream);
        bstop.onclick = () => (video.srcObject = null);

        const track = stream.getVideoTracks()[0];
        capture = new ImageCapture(track);
        console.log(capture);
    })
    .then(() => {
        interval = setInterval(() => {
            // capture.takePhoto(null).then((blob) => {
            capture.grabFrame().then((bitmap) => {
                console.log("bitmap: ", bitmap);
                const blob = toblob(bitmap);
                console.log("blob: ", blob);
                xhr.send(blob);
            });
        }, 1000 / FPS);
    })
    .catch((err) => console.error(err));
