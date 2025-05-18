const FPS = 1;
let websocket = null;
let capture = null;
let interval = null;

async function getstream() {
    try {
        const stream = await navigator.mediaDevices.getUserMedia({
            video: true
        });
        console.log("Got MediaStream:", stream);
        return stream;
    } catch (error) {
        console.error("Error opening video camera.", error);
        return null;
    }
}

async function toblob(bitmap) {
    const canvas = new OffscreenCanvas(bitmap.width, bitmap.height);
    const ctx = canvas.getContext('2d');
    ctx.drawImage(bitmap, 0, 0);
    return await canvas.convertToBlob({ type: 'image/jpeg', quality: 0.8 });
}

async function setupWebSocket() {
    // Use relative WebSocket URL that will work with any host
    const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
    const wsUrl = `${protocol}//${window.location.host}/ws`;
    
    websocket = new WebSocket(wsUrl);
    
    websocket.onopen = () => {
        console.log('WebSocket connected');
        startStreaming();
    };
    
    websocket.onclose = () => {
        console.log('WebSocket disconnected');
        stopStreaming();
        // Try to reconnect after 5 seconds
        setTimeout(setupWebSocket, 5000);
    };
    
    websocket.onerror = (error) => {
        console.error('WebSocket error:', error);
    };
    
    websocket.onmessage = (event) => {
        try {
            const data = JSON.parse(event.data);
            updateUI(data);
        } catch (error) {
            console.error('Error parsing WebSocket message:', error);
        }
    };
}

function updateUI(data) {
    // Update any UI elements with the received data
    if (data.numberOfPeople !== undefined) {
        const countDisplay = document.getElementById('peopleCount');
        if (countDisplay) {
            countDisplay.textContent = `Number of people: ${data.numberOfPeople}`;
        }
    }
}

function startStreaming() {
    if (!capture || !websocket) return;
    
    interval = setInterval(async () => {
        if (websocket.readyState === WebSocket.OPEN) {
            try {
                const bitmap = await capture.grabFrame();
                const blob = await toblob(bitmap);
                websocket.send(blob);
            } catch (error) {
                console.error('Error capturing frame:', error);
            }
        }
    }, 1000 / FPS);
}

function stopStreaming() {
    if (interval) {
        clearInterval(interval);
        interval = null;
    }
}

// Initialize everything when the page loads
document.addEventListener('DOMContentLoaded', async () => {
    const video = document.getElementById('video');
    const startButton = document.getElementById('bstart');
    const stopButton = document.getElementById('bstop');
    
    const stream = await getstream();
    if (stream && video) {
        video.srcObject = stream;
        const track = stream.getVideoTracks()[0];
        capture = new ImageCapture(track);
        
        startButton.onclick = () => {
            video.srcObject = stream;
            setupWebSocket();
        };
        
        stopButton.onclick = () => {
            video.srcObject = null;
            stopStreaming();
            if (websocket) {
                websocket.close();
            }
        };
        
        // Initial WebSocket setup
        setupWebSocket();
    }
});
