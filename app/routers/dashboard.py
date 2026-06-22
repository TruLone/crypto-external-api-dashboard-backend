import asyncio
from fastapi import APIRouter, WebSocket, WebSocketDisconnect
import httpx

router = APIRouter(
    tags=["Real-Time Dashboard"]
)

CRYPTO_API_URL = "https://api.coingecko.com/api/v3/simple/price?ids=bitcoin,ethereum,solana&vs_currencies=usd"


def get_mock_prices():
    import random
    return {
        "bitcoin": round(random.uniform(30000, 40000), 2),
        "ethereum": round(random.uniform(2000, 3000), 2),
        "note": "This is mock data. Public API rate limited."
    }

class ConnectionManager:
    def __init__(self):
        self.active_connections: list[WebSocket] = []

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.append(websocket)
        print(f"[WebSocket] New client connected. Total connections: {len(self.active_connections)}")

    def disconnect(self, websocket: WebSocket):
        self.active_connections.remove(websocket)
        print(f"[WebSocket] Client disconnected. Total connections: {len(self.active_connections)}")

    async def send_json(self, message: dict):
        tasks = []
        for connection in self.active_connections:
            tasks.append(connection.send_json(message))

        if tasks:
            await asyncio.gather(*tasks, return_exceptions=True)

manager = ConnectionManager()

async def crypto_background_fetcher():
    while True:
        async with httpx.AsyncClient() as client:
            try:
                response = await client.get(CRYPTO_API_URL, follow_redirects=True, timeout=5.0)
                
                if response.status_code == 200:
                    payload_data = response.json()
                else:
                    payload_data = get_mock_prices()
            except Exception as e:
                print(f"[Background Fetcher] Connection error: {e}")
                payload_data = get_mock_prices()
        await manager.send_json({
                "timestamp": asyncio.get_event_loop().time(),
                "active_clients": len(manager.active_connections),
                "prices": payload_data
            })
        await asyncio.sleep(5)  # Send updates every 5 seconds

@router.get("/crypto/latest")
async def get_latest_crypto_prices():
    async with httpx.AsyncClient() as client:
        try:
            response = await client.get(CRYPTO_API_URL, follow_redirects=True, timeout=5.0)
            
            if response.status_code == 200:
                return response.json()
            else:
                return get_mock_prices()
        except Exception as e:
            print(f"[HTTP Endpoint] Connection error: {e}")
            return get_mock_prices()

@router.websocket("/ws/crypto")
async def stream_crypto_prices(websocket: WebSocket):
    await manager.connect(websocket)
    try:
        while True:
            await websocket.receive_text()  # Keep connection alive
    except WebSocketDisconnect:
        manager.disconnect(websocket)