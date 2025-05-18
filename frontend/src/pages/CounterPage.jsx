import React, { useState, useEffect, useRef } from 'react';

const FPS = 1; // Frames per second to send to backend

function CounterPage() {
    const [university, setUniversity] = useState('');
    const [building, setBuilding] = useState('');
    const [infoSubmitted, setInfoSubmitted] = useState(false);
    const [isStreaming, setIsStreaming] = useState(false);
    const [peopleCount, setPeopleCount] = useState(0);
    const [error, setError] = useState('');

    const videoRef = useRef(null);
    const streamRef = useRef(null);
    const imageCaptureRef = useRef(null);
    const websocketRef = useRef(null);
    const intervalRef = useRef(null);

    useEffect(() => {
        // Cleanup on component unmount
        return () => {
            stopStreaming();
            if (websocketRef.current) {
                websocketRef.current.close();
            }
            if (streamRef.current) {
                streamRef.current.getTracks().forEach(track => track.stop());
            }
        };
    }, []);

    const handleInfoSubmit = (e) => {
        e.preventDefault();
        if (university && building) {
            setInfoSubmitted(true);
            setError('');
        } else {
            setError('Please enter both university and building name.');
        }
    };

    async function getMediaStream() {
        try {
            const stream = await navigator.mediaDevices.getUserMedia({ video: true });
            streamRef.current = stream;
            if (videoRef.current) {
                videoRef.current.srcObject = stream;
            }
            const track = stream.getVideoTracks()[0];
            imageCaptureRef.current = new ImageCapture(track);
            return true;
        } catch (err) {
            console.error("Error opening video camera.", err);
            setError('Could not access the camera. Please check permissions.');
            return false;
        }
    }

    async function convertBitmapToBlob(bitmap) {
        const canvas = new OffscreenCanvas(bitmap.width, bitmap.height);
        const ctx = canvas.getContext('2d');
        if (ctx) {
            ctx.drawImage(bitmap, 0, 0);
            return await canvas.convertToBlob({ type: 'image/jpeg', quality: 0.8 });
        }
        return null;
    }

    function setupWebSocket() {
        const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
        const wsUrl = `${protocol}//${window.location.host}/ws`;
        
        const ws = new WebSocket(wsUrl);

        ws.onopen = () => {
            console.log('WebSocket connected');
            setError('');
            startSendingFrames();
        };

        ws.onmessage = (event) => {
            try {
                const data = JSON.parse(event.data);
                if (data.numberOfPeople !== undefined) {
                    setPeopleCount(data.numberOfPeople);
                }
            } catch (err) {
                console.error('Error parsing WebSocket message:', err);
            }
        };

        ws.onerror = (err) => {
            console.error('WebSocket error:', err);
            setError('WebSocket connection error. Trying to reconnect...');
            // Optional: Add more robust error display to the user
        };

        ws.onclose = () => {
            console.log('WebSocket disconnected');
            if (isStreaming) { // if streaming was active, try to reconnect
                 setError('WebSocket disconnected. Attempting to reconnect...');
                 setTimeout(setupWebSocket, 5000); // Attempt to reconnect after 5 seconds
            }
        };
        websocketRef.current = ws;
    }

    async function startSendingFrames() {
        if (intervalRef.current) clearInterval(intervalRef.current);

        intervalRef.current = setInterval(async () => {
            if (imageCaptureRef.current && websocketRef.current && websocketRef.current.readyState === WebSocket.OPEN) {
                try {
                    const bitmap = await imageCaptureRef.current.grabFrame();
                    const blob = await convertBitmapToBlob(bitmap);
                    if (blob) {
                        websocketRef.current.send(blob);
                    }
                } catch (err) {
                    console.error('Error capturing or sending frame:', err);
                    // If grabFrame fails often, it might be due to camera access issues
                    // or the track ending.
                }
            }
        }, 1000 / FPS);
    }
    
    const startStreamAndProcessing = async () => {
        if (!infoSubmitted) {
            setError("Please submit university and building information first.");
            return;
        }
        setIsStreaming(true);
        const mediaStreamReady = await getMediaStream();
        if (mediaStreamReady) {
            setupWebSocket();
        } else {
            setIsStreaming(false); // Failed to get media stream
        }
    };

    const stopStreaming = () => {
        setIsStreaming(false);
        if (intervalRef.current) {
            clearInterval(intervalRef.current);
            intervalRef.current = null;
        }
        if (websocketRef.current) {
            websocketRef.current.close();
            websocketRef.current = null;
        }
        if (streamRef.current) {
            streamRef.current.getTracks().forEach(track => track.stop());
            streamRef.current = null;
        }
        if (videoRef.current) {
            videoRef.current.srcObject = null;
        }
        // Keep university/building info, but reset people count if desired
        // setPeopleCount(0); 
    };

    if (!infoSubmitted) {
        return (
            <div>
                <h2>Enter Location Information</h2>
                <form onSubmit={handleInfoSubmit}>
                    <div>
                        <label htmlFor="university">University/School:</label>
                        <input
                            type="text"
                            id="university"
                            value={university}
                            onChange={(e) => setUniversity(e.target.value)}
                            required
                        />
                    </div>
                    <div>
                        <label htmlFor="building">Building Name/Number:</label>
                        <input
                            type="text"
                            id="building"
                            value={building}
                            onChange={(e) => setBuilding(e.target.value)}
                            required
                        />
                    </div>
                    <button type="submit">Submit</button>
                </form>
                {error && <p style={{ color: 'red' }}>{error}</p>}
            </div>
        );
    }

    return (
        <div>
            <h2>Live Counter</h2>
            <p>University: {university}</p>
            <p>Building: {building}</p>
            <video ref={videoRef} autoPlay playsInline muted style={{ width: '640px', height: '480px', border: '1px solid black' }}></video>
            <div>
                {!isStreaming ? (
                    <button onClick={startStreamAndProcessing}>Start Camera & Count</button>
                ) : (
                    <button onClick={stopStreaming}>Stop Camera & Count</button>
                )}
            </div>
            <h3>People Detected: {peopleCount}</h3>
            {error && <p style={{ color: 'red' }}>{error}</p>}
        </div>
    );
}

export default CounterPage; 