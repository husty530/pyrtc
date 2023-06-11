let pc = null;
let dc = null;

function negotiate() {

  pc.addTransceiver('video', {direction: 'recvonly'});
  pc.addTransceiver('audio', {direction: 'recvonly'});
  return pc.createOffer().then(function(offer) {
    return pc.setLocalDescription(offer);
  }).then(function() {
    return new Promise(function(resolve) {
      if (pc.iceGatheringState === 'complete') {
        resolve();
      } else {
        function checkState() {
          if (pc.iceGatheringState === 'complete') {
            pc.removeEventListener('icegatheringstatechange', checkState);
            resolve();
          }
        }
        pc.addEventListener('icegatheringstatechange', checkState);
      }
    });
  }).then(function() {
    const offer = pc.localDescription;
    console.log('offer-sdp: ' + offer.sdp);
    return fetch('/offer', {
      body: JSON.stringify({ sdp: offer.sdp, type: offer.type }),
      headers: { 'Content-Type': 'application/json' },
      method: 'POST'
    });
  }).then(function(response) {
    return response.json();
  }).then(function(answer) {
    console.log('answer-sdp: ' + answer.sdp);
    return pc.setRemoteDescription(answer);
  }).catch(function(e) {
    alert(e);
  });

}

function start() {

  document.getElementById('start').style.display = 'none';
  const config = {
    sdpSemantics: 'unified-plan',
    iceServers: [{ urls: ['stun:stun.l.google.com:19302'] }]
  };
  
  pc = new RTCPeerConnection(config);
  pc.addEventListener('icegatheringstatechange', function() { console.log('ICE gathering state: ' + pc.iceGatheringState); }, false);
  pc.addEventListener('iceconnectionstatechange', function() { console.log('ICE connection state: ' + pc.iceConnectionState); }, false);
  pc.addEventListener('signalingstatechange', function() { console.log('Signaling state: ' + pc.signalingState); }, false);
  pc.addEventListener('track', function(evt) {
    console.log('receive track: ' + evt.track.kind)
    if (evt.track.kind == 'video')
      document.getElementById('video').srcObject = evt.streams[0];
    else
      document.getElementById('audio').srcObject = evt.streams[0];
  });

  dc = pc.createDataChannel('chat');
  let interval = null;
  dc.onclose = function() {
    clearInterval(interval);
    console.log('data channel closed');
  };
  dc.onopen = function() {
    console.log('data channel opened');
    interval = setInterval(function() {
      // TODO: implement data sending process and interval
      dc.send('hello from browser');
    }, 1000);
  };
  dc.onmessage = function(evt) {
    // TODO: implement callback for data arriving
    console.log('data: ' + evt.data);
  };

  negotiate();
  document.getElementById('stop').style.display = 'inline-block';

}

function stop() {

  document.getElementById('stop').style.display = 'none';

  if (dc) { dc.close(); }
  if (pc.getTransceivers) {
    pc.getTransceivers().forEach(function(transceiver) {
      if (transceiver.stop) { transceiver.stop(); }
    });
  }
  setTimeout(function() { pc.close(); }, 500);

}
