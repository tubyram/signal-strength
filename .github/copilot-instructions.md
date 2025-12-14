# Copilot Instructions for signal-strength

## Project Overview

A single-file Python CLI tool for scanning HDHomeRun TV tuner signal quality across broadcast channels. Used to optimize antenna positioning by comparing signal metrics at different orientations.

## Architecture

- **Single script**: `signal-strength.py` - no package structure, runs directly with `uv`
- **HDHomeRun API integration**: Communicates with local HDHomeRun device via mDNS hostname (`hdhomerun.local`)
- **Workflow**: Tunes each channel → waits for lock → reads signal metrics → saves JSON report

## Running the Tool

```bash
# Run with uv (no venv needed)
uv run --with requests ./signal-strength.py [orientation]

# Examples:
uv run --with requests ./signal-strength.py 0deg
uv run --with requests ./signal-strength.py 45deg
```

The optional `orientation` argument labels the output file for A/B testing antenna positions.

## Key Patterns

### HDHomeRun API Endpoints
- `http://{IP}/lineup.json` - Channel list
- `http://{IP}/status.json` - Current tuner status (signal metrics)
- `http://{IP}:5004/auto/v{channel}` - Stream endpoint (port 5004, `v` prefix for virtual channel)

### Signal Metrics
Three quality indicators returned per channel:
- `SignalStrengthPercent` - Raw signal power
- `SignalQualityPercent` - Signal-to-noise ratio
- `SymbolQualityPercent` - Digital decoding quality

### Output Format
JSON files named `antenna_scan_{orientation}_{timestamp}.json` with per-channel metrics and summary stats.

## Conventions

- **No dependencies file**: Uses `uv run --with` for ad-hoc dependency injection
- **mDNS discovery**: Uses `hdhomerun.local` hostname for automatic device discovery
- **Major channels filter**: Only scans specific channels (2.1, 4.1, 5.1, etc.) - modify `major_channels` list to change
