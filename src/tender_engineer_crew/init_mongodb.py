"""CLI entrypoint to initialize MongoDB schema for tender processing."""

from tender_engineer_crew.tools.mongodb_utils import initialize_mongodb_schema


def run() -> None:
    """Initialize MongoDB collections, validators, and indexes."""
    success = initialize_mongodb_schema()
    if success:
        print("✅ MongoDB schema initialized successfully")
    else:
        raise SystemExit("❌ MongoDB schema initialization failed")


if __name__ == "__main__":
    run()
