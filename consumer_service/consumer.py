import json
import asyncio
import os
from aiokafka import AIOKafkaConsumer
from motor.motor_asyncio import AsyncIOMotorClient
from dotenv import load_dotenv

load_dotenv()

# Mongo connection
MONGO_URI = os.getenv("MONGO_URL")
client = AsyncIOMotorClient(MONGO_URI)
db = client["SCM"]
device_stream_collection = db["device_stream"]

BOOTSTRAP = os.getenv("KAFKA_BOOTSTRAP", "kafka:9092")


async def main():
    consumer = AIOKafkaConsumer(
        "device-stream-topic",
        bootstrap_servers=BOOTSTRAP,
        group_id="device-stream-group",
        auto_offset_reset="latest",
        value_deserializer=lambda x: json.loads(x.decode("utf-8"))
    )

    # Wait for Kafka to be ready
    while True:
        try:
            await consumer.start()
            print("📥 Kafka Consumer Started")
            break
        except Exception as e:
            print("Retrying Kafka consumer...", e)
            await asyncio.sleep(5)

    try:
        async for msg in consumer:
            data = msg.value
            print("Received:", data)

            await device_stream_collection.insert_one(data)
            print("Saved to MongoDB")

    finally:
        await consumer.stop()
        print("Kafka Consumer Stopped")


if __name__ == "__main__":
    asyncio.run(main())
