# Who's That Pokemon?

Static browser game built to recreate the nostalgia of watching Pokemon and waiting for the "Who's That Pokemon?" segment that used to appear after each episode. The project is meant to bring back that familiar challenge for people who grew up with the show and still remember trying to guess the silhouette before the reveal.

## Run locally

From the project directory:

```bash
python3 -m pip install -r requirements.txt
python3 server.py
```

Then open:

```text
http://localhost:8000
```

This Flask app serves the frontend and the leaderboard API from the same origin, and reads Supabase credentials from `.env`.
If port `8000` is already in use, run with `PORT=8001 python3 server.py` instead.
Before the leaderboard works, create the Supabase table with the SQL in `supabase/leaderboard_scores.sql`.
Before generation icons work from the database, create the Supabase table with the SQL in `supabase/pokemon_generation_icons.sql`, then seed it once with:

```bash
python3 scripts/seed_generation_icons.py
```

If you already created `pokemon_generation_icons` when it only supported Gen 1-3 plus All, run `supabase/pokemon_generation_icons_expand_to_gen9.sql` first, then rerun the seed script.

## Project structure

```text
.
├── index.html
├── pokemon.html
├── server.py
├── backend/
├── requirements.txt
├── .env.example
├── supabase/
├── css/
├── js/
└── assets/
```

## Notes

- `index.html` redirects to `pokemon.html` so the project works cleanly on static hosts.
- `pokemon.html` contains the main game markup, styles, and logic.
- `server.py` is the Flask entrypoint for the static app and leaderboard API.
- `backend/` contains the Python Supabase configuration, client, and leaderboard persistence logic.
- `.env` should define `SUPABASE_URL` and `SUPABASE_SECRET_KEY` for server-side access.
- `css/styles.css` and `js/tracking.js` are present so referenced asset paths resolve correctly during deployment.
- The game fetches Pokemon data from `https://pokeapi.co/`, so internet access is required while playing.
