import cv2
import numpy as np
from aiortc import RTCPeerConnection, RTCSessionDescription
from aiortc.contrib.media import MediaStreamTrack
import asyncio

class VideoReceiver(MediaStreamTrack):
    """A class to receive video frames from a WebRTC stream."""
    kind = "video"

    def __init__(self, track):
        super().__init__()
        self.track = track

    async def recv(self):
        frame = await self.track.recv()
        return frame

class WebcamStreamer:
    def __init__(self, vive_server=None):
        self.vive_server = vive_server
        self.pcs = set()

    async def handle_offer(self, params):
        """Handle the WebRTC offer from the client."""
        offer = RTCSessionDescription(sdp=params["sdp"], type=params["type"])
        pc = RTCPeerConnection()
        self.pcs.add(pc)

        @pc.on("track")
        async def on_track(track):
            if self.vive_server:
                self.vive_server.log(f"Track {track.kind} received", "INFO")
            
            if track.kind == "video":
                local_video = VideoReceiver(track)
                # Start a new task to display the video stream
                asyncio.create_task(self.display_video(local_video))

            @track.on("ended")
            async def on_ended():
                if self.vive_server:
                    self.vive_server.log(f"Track {track.kind} ended", "INFO")

        await pc.setRemoteDescription(offer)
        answer = await pc.createAnswer()
        await pc.setLocalDescription(answer)

        return {"sdp": pc.localDescription.sdp, "type": pc.localDescription.type}

    async def display_video(self, video_track):
        """Display video frames in an OpenCV window."""
        cv2.namedWindow("ViVe Webcam Stream", cv2.WINDOW_NORMAL)
        while True:
            try:
                frame = await video_track.recv()
                img = frame.to_ndarray(format="bgr24")
                cv2.imshow("ViVe Webcam Stream", img)
                if cv2.waitKey(1) & 0xFF == ord('q'):
                    break
            except Exception as e:
                if self.vive_server:
                    self.vive_server.log(f"Error in video display loop: {e}", "ERROR")
                break
        cv2.destroyAllWindows()

    async def close(self):
        """Close all peer connections."""
        for pc in self.pcs:
            await pc.close()
        self.pcs.clear()
