import time
import logging
from unittest.mock import Mock, patch
from models.device_models import RFIDReader, MCP3008

logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


def test_basic_functionality():
    """Test basic RFID reading functionality"""
    print("\n=== Testing Basic Functionality ===")

    try:
        with RFIDReader() as reader:
            print("RFID Reader initialized successfully")
            print(f"Reader is active: {reader.is_active()}")

            print("\nScanning for RFID cards... (Press Ctrl+C to stop)")
            scan_count = 0
            max_scans = 20

            while scan_count < max_scans:
                card_id = reader.read_no_block()

                if card_id is not None:
                    print(f"Card detected! ID: {card_id}")
                    print(f"Card ID type: {type(card_id)}")
                    break
                else:
                    print(".", end="", flush=True)
                    time.sleep(0.5)
                    scan_count += 1

            if scan_count >= max_scans:
                print(f"\nNo card detected after {max_scans} attempts")

            print(f"\nReader still active: {reader.is_active()}")

    except KeyboardInterrupt:
        print("\nTest interrupted by user")
    except Exception as e:
        print(f"Error during basic test: {e}")


def test_multiple_reads():
    """Test multiple consecutive reads"""
    print("\n=== Testing Multiple Reads ===")

    try:
        reader = RFIDReader()
        print("Testing multiple read operations...")
        mpu = MCP3008(0, 1)

        for i in range(5):
            value = mpu.read_channel(0)
            print(f"MPU Channel 0 Value: {value}")
            print(f"Read attempt {i+1}:", end=" ")
            card_id = reader.read_no_block()

            if card_id:
                print(f"Card ID: {card_id}")
            else:
                print("No card detected")

            time.sleep(1)

        reader.cleanup()
        print("Multiple read test completed")

    except Exception as e:
        print(f"Error during multiple read test: {e}")


def test_cleanup_and_reactivation():
    """Test cleanup functionality and state management"""
    print("\n=== Testing Cleanup and State Management ===")

    try:
        reader = RFIDReader()
        print(f"Initial state - Active: {reader.is_active()}")

        result = reader.read_no_block()
        print(f"Read result while active: {result is not None}")

        reader.cleanup()
        print(f"After cleanup - Active: {reader.is_active()}")

        result = reader.read_no_block()
        print(f"Read result after cleanup: {result}")

    except Exception as e:
        print(f"Error during cleanup test: {e}")


def test_context_manager():
    """Test context manager functionality"""
    print("\n=== Testing Context Manager ===")

    try:
        print("Testing 'with' statement...")

        with RFIDReader() as reader:
            print(f"Inside context - Active: {reader.is_active()}")
            card_id = reader.read_no_block()
            print(f"Read attempt result: {'Card detected' if card_id else 'No card'}")

        print(f"Outside context - Active: {reader.is_active()}")

    except Exception as e:
        print(f"Error during context manager test: {e}")


def test_error_handling():
    """Test error handling with mocked exceptions"""
    print("\n=== Testing Error Handling ===")

    try:
        with patch("rfid_reader.SimpleMFRC522") as mock_reader_class:
            mock_instance = Mock()
            mock_instance.read_no_block.side_effect = Exception("Simulated read error")
            mock_reader_class.return_value = mock_instance

            reader = RFIDReader()
            print("Testing error handling during read...")

            result = reader.read_no_block()
            print(f"Result when exception occurs: {result}")

            reader.cleanup()
            print("Error handling test completed")

    except Exception as e:
        print(f"Error during error handling test: {e}")


def continuous_monitoring_test(duration=30):
    """Continuous monitoring test"""
    print(f"\n=== Continuous Monitoring Test ({duration}s) ===")

    try:
        with RFIDReader() as reader:
            print(f"Monitoring for {duration} seconds...")
            print("Present and remove RFID cards to test detection")

            start_time = time.time()
            last_card_id = None
            detection_count = 0

            while time.time() - start_time < duration:
                current_card_id = reader.read_no_block()

                if current_card_id != last_card_id:
                    if current_card_id is not None:
                        detection_count += 1
                        print(
                            f"[{time.strftime('%H:%M:%S')}] Card detected: {current_card_id}"
                        )
                    elif last_card_id is not None:
                        print(f"[{time.strftime('%H:%M:%S')}] Card removed")

                    last_card_id = current_card_id

                time.sleep(0.1)

            print(f"\nMonitoring completed. Total detections: {detection_count}")

    except KeyboardInterrupt:
        print("\nMonitoring interrupted by user")
    except Exception as e:
        print(f"Error during continuous monitoring: {e}")


def performance_test():
    """Test reading performance"""
    print("\n=== Performance Test ===")

    try:
        reader = RFIDReader()
        num_reads = 100

        print(f"Performing {num_reads} read operations...")
        start_time = time.time()

        successful_reads = 0
        for i in range(num_reads):
            result = reader.read_no_block()
            if result is not None:
                successful_reads += 1

        end_time = time.time()
        duration = end_time - start_time

        print(f"Completed {num_reads} reads in {duration:.2f} seconds")
        print(f"Average time per read: {(duration/num_reads)*1000:.2f} ms")
        print(f"Successful reads: {successful_reads}")
        print(f"Read rate: {num_reads/duration:.2f} reads/second")

        reader.cleanup()

    except Exception as e:
        print(f"Error during performance test: {e}")


def main():
    """Main test function"""
    # print("RFID Reader Test Program")y
    # print("=" * 40)
    # test_basic_functionality()
    test_multiple_reads()
    # test_cleanup_and_reactivation()
    # test_context_manager()
    # test_error_handling()
    # performance_test()
    response = input("\nRun continuous monitoring test? (y/n): ").lower().strip()
    if response == "y":
        try:
            duration = int(input("Enter duration in seconds (default 30): ") or "30")
            continuous_monitoring_test(duration)
        except ValueError:
            print("Invalid duration, using 30 seconds")
            continuous_monitoring_test(30)

    print("\n" + "=" * 40)
    print("All tests completed!")


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\nTest program interrupted by user")
    except Exception as e:
        print(f"Unexpected error: {e}")
        logger.error(f"Unexpected error in main: {e}")
    finally:
        print("Test program finished")
