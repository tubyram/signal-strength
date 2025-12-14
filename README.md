# signal-strength

A single-file Python CLI tool for scanning HDHomeRun TV tuner signal quality across broadcast channels. Used to optimize antenna positioning by comparing signal metrics at different orientations.

## Usage

```bash
# Run with uv (no venv needed)
uv run --with requests ./signal-strength.py [orientation]

# Examples:
uv run --with requests ./signal-strength.py 0deg
uv run --with requests ./signal-strength.py 45deg
```

The optional `orientation` argument labels the output file for A/B testing antenna positions.

## Output

JSON files named `antenna_scan_{orientation}_{timestamp}.json` with per-channel metrics and summary stats.

### Signal Metrics
- `SignalStrengthPercent` - Raw signal power
- `SignalQualityPercent` - Signal-to-noise ratio  
- `SymbolQualityPercent` - Digital decoding quality

## HDHomeRun API

Uses mDNS hostname `hdhomerun.local` for automatic device discovery.

| Endpoint | Purpose |
|----------|---------|
| `http://{host}/lineup.json` | Channel list |
| `http://{host}/status.json` | Tuner status (signal metrics) |
| `http://{host}:5004/auto/v{channel}` | Stream endpoint (port 5004, `v` prefix) |

## Configuration

- **Channel filter**: Edit `major_channels` list in script to change which channels are scanned
- **Dependencies**: Only `requests` - injected via `uv run --with`
