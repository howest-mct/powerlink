import asyncio


async def task1():
    await asyncio.sleep(1)
    print("Task 1 running")
    return "Result 1"


async def task2():
    await asyncio.sleep(2)
    print("Task 2 running")
    return "Result 2"


async def task3():
    await asyncio.sleep(1.5)
    print("Task 3 running")
    return "Result 3"


async def main():
    # Create tasks
    tasks = [
        asyncio.create_task(task1()),
        asyncio.create_task(task2()),
        asyncio.create_task(task3()),
    ]

    # Print the tasks list to show what's being unpacked
    print("Tasks before unpacking:", tasks)

    # Unpack tasks with * and await their completion
    results = await asyncio.gather(*tasks, return_exceptions=True)

    # Print the results
    print("Results after gathering:", results)

    # Simulate shutdown with cancellation (for completeness)
    for task in tasks:
        task.cancel()
    await asyncio.gather(*tasks, return_exceptions=True)
    print("Tasks canceled and cleaned up")


# Run the example
if __name__ == "__main__":
    asyncio.run(main())
