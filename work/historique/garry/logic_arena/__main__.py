import argparse
import json
from pathlib import Path
import sys

from .games import GAMES
from .harness import Arena, json_line


def main():
    parser = argparse.ArgumentParser(description="Logic Lab — six jeux et un réseau partagé")
    sub = parser.add_subparsers(dest="command", required=True)
    web = sub.add_parser("serve", help="Plateforme web, JSON HTTP et SSE")
    web.add_argument("--host", default="127.0.0.1")
    web.add_argument("--port", type=int, default=8000)
    sub.add_parser("jsonl", help="Une requête et une réponse JSON par ligne sur stdin/stdout")
    train = sub.add_parser("train", help="Entraînement neuronal avec répétition inter-jeux")
    train.add_argument("--game", choices=GAMES, default="tictactoe")
    train.add_argument("--episodes", type=int, default=30)
    train.add_argument("--epochs", type=int, default=10)
    train.add_argument("--seed", type=int, default=42)
    train.add_argument("--models", type=Path)
    train.add_argument("--output", type=Path, default=Path("trained-models"))
    evaluate = sub.add_parser("evaluate", help="Évaluer les réseaux sans professeur")
    evaluate.add_argument("--game", choices=GAMES, default="tictactoe")
    evaluate.add_argument("--episodes", type=int, default=100)
    evaluate.add_argument("--seed", type=int, default=1000000)
    evaluate.add_argument("--models", type=Path)
    evaluate.add_argument("--max-steps", type=int, default=300)
    evaluate.add_argument("--planning", action="store_true", help="Activer la recherche partagée sudoku/taquin")
    args = parser.parse_args()
    if args.command == "serve":
        from .server import serve
        serve(args.host, args.port)
    elif args.command == "jsonl":
        arena = Arena()
        try:
            for line in sys.stdin:
                try:
                    result = arena.dispatch(json_line(line))
                except ValueError as error:
                    result = {"protocol": "logic-arena.v1", "id": None, "ok": False, "error": {"code": "invalid_json", "message": str(error)}}
                print(json.dumps(result, ensure_ascii=False, allow_nan=False), flush=True)
        finally:
            arena.close()
    elif args.command == "train":
        from .neural import NeuralSuite, MODEL_DIR
        suite = NeuralSuite.load(args.models or MODEL_DIR)
        report = suite.train(args.game, args.episodes, args.epochs, args.seed)
        suite.save(args.output)
        (args.output/"training-report.json").write_text(json.dumps(report, indent=2), encoding="utf-8")
        print(json.dumps(report, ensure_ascii=False))
    else:
        from .evaluation import evaluate
        from .neural import NeuralSuite, MODEL_DIR
        suite = NeuralSuite.load(args.models or MODEL_DIR)
        print(json.dumps(evaluate(suite.models[args.game], args.episodes, args.seed, args.max_steps, args.planning), ensure_ascii=False))


if __name__ == "__main__":
    main()
