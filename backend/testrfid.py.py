import threading
import time

from mfrc522 import SimpleMFRC522

CARD_READER = SimpleMFRC522()


def front_door():
    global CARD_READER
    scanned_card = None

    while True:
        try:
            scanned_card = CARD_READER.read_no_block()
            print(f"Scanned card: {scanned_card}")
            # await asyncio.sleep(0)

            if scanned_card is not None:
                print(f"Card {scanned_card} detected at the front door.")

        except Exception as e:
            print(f"Error reading card: {e}")
            # await asyncio.sleep(1)


threading.Thread(
    target=front_door,
    daemon=True,
).start()

try:
    while True:
        # Keep the main thread alive
        time.sleep(1)
except KeyboardInterrupt:
    print("Exiting program.")
    CARD_READER.cleanup()
    exit(0)
#         print("Starting RFID reader...")
