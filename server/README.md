# Opening Tree Server

A minimal Node 22.12 + TypeScript HTTP API to serve chess opening trees from SQLite databases, mirroring the existing `serve` behavior and URL paths.

## Requirements

- Node `22.12` (use nvm or Volta)
- Yarn (as the package manager)

## Install

- `cd server`
- `yarn install`

## Configure

The server reads a JSON config file, pointed to by the `OPENING_TREE_CONFIG` environment variable.

Example config (`local-config.json`) located at the repo root:

```
{
  "host": "localhost",
  "port": 2882,
  "baseUrl": "http://localhost:2882", // optional
  "trees": [
    { "name": "twic", "file": "trees/twic.tree" },
    { "name": "iccf", "file": "trees/iccf.tree" },
    { "name": "twic-2025", "file": "trees/twic-2025.tree" }
  ]
}
```

Notes:

- `trees` is required. Each entry provides a `name` and the path to the `.tree` SQLite file.
- Paths for `file` can be relative; they are resolved against the directory of the config file.
- `host` and `port` are informational in this config; the server listens using environment variables `HOST` and `PORT` (see Run). Keep them aligned for documentation purposes.
- `baseUrl` is optional and helps when you run behind a reverse proxy or need to advertise a public URL. The API returns relative `path` entries for the tree list; clients can prefix with `baseUrl` when composing absolute links.

## Run

- Development: `OPENING_TREE_CONFIG=../local-config.json yarn dev`
- Production build:
  - `yarn build`
  - `OPENING_TREE_CONFIG=/absolute/path/to/config.json HOST=0.0.0.0 PORT=8000 yarn start`

Environment variables:

- `OPENING_TREE_CONFIG`: absolute or relative path to the JSON config
- `HOST`: bind address (defaults to `0.0.0.0`)
- `PORT`: port (defaults to `8000`)

## API

- `GET /`
  - Returns an array of trees:
  - `[{ name: string, path: "/{name}/" }]`
  - The `path` is relative; prefix it with your `baseUrl` when building absolute URLs.

- `GET /{treeName}/{encodedFEN}`
  - `encodedFEN` is a URL-encoded FEN string
  - Returns `{ fen, moves }` with aggregated stats or `404` if not found

## Behavior

- Databases are opened in read-only mode; the server never writes.
- When possible, databases are opened via SQLite URI with `mode=ro` and `immutable=1` (fallback to read-only file open if the URI form isn’t supported by the local SQLite).
- FEN normalization and en-passant handling match the Python logic to ensure identical query behavior.

## Scripts

- `yarn dev` — start the server in development
- `yarn test` — run unit tests (placed next to modules in `src`)
- `yarn typecheck` — TypeScript type checking
- `yarn lint` — lint and auto-fix using Biome
- `yarn build` — compile TypeScript to `dist`

## Examples

Start locally with the provided config:

```
cd server
OPENING_TREE_CONFIG=../local-config.json yarn dev
```

Open the API root:

```
http://localhost:8000/
```

Query a position:

```
http://localhost:8000/twic/rnbqkbnr%2Fppp2ppp%2F4p3%2F3pP3%2F8%2F8%2FPPPP1PPP%2FRNBQKBNR%20w%20KQkq%20d6
```
