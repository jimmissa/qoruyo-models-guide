# Installation and model retrieval

## Requirements

- Python 3 supported by the current Kraken release
- a shell or terminal
- page images in a format supported by Kraken

Kraken's official installation instructions should take precedence when its
requirements change: <https://kraken.re/main/getting_started.html>.

## Isolated installation

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip kraken
kraken --version
```

On Windows PowerShell, activate with:

```powershell
.venv\Scripts\Activate.ps1
```

## Discovering models

Kraken's model repository is backed by Zenodo:

```bash
kraken list
kraken show 10.5281/zenodo.17406626
```

Depending on the Kraken release, repository listing filters and presentation
may differ. The DOI remains the stable identifier.

## Downloading models

Download a model by DOI:

```bash
kraken get 10.5281/zenodo.17406626
```

Kraken prints the managed model directory and downloaded filename. Models in
that directory can normally be selected by filename. If a local Kraken setup
does not resolve the filename automatically, pass the displayed full path to
`segment -i` or `ocr -m`.

Download every model documented by this project:

```bash
bash scripts/download-all-models.sh
```

## Confirming metadata

Before a large run, inspect the exact record:

```bash
kraken show 10.5281/zenodo.17406773
```

The Zenodo page remains authoritative for creators, description, files,
license, and DOI:

```text
https://zenodo.org/records/17406773
```

## Suggested working layout

```text
ocr-project/
  images/
    page_001.png
  output/
  scripts/
```

The model files do not need to be copied into the project if Kraken can resolve
them from its managed model directory.
