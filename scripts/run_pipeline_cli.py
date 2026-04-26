"""
CLI tool to test the pipeline without the web server.
Usage: python scripts/run_pipeline_cli.py <input.mp4> [--handle Name] [--color blue]
"""
import os, sys, argparse, time
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from pipeline.orchestrator import run_pipeline


def main():
    """Execute main operation."""
    parser = argparse.ArgumentParser(description="Topcoder Video Pipeline CLI")
    parser.add_argument("input", help="Path to raw input video")
    parser.add_argument("--output", "-o", default="output_final.mp4", help="Output path")
    parser.add_argument("--handle", default="TechStar", help="Member handle")
    parser.add_argument("--color", default="blue",
                        choices=["red","yellow","blue","green","gray"],
                        help="Rating color")
    parser.add_argument("--tracks", default="development",
                        help="Comma-separated tracks")
    parser.add_argument("--tagline", default="", help="Optional tagline")
    args = parser.parse_args()

    if not os.path.exists(args.input):
        print(f"❌ File not found: {args.input}")
        sys.exit(1)

    metadata = {
        "handle": args.handle,
        "rating_color": args.color,
        "tracks": [t.strip() for t in args.tracks.split(",")],
        "tagline": args.tagline,
    }

    print(f"\n🎬 Topcoder Profile Video Pipeline v3")
    print(f"   Input:  {args.input}")
    print(f"   Output: {args.output}")
    print(f"   Handle: {metadata['handle']}")
    print(f"   Color:  {metadata['rating_color']}")
    print(f"   Tracks: {metadata['tracks']}")
    print()

    start = time.time()

    def progress(p):
        """Execute progress operation."""
        bar = "█" * (p // 2) + "░" * (50 - p // 2)
        print(f"\r   [{bar}] {p}%", end="", flush=True)

    run_pipeline(
        video_path=args.input,
        metadata=metadata,
        output_path=args.output,
        progress_callback=progress,
    )

    elapsed = time.time() - start
    print(f"\n\n✅ Done in {elapsed:.1f}s -> {args.output}")


if __name__ == "__main__":
    main()
