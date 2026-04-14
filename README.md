# Who's That Pokemon?

Static browser game built to recreate the nostalgia of watching Pokemon and waiting for the "Who's That Pokemon?" segment that used to appear after each episode. The project is meant to bring back that familiar challenge for people who grew up with the show and still remember trying to guess the silhouette before the reveal.

## Run locally

From the project directory:

```bash
python3 -m http.server 8000
```

Then open:

```text
http://localhost:8000
```

You can also use any other static server, for example:

```bash
npx serve .
```

## Project structure

```text
.
├── index.html
├── pokemon.html
├── css/
├── js/
├── images/
├── whos_that_pokemon.mp3
└── pokeball_openingv3.mp3
```

## Notes

- `index.html` redirects to `pokemon.html` so the project works cleanly on static hosts.
- `pokemon.html` contains the main game markup, styles, and logic.
- `css/styles.css` and `js/tracking.js` are present so referenced asset paths resolve correctly during deployment.
- The game fetches Pokemon data from `https://pokeapi.co/`, so internet access is required while playing.
