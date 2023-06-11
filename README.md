# PyRTC - example codes using aiortc

[aiortc](https://github.com/aiortc/aiortc)を使ってみようという試みです．  
自分もよくわかっていないところがあり，いろいろ適当です．とりあえずミニマムに作ったつもりです．  
まだローカルでしか試してないので，NAT越えがどうだとかは何もしていません．  
ライブラリの実装見るかぎり，このままではポート開放が要りそうですが．  
自分で外部サーバ立てるなら[aioice](https://github.com/aiortc/aioice)とかを使うことになるんですかね．  

一応テンプレとして使えるようにファイル名はtemplateに，使うときに適宜書き換えてほしいところは"TODO: implement ~"と記しています．  
このリポジトリでやっていることは以下の2パターンです．  
Windowsで行う前提で進めます．まずはpipで必要なパッケージを入れてから次に進んでください．  
```
pip install aiohttp aiortc opencv-python
```

## Python(server) <---> JavaScript(client)
* data channel  ... server <---> client
* media channel ... server ----> client

起動コマンドは以下のように打ちます．  
```
cd web-server
python template.py --video-src <camera_name> --format dshow
```
<camera_name>はPCに認識されているWebカメラの名前を入れてください．  
dshowで使えるWebカメラを以下のコマンドで検索することができます．  
```
ffmpeg -f dshow -list_devices true -i ""
```
私はHPの標準Webカメラ名が"video=HP Wide Vision HD Camera"でした．  

Webカメラをそのまま流すようにしていますが，OpenCVのndarrayからTrackを作成することも可能です．  
ここには書きませんが公式のexamplesに書き方の見本があるので，必要ならやってみてください．  
アプリを利用するclientはブラウザで次のURLを叩き入ります．  
```
https://localhost:8080
```
serverがビデオを流していたらStartでキャプチャ画面が出るはずです．  
接続状況やdata channelの挙動は開発者ツール(F12)のConsoleで見ることができます．  

## Python(server) <---> Python(client)
* data channel  ... server <---> client
* media channel ... server <---> client

server-->clientでビデオを送る場合の起動コマンドは以下のように打ちます．  
```
cd cli-server
python template.py --signaling tcp-socket --video-src <camera_name> --format dshow
```
もう一つのターミナルで，  
```
cd cli-client
python template.py --signaling tcp-socket
```
これでOpenCVのWindowが出ればOKです．  

起動時に--signaling-host, --signaling-portを指定できるので，グローバルIPでやりたいときはここをいじればいいんですかね？  

一旦ここまで．  