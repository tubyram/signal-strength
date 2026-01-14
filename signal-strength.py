# /// script
# dependencies = ["requests"]
# ///
import requests
import time
import json
import sys
from datetime import datetime

HDHOMERUN_IP = "hdhomerun.local"
MAJOR_CHANNELS = ['4.1', '5.1', '8.8', '11.1', '13.1', '21.1', '27.1', '33.1']
CHANNEL_NAMES = {
    '4.1': 'FOX',
    '5.1': 'NBC',
    '8.8': 'ABC',
    '11.1': 'CBS',
    '13.1': 'PBS',
    '21.1': 'KTXA',
    '27.1': 'MNT',
    '33.1': 'CW',
}

def get_channels():
    """Get list of all channels from HDHomeRun"""
    resp = requests.get(f"http://{HDHOMERUN_IP}/lineup.json")
    return resp.json()

def tune_and_get_status(channel_number):
    """Tune to channel and get status, properly releasing the tuner."""
    url = f"http://{HDHOMERUN_IP}:5004/auto/v{channel_number}"

    # Start streaming
    stream = requests.get(url, stream=True, timeout=5)

    # Wait for tuner to lock
    time.sleep(0.5)

    # Get status while stream is active
    status = requests.get(f"http://{HDHOMERUN_IP}/status.json").json()

    # Read some data to establish the stream, then close properly
    try:
        stream.raw.read(1000)
    except:
        pass

    stream.close()
    del stream

    return status

def find_tuner_for_channel(status, channel_num):
    """Find tuner data for a specific channel in status response"""
    for tuner in status:
        if tuner.get('VctNumber') == channel_num:
            return tuner
    return None

def scan_channel(channel_num, channel_name, debug=False):
    """Scan a single channel and return result dict or None if failed"""
    status = tune_and_get_status(channel_num)
    if debug:
        print(f"\nDEBUG: Looking for channel {channel_num}")
        print(f"DEBUG: Status response: {status}")
    tuner = find_tuner_for_channel(status, channel_num)
    if tuner:
        return {
            'channel': channel_num,
            'name': channel_name,
            'signal_strength': tuner.get('SignalStrengthPercent', 0),
            'signal_quality': tuner.get('SignalQualityPercent', 0),
            'symbol_quality': tuner.get('SymbolQualityPercent', 0)
        }
    return None

def scan_all_channels(quiet=False):
    """Scan all major channels and return results"""
    channels = get_channels()
    channels = [ch for ch in channels if ch['GuideNumber'] in MAJOR_CHANNELS]

    results = []
    failed_channels = []

    if not quiet:
        print(f"Scanning {len(channels)} channels...")

    for idx, channel in enumerate(channels):
        channel_num = channel['GuideNumber']
        channel_name = channel['GuideName']

        if not quiet:
            print(f"[{idx+1}/{len(channels)}] Tuning to {channel_num:>5} {channel_name:<10}...", end=' ', flush=True)

        try:
            result = scan_channel(channel_num, channel_name)
            if result:
                results.append(result)
                if not quiet:
                    print(f"SS:{result['signal_strength']}% SQ:{result['signal_quality']}% SYM:{result['symbol_quality']}%")
            else:
                failed_channels.append(channel_num)
                if not quiet:
                    print("FAILED")
        except Exception as e:
            failed_channels.append(channel_num)
            if not quiet:
                print(f"ERROR: {e}")

    return results, failed_channels

def monitor_continuously():
    """Continuously monitor channel signal quality"""
    print("Starting continuous monitoring mode...")
    print("Press Ctrl+C to stop\n")
    time.sleep(2)

    try:
        while True:
            results, failed_channels = scan_all_channels(quiet=True)

            print(f"\n[{datetime.now().strftime('%H:%M:%S')}]", end=" ")

            channel_strs = [f"{CHANNEL_NAMES.get(r['channel'], r['channel'])}:{r['signal_quality']}%" for r in results]
            channel_strs += [f"{CHANNEL_NAMES.get(ch, ch)}:FAIL" for ch in failed_channels]
            print(" | ".join(channel_strs), end="")

            if failed_channels:
                print(" | Minimum:FAILED")
            elif results:
                min_sq = min(r['signal_quality'] for r in results)
                print(f" | Minimum:{min_sq}%")
            else:
                print()

            time.sleep(0.5)
    except KeyboardInterrupt:
        print("\n\nMonitoring stopped.")
        sys.exit(0)

def main():
    if len(sys.argv) > 1 and sys.argv[1] in ['-w', '--watch']:
        monitor_continuously()
        return

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

    if len(sys.argv) > 1:
        orientation = sys.argv[1]
        filename = f"antenna_scan_{orientation}_{timestamp}.json"
    else:
        filename = f"antenna_scan_{timestamp}.json"

    print(f"Starting channel scan at {datetime.now()}")
    print(f"Results will be saved to: {filename}\n")

    results, _ = scan_all_channels()

    if results:
        avg_ss = sum(r['signal_strength'] for r in results) / len(results)
        avg_sq = sum(r['signal_quality'] for r in results) / len(results)
        perfect_channels = sum(1 for r in results if r['signal_quality'] == 100)
    else:
        avg_ss = avg_sq = perfect_channels = 0

    output = {
        'timestamp': timestamp,
        'summary': {
            'total_channels': len(results),
            'avg_signal_strength': round(avg_ss, 1),
            'avg_signal_quality': round(avg_sq, 1),
            'channels_with_100_quality': perfect_channels
        },
        'channels': results
    }

    with open(filename, 'w') as f:
        json.dump(output, f, indent=2)

    print(f"\n=== SUMMARY ===")
    print(f"Total channels: {len(results)}")
    print(f"Avg signal strength: {avg_ss:.1f}%")
    print(f"Avg signal quality: {avg_sq:.1f}%")
    print(f"Channels with 100% quality: {perfect_channels}/{len(results)}")
    print(f"\nResults saved to: {filename}")

if __name__ == "__main__":
    main()
