import time
from models.device_models import (
    MCP3008,
    RFIDReader,
)


CARD_READER = RFIDReader()


MCP = MCP3008(0, 1)
try:
    while True:
        print("Reading MCP3008 values...")

        print(f"Channel {0}: {MCP.read_channel(0)}")

        print("Reading RFID card...")
        card_data = CARD_READER.read_no_block()
        if card_data:
            print(f"Card Data: {card_data}")
        else:
            print("No card detected.")
        time.sleep(1)
except Exception as e:
    print(f"An error occurred: {e}")
except KeyboardInterrupt:
    print("Exiting...")
finally:
    print("Cleaning up resources...")
    MCP.close()
    # CARD_READER.cleanup()
