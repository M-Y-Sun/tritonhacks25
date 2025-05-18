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

const FPS = 15;

const video = document.getElementById("video");
const bstart = document.getElementById("bstart");
const bstop = document.getElementById("bstop");

let capture, interval;

getstream()
    .then((stream) => {
        bstart.onclick = () => (video.srcObject = stream);
        bstop.onclick = () => (video.srcObject = null);

        const track = stream.getVideoTracks()[0];
        capture = new ImageCapture(track);
    })
    .then(() => {
        interval = setInterval(() => {
            capture.takePhoto().then((blob) => {
                console.log("blob: ", blob);
            });
        }, 1000 / FPS);
    })
    .catch((err) => console.error(err));
