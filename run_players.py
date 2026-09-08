"""Root shim — prefer `python -m ingestion.run_players`."""

from ingestion.run_players import main

if __name__ == "__main__":
    main()
