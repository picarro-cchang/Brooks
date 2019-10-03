const WebSocket=require('ws');
const ws = new WebSocket("ws://localhost:8004/withSocket/ws");
ws.on('message', (data) => console.log(data));
ws.on('open', () => { setInterval( ()=>ws.send("Message from front end"), 1000)});