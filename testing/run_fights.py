import argparse
import json
import re
import subprocess
from collections import Counter
from datetime import datetime
from pathlib import Path


RESULT_PATTERN = re.compile(r"team ([AB]) wins after (\d+) rounds")


def run_match(project_root: Path, map_path: str, team_a: str, team_b: str, keep_replays: bool) -> dict:
    command = [
        "unswbc",
        "run",
        map_path,
        team_a,
        team_b,
        "--no-logs",
        "--no-indicator",
        "--no-draw",
        "--no-debug",
    ]
    if not keep_replays:
        command.append("--no-replay")
    completed = subprocess.run(
        command,
        cwd=project_root,
        capture_output=True,
        text=True,
        check=False,
    )
    output = f"{completed.stdout}\n{completed.stderr}"
    result = RESULT_PATTERN.search(output)

    if completed.returncode != 0:
        return {
            "team_a": team_a,
            "team_b": team_b,
            "winner": "error",
            "rounds": "",
            "error": output.strip()[-1000:],
        }

    if result is None:
        return {
            "team_a": team_a,
            "team_b": team_b,
            "winner": "unknown",
            "rounds": "",
            "error": "Could not find a winner in unswbc output.",
        }

    winner = team_a if result.group(1) == "A" else team_b
    return {
        "team_a": team_a,
        "team_b": team_b,
        "winner": winner,
        "rounds": result.group(2),
        "error": "",
    }


def main() -> None:
    parser = argparse.ArgumentParser(description="Run repeated UNSW bot-versus-bot fights.")
    parser.add_argument("--matches", type=int, default=10, help="Number of fights to run (default: 10).")
    parser.add_argument("--map", default="maps/default.map", dest="map_path", help="Map path (default: maps/default.map).")
    parser.add_argument("--altbot", default="baselinebot", help="First bot directory (default: baselinebot).")
    parser.add_argument("--mybot", default="mybot", help="Second bot directory (default: mybot).")
    parser.add_argument("--output", default="fight_results", help="Output file prefix (default: fight_results).")
    parser.add_argument("--keep-replays", action="store_true", help="Keep replay files in replays/.")
    args = parser.parse_args()

    if args.matches < 1:
        parser.error("--matches must be at least 1")

    script_dir = Path(__file__).resolve().parent
    project_root = script_dir.parent
    output_path = Path(args.output)
    if not output_path.is_absolute():
        output_path = script_dir / output_path
    results_path = Path(f"{output_path}.json")
    results_path.parent.mkdir(parents=True, exist_ok=True)
    results = []

    for match_number in range(1, args.matches + 1):
        if match_number % 2:
            team_a, team_b = args.altbot, args.mybot
        else:
            team_a, team_b = args.mybot, args.altbot

        print(f"Match {match_number}/{args.matches}: {team_a} vs {team_b}...", flush=True)
        result = run_match(project_root, args.map_path, team_a, team_b, args.keep_replays)
        result = {"match": match_number, "map": args.map_path, **result}
        results.append(result)

        if result["winner"] in (args.altbot, args.mybot):
            print(f"  winner: {result['winner']} ({result['rounds']} rounds)")
        else:
            print(f"  result: {result['winner']} - {result['error']}")

    counts = Counter(result["winner"] for result in results)
    summary = {
        "created_at": datetime.now().isoformat(timespec="seconds"),
        "map": args.map_path,
        "matches": args.matches,
        "wins": {args.altbot: counts[args.altbot], args.mybot: counts[args.mybot]},
        "other_results": counts["unknown"] + counts["error"],
        "results_file": str(results_path),
    }

    payload = {
        "summary": summary,
        "results": results,
    }

    with results_path.open("w", encoding="utf-8") as file:
        json.dump(payload, file, indent=2)
        file.write("\n")

    print(f"\nResults: {args.altbot} {counts[args.altbot]} wins, {args.mybot} {counts[args.mybot]} wins")
    if summary["other_results"]:
        print(f"Unresolved matches: {summary['other_results']}")
    print(f"Saved to {results_path}")


if __name__ == "__main__":
    main()