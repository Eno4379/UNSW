import argparse
import csv
import json
import re
import subprocess
from datetime import datetime
from pathlib import Path


RESULT_PATTERN = re.compile(r"team ([AB]) wins after (\d+) rounds")


def run_match(project_root: Path, map_path: Path, mybot: str, altbot: str, keep_replay: bool) -> dict:
    command = [
        "unswbc",
        "run",
        str(map_path),
        mybot,
        altbot,
        "--no-logs",
        "--no-indicator",
        "--no-draw",
        "--no-debug",
    ]
    if not keep_replay:
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
            "map": str(map_path),
            "winner": "error",
            "rounds": "",
            "error": output.strip()[-1000:],
        }

    if result is None:
        return {
            "map": str(map_path),
            "winner": "unknown",
            "rounds": "",
            "error": "Could not find a winner in unswbc output.",
        }

    winner = mybot if result.group(1) == "A" else altbot
    return {
        "map": str(map_path),
        "winner": winner,
        "rounds": result.group(2),
        "error": "",
    }


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Run one mybot-versus-baselinebot match on every map."
    )
    parser.add_argument("--mybot", default="mybot", help="mybot directory")
    parser.add_argument("--altbot", default="baselinebot", help="baselinebot directory")
    parser.add_argument(
        "--matches-per-map",
        type=int,
        default=20,
        help="How many times each map is played (default: 20)",
    )
    parser.add_argument(
        "--output",
        default="all_maps_results",
        help="Output file prefix (default: all_maps_results)",
    )
    parser.add_argument(
        "--no-replays",
        action="store_true",
        help="Do not keep replay files.",
    )
    args = parser.parse_args()

    if args.matches_per_map < 1:
        parser.error("--matches-per-map must be at least 1")

    script_dir = Path(__file__).resolve().parent
    project_root = script_dir.parent
    output_path = Path(args.output)
    if not output_path.is_absolute():
        output_path = script_dir / output_path
    csv_path = Path(f"{output_path}.csv")
    json_path = Path(f"{output_path}.json")
    csv_path.parent.mkdir(parents=True, exist_ok=True)
    maps = sorted((project_root / "maps").glob("*.map"), key=lambda path: path.name.lower())
    if not maps:
        parser.error("No .map files found in maps/")

    all_results = []
    per_map_summaries = []
    total_mybot_wins = 0
    total_altbot_wins = 0
    total_unresolved = 0

    for map_index, map_path in enumerate(maps, start=1):
        print(f"Map {map_index}/{len(maps)}: {map_path.name} ({args.matches_per_map} matches)", flush=True)
        map_results = []

        for match_number in range(1, args.matches_per_map + 1):
            if match_number % 2:
                team_a, team_b = args.mybot, args.altbot
            else:
                team_a, team_b = args.altbot, args.mybot

            result = run_match(project_root, map_path, team_a, team_b, not args.no_replays)
            result = {
                "match": match_number,
                "map": map_path.name,
                "team_a": team_a,
                "team_b": team_b,
                **result,
            }
            map_results.append(result)
            all_results.append(result)

            if result["winner"] in (args.mybot, args.altbot):
                print(f"  match {match_number}: {result['winner']} ({result['rounds']} rounds)")
            else:
                print(f"  match {match_number}: {result['winner']} - {result['error']}")

        mybot_wins = sum(result["winner"] == args.mybot for result in map_results)
        altbot_wins = sum(result["winner"] == args.altbot for result in map_results)
        unresolved = len(map_results) - mybot_wins - altbot_wins
        total_mybot_wins += mybot_wins
        total_altbot_wins += altbot_wins
        total_unresolved += unresolved

        per_map_summaries.append({
            "map": map_path.name,
            "matches": len(map_results),
            "mybot_wins": mybot_wins,
            "altbot_wins": altbot_wins,
            "other_results": unresolved,
            "win_rate": {
                args.mybot: mybot_wins / len(map_results),
                args.altbot: altbot_wins / len(map_results),
            },
        })

    summary = {
        "created_at": datetime.now().isoformat(timespec="seconds"),
        "maps_played": len(maps),
        "matches_per_map": args.matches_per_map,
        "total_matches": len(all_results),
        "overall_wins": {args.mybot: total_mybot_wins, args.altbot: total_altbot_wins},
        "overall_other_results": total_unresolved,
        "results_file": str(json_path),
    }

    payload = {
        "summary": summary,
        "maps": per_map_summaries,
        "results": all_results,
    }

    fieldnames = ["match", "map", "team_a", "team_b", "winner", "rounds", "error"]
    with csv_path.open("w", newline="", encoding="utf-8") as file:
        writer = csv.DictWriter(file, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(all_results)

    with json_path.open("w", encoding="utf-8") as file:
        json.dump(payload, file, indent=2)
        file.write("\n")

    print(f"\nOverall: {args.mybot} {total_mybot_wins} wins, {args.altbot} {total_altbot_wins} wins")
    if total_unresolved:
        print(f"Unresolved matches: {total_unresolved}")
    print(f"Saved to {csv_path} and {json_path}")


if __name__ == "__main__":
    main()
