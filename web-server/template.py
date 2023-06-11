import os
import json
import argparse
import asyncio
import ssl
from aiohttp import web
from aiortc import RTCPeerConnection, RTCSessionDescription, RTCConfiguration, RTCIceServer
from aiortc.contrib.media import MediaPlayer
from aiortc.rtcrtpsender import RTCRtpSender

ROOT = os.path.dirname(__file__)
pc = RTCPeerConnection(configuration=RTCConfiguration([RTCIceServer("stun:stun.l.google:19302")]))

def force_codec(pc, sender, forced_codec):
  kind = forced_codec.split("/")[0]
  codecs = RTCRtpSender.getCapabilities(kind).codecs
  transceiver = next(t for t in pc.getTransceivers() if t.sender == sender)
  transceiver.setCodecPreferences(
    [codec for codec in codecs if codec.mimeType == forced_codec]
  )

async def index(request):
  content = open(os.path.join(ROOT, "index.html"), "r").read()
  return web.Response(content_type="text/html", text=content)

async def javascript(request):
  content = open(os.path.join(ROOT, "client.js"), "r").read()
  return web.Response(content_type="application/javascript", text=content)

async def offer(request):
  
  async def send_message(data_channel):
    while True:
      # TODO: implement data sending process and interval
      data_channel.send("hello from python server")
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
  
  params = await request.json()
  offer = RTCSessionDescription(sdp=params["sdp"], type=params["type"])
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
    
  await pc.setRemoteDescription(offer)
  await pc.setLocalDescription(await pc.createAnswer())
  return web.Response(
    content_type="application/json",
    text=json.dumps({"sdp": pc.localDescription.sdp, "type": pc.localDescription.type})
  )

async def on_shutdown(app):
  await pc.close()

if __name__ == "__main__":

  parser = argparse.ArgumentParser(description="Web application server")
  parser.add_argument("--audio-src")
  parser.add_argument("--audio-codec", help="Force a specific audio codec (e.g. audio/opus)")
  parser.add_argument("--video-src")
  parser.add_argument("--video-codec", help="Force a specific video codec (e.g. video/H264)")
  parser.add_argument("--format")
  parser.add_argument("--framerate", default="30")
  parser.add_argument("--framesize", default="640x480")
  parser.add_argument("--cert-file", help="SSL certificate file (for HTTPS)")
  parser.add_argument("--key-file", help="SSL key file (for HTTPS)")
  parser.add_argument("--host", default="0.0.0.0", help="Host for HTTP server (default: 0.0.0.0)")
  parser.add_argument("--port", type=int, default=8080, help="Port for HTTP server (default: 8080)")
  args = parser.parse_args()

  if args.cert_file:
    ssl_context = ssl.SSLContext()
    ssl_context.load_cert_chain(args.cert_file, args.key_file)
  else:
    ssl_context = None
    
  app = web.Application()
  app.on_shutdown.append(on_shutdown)
  app.router.add_get("/", index)
  app.router.add_get("/client.js", javascript)
  app.router.add_post("/offer", offer)
  web.run_app(app, access_log=None, host=args.host, port=args.port, ssl_context=ssl_context)
