from .games import make_game


def evaluate(model, episodes=100, seed=1000000, max_steps=300, planning=False):
    if type(episodes) is not int or not 1 <= episodes <= 10000 or type(max_steps) is not int or not 1 <= max_steps <= 10000:
        raise ValueError("episodes et max_steps doivent être entre 1 et 10000")
    stats = {"game": model.game, "episodes": episodes, "wins": 0, "losses": 0, "draws": 0,
             "truncated": 0, "mean_score": 0., "opponent": "random_legal", "seed": seed,
             "level": 10, "style": "balanced", "teacher_used": False, "planning": planning}
    for i in range(episodes):
        env = make_game(model.game, seed+i)
        player = 1+i%2 if env.players == 2 else 1
        for _ in range(max_steps):
            legal = env.legal_actions()
            action = model.choose(env.observation(), legal) if env.current_player == player else env.rng.choice(legal)
            if planning and env.current_player == player:
                from .planner import plan
                action,_ = plan(env.observation(),legal,model,10,action)
            env.step(action)
            if env.done:
                break
        if not env.done:
            stats["truncated"] += 1
        elif env.winner == player:
            stats["wins"] += 1
        elif env.players == 2 and env.winner == 0:
            stats["draws"] += 1
        else:
            stats["losses"] += 1
        stats["mean_score"] += env.score/episodes
    return stats
