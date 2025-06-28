document.addEventListener('DOMContentLoaded', () => {
    const startButton = document.getElementById('start-stream');
    const videoElement = document.getElementById('video');
    const statusElement = document.getElementById('status');
    let pc = null;

    startButton.onclick = async () => {
        statusElement.textContent = 'Status: Starting...';
        
        const stream = await navigator.mediaDevices.getUserMedia({ video: { facingMode: 'environment' } });
        videoElement.srcObject = stream;

        pc = new RTCPeerConnection();

        stream.getTracks().forEach(track => {
            pc.addTrack(track, stream);
        });

        pc.oniceconnectionstatechange = () => {
            statusElement.textContent = `Status: ${pc.iceConnectionState}`;
        };

        const offer = await pc.createOffer();
        await pc.setLocalDescription(offer);

        const response = await fetch('/api/webcam/offer', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({ sdp: pc.localDescription.sdp, type: pc.localDescription.type }),
        });

        const answer = await response.json();
        await pc.setRemoteDescription(answer);
        
        startButton.disabled = true;
    };
});
