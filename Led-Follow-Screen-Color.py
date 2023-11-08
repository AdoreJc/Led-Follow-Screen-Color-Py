import asyncio
from bleak import BleakClient
from colorthief import ColorThief
import io
from PIL import ImageGrab
import time

address = "23:01:02:0c:b3:87"
uuid = "0000afd1-0000-1000-8000-00805f9b34fb"

Is_On = 1

ON_HEX = "5bf000b5"
OFF_HEX = "5b0f00b5"

client = BleakClient

async def send_color_to_device(Client: BleakClient, color = "ff ff ff", dim = "64", speed = "00"):
    header = bytes.fromhex("5a 00 01")
    footer = bytes.fromhex("00 a5")
    value = header + bytes.fromhex(color) + bytes.fromhex(speed) + bytes.fromhex(dim) + footer
    await Client.write_gatt_char(uuid, value)

# inbuild effects hex: str 80-96; int 0-22
async def effects(Client: BleakClient, mod = "80", dim = "64", speed = "00"):
    if isinstance(mod, int):
        value = int(128 + mod).to_bytes(1,"big")
    else:
        value = bytes.fromhex(mod)
    header = bytes.fromhex("5c 00")
    footer = bytes.fromhex("00 c5")
    await Client.write_gatt_char(uuid, header + value + bytes.fromhex(speed) + bytes.fromhex(dim) + footer)

# inbuild effects: hex 01-04
async def mic_effect(Client: BleakClient, mod = "01"):
    header = bytes.fromhex("5a 0a f0")
    footer = bytes.fromhex("01 a5")
    await Client.write_gatt_char(uuid, header + bytes.fromhex(mod) + footer)

# inbuild effects: int 1-4
async def mic_effect(Client: BleakClient, mod = 1):
    header = bytes.fromhex("5a 0a f0")
    footer = bytes.fromhex("01 a5")
    await Client.write_gatt_char(uuid, header + int.to_bytes(mod) + footer)

async def toggle_on(Client: BleakClient, _uuid = uuid) -> None:
    await Client.write_gatt_char(_uuid, bytes.fromhex(ON_HEX))
    print("Turned on")

async def toggle_off(Client: BleakClient, _uuid = uuid) -> None:
    await Client.write_gatt_char(_uuid, bytes.fromhex(OFF_HEX))
    print("Turned off")

async def init_client(address: str) -> BleakClient:
    client =  BleakClient(address)  
    print("Connecting")
    await client.connect()
    print(f"Connected to {address}")
    return client

async def on_exit(Client = client) -> None:
    if Client is not None:
        await disconnect_client(client)
    print("Exited")

# setup screenshot region
screen_width, screen_height = ImageGrab.grab().size
region_width = 640
region_height = 480
region_left = (screen_width - region_width) // 2
region_top = (screen_height - region_height) // 2
screen_region = (region_left, region_top, region_left + region_width, region_top + region_height)

screenshot_memory = io.BytesIO(b"")

def get_dominant_colour() -> str:
    try:
        screenshot = ImageGrab.grab(screen_region)
        screenshot_memory.seek(0)
        screenshot_memory.truncate(0)
        screenshot.save("tmp.png") 
        color_thief = ColorThief("tmp.png")
        # Get the dominant color
        dominant_color = color_thief.get_color(quality=20)
    except Exception as e:
        print(f"Error: {e}")
        return "00 00 00"
    finally:
        #print("Color #", dominant_color)
        return '{:02x}{:02x}{:02x}'.format(*dominant_color)
    #print("Color #", dominant_color)
    return '{:02x}{:02x}{:02x}'.format(*dominant_color)

async def loop_dominant_color(Client: BleakClient, gap = 0.12, dim = "64", speed = "00"):
    while True:
        await send_color_to_device(Client, get_dominant_colour(), dim, speed)
        #command = bytes.fromhex(get_dominant_colour())
        #await client.write_gatt_char(uuid, header + command + params)
        time.sleep(gap)

async def main(address): 
    print("Connecting")
    async with BleakClient(address) as cli:
        client = cli
        print("Connected")
        await toggle_on(client, uuid)
        #await send_color_to_device(client, "ff ff ff", "64", "00")
        #await effects(client, 1, "64", "00")
        #await effects(client, "80", "64", "00")
        #await mic_effect(client, 1)
        await loop_dominant_color(client, 0.12, "64", "00")
        #await toggle_off(client, uuid)

def run_main(address):
    # kick off the main functon in an asyncioi event loop
    loop = asyncio.get_event_loop()
    loop.run_until_complete(main(address))
    loop.close()

if __name__ == "__main__": 
    run_main(address)
