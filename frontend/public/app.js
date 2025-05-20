document.addEventListener("visibilitychange", () => {
    if (document.visibilityState === "hidden") {
        const blob = new Blob(
            [
                JSON.stringify({
                    sid: SERVER_CONNECT_SID,
                }),
            ],
            { type: "application/json" },
        );

        navigator.sendBeacon("/disconnect", blob);
    }
});

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

let interval, canvas, ctx;

function capture() {
    ctx.drawImage(video, 0, 0, canvas.width, canvas.height);
    const dataurl = canvas.toDataURL("image/png");
    image.src = dataurl;

    fetch("/connect", {
        method: "POST",
        headers: {
            "Content-type": "application/json",
        },
        body: JSON.stringify({
            sid: SERVER_CONNECT_SID,
            dataurl: dataurl,
        }),
    });
}

video.addEventListener("canplay", () => {
    bstart.addEventListener("click", () => {
        video.play();
        interval = setInterval(capture, 1000 / FPS);
    });

    bstop.addEventListener("click", () => {
        clearInterval(interval);
        video.pause();
    });
});

getstream()
    .then((stream) => {
        video.srcObject = stream;

        video.addEventListener("loadeddata", () => {
            console.log("loaded data");

            canvas = document.createElement("canvas");
            canvas.width = video.width;
            canvas.height = video.height;
            ctx = canvas.getContext("2d");
        });
    })
    .catch((err) => console.error(err));
