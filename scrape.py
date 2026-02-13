import argparse
import sys
from scraper.orchestrator import Orchestrator
from config.settings import (
    DEFAULT_LIMIT, RATE_LIMIT, CONCURRENCY,
    OUTPUT_PATH, METADATA_DB
)


def parse_args():
    """Parse command-line arguments"""
    parser = argparse.ArgumentParser(
        description='Tender Scraper POC - Extract tenders from tender.nprocure.com',
        formatter_class=argparse.ArgumentDefaultsHelpFormatter
    )

    parser.add_argument(
        '--limit',
        type=int,
        default=DEFAULT_LIMIT,
        help='Maximum number of tenders to scrape (for demo runs)'
    )

    parser.add_argument(
        '--rate-limit',
        type=float,
        default=RATE_LIMIT,
        help='Rate limit in requests per second'
    )

    parser.add_argument(
        '--concurrency',
        type=int,
        default=CONCURRENCY,
        help='Number of concurrent requests'
    )

    parser.add_argument(
        '--output',
        type=str,
        default=OUTPUT_PATH,
        help='Output file path for tender data'
    )

    parser.add_argument(
        '--metadata-db',
        type=str,
        default=METADATA_DB,
        help='Path to metadata SQLite database'
    )

    return parser.parse_args()


def main():
    """Main entry point"""
    args = parse_args()

    print(f"""
╔════════════════════════════════════════════════════════════╗
║          TENDER SCRAPER POC - tender.nprocure.com          ║
╚════════════════════════════════════════════════════════════╝

Configuration:
  - Limit:         {args.limit} tenders
  - Rate Limit:    {args.rate_limit} req/s
  - Concurrency:   {args.concurrency}
  - Output:        {args.output}
  - Metadata DB:   {args.metadata_db}

""")

    try:
        orchestrator = Orchestrator(
            limit=args.limit,
            rate_limit=args.rate_limit,
            concurrency=args.concurrency,
            output_path=args.output,
            metadata_db=args.metadata_db
        )

        orchestrator.run()

        print(f"""
╔════════════════════════════════════════════════════════════╗
║                    RUN COMPLETED ✓                         ║
╚════════════════════════════════════════════════════════════╝

Output files:
  - Tenders:  {args.output}
  - Metadata: {args.metadata_db}

Run ID: {orchestrator.get_metadata().run_id}
""")

        return 0

    except KeyboardInterrupt:
        print("\n\n[!] Scraper interrupted by user")
        return 130

    except Exception as e:
        print(f"\n\n[ERROR] Scraper failed: {e}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    sys.exit(main())