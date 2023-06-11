import argparse
import asyncio
from aiortc import RTCIceCandidate, RTCPeerConnection, RTCSessionDescription, RTCConfiguration, RTCIceServer
from aiortc.contrib.media import MediaPlayer
from aiortc.rtcrtpsender import RTCRtpSender
from aiortc.contrib.signaling import BYE, add_signaling_arguments, create_signaling
import cv2

def force_codec(pc, sender, forced_codec):
  kind = forced_codec.split("/")[0]
  codecs = RTCRtpSender.getCapabilities(kind).codecs
  transceiver = next(t for t in pc.getTransceivers() if t.sender == sender)
  transceiver.setCodecPreferences(
    [codec for codec in codecs if codec.mimeType == forced_codec]
  )

async def run(pc, signaling):

  async def send_message(data_channel):
    while True:
      # TODO: implement data sending process and interval
      data_channel.send("hello from python client")
      await asyncio.sleep(1)

  @pc.on("datachannel")
  def on_datachannel(data_channel):
    asyncio.ensure_future(send_message(data_channel))
    @data_channel.on("message")
    def on_message(message):
      # TODO: implement callback for data arriving
      print(message)

  @pc.on("connectionstatechange")
  async def on_connectionstatechange():
    if pc.connectionState == "failed":
      await pc.close()
    
  @pc.on("track")
  async def on_track(track):
    if track.kind == "audio":
      while True:
        f = await track.recv()
        # TODO: implement callback for audio frame arriving
    if track.kind == "video":
      while True:
        f = await track.recv()
        # TODO: implement callback for video frame arriving
        img = f.to_ndarray(format="bgr24")
        cv2.imshow("FROM_SERVER", img)
        cv2.waitKey(1)

  await signaling.connect()

  while True:
    obj = await signaling.receive()
    if isinstance(obj, RTCSessionDescription):
      await pc.setRemoteDescription(obj)
      if args.audio_src:
        player = MediaPlayer(args.audio_src)
        sender = pc.addTrack(player.audio)
        if args.audio_codec:
          force_codec(pc, sender, args.audio_codec)
      if args.video_src:
        options = {"framerate": args.framerate, "video_size": args.framesize}
        player = MediaPlayer(args.video_src, format=args.format, options=options)
        sender = pc.addTrack(player.video)
        if args.video_codec:
          force_codec(pc, sender, args.video_codec)
      await pc.setLocalDescription(await pc.createAnswer())
      await signaling.send(pc.localDescription)
    elif isinstance(obj, RTCIceCandidate):
      await pc.addIceCandidate(obj)
    elif obj is BYE:
      break

if __name__ == "__main__":

  parser = argparse.ArgumentParser(description="P2P stream client")
  parser.add_argument("--audio-src")
  parser.add_argument("--audio-codec", help="Force a specific audio codec (e.g. audio/opus)")
  parser.add_argument("--video-src")
  parser.add_argument("--video-codec", help="Force a specific video codec (e.g. video/H264)")
  parser.add_argument("--format")
  parser.add_argument("--framerate", default="30")
  parser.add_argument("--framesize", default="640x480")
  add_signaling_arguments(parser)
  args = parser.parse_args()

  signaling = create_signaling(args)
  pc = RTCPeerConnection(configuration=RTCConfiguration([RTCIceServer("stun:stun.l.google:19302")]))
  loop = asyncio.get_event_loop()
  try:
    loop.run_until_complete(run(pc, signaling))
  except KeyboardInterrupt:
    pass
  finally:
    loop.run_until_complete(signaling.close())
    loop.run_until_complete(pc.close())
