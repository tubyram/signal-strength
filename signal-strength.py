# /// script
# dependencies = [
#   "requests>=2.31.0",
# ]
# ///
import requests
import time
import json
import sys
import os
from datetime import datetime

HDHOMERUN_IP = "hdhomerun.local"

# Filter to major channels only
MAJOR_CHANNELS = ['4.1', '5.1', '8.8', '11.1', '13.1', '21.1', '27.1', '33.1']

def get_channels():
    """Get list of all channels from HDHomeRun"""
    resp = requests.get(f"http://{HDHOMERUN_IP}/lineup.json")
    return resp.json()

def start_stream(channel_number):
    """Start streaming a channel to tune the tuner"""
    url = f"http://{HDHOMERUN_IP}:5004/auto/v{channel_number}"
    resp = requests.get(url, stream=True, timeout=30)
    return resp

def get_status():
    """Get current tuner status"""
    resp = requests.get(f"http://{HDHOMERUN_IP}/status.json")
    return resp.json()

def scan_all_channels():
    """Scan all channels and record signal quality"""
    channels = get_channels()

    channels = [ch for ch in channels if ch['GuideNumber'] in MAJOR_CHANNELS]
    
    results = []
    
    print(f"Scanning {len(channels)} channels...")
    
    for idx, channel in enumerate(channels):
        channel_num = channel['GuideNumber']
        channel_name = channel['GuideName']
        
        print(f"[{idx+1}/{len(channels)}] Tuning to {channel_num:>5} {channel_name:<10}...", end=' ', flush=True)
        
        try:
            # Start the stream (this tunes the tuner)
            stream_resp = start_stream(channel_num)

            # Wait a moment for tuner to lock
            time.sleep(1)

            # Check status while stream is active
            status = get_status()

            # Read a tiny bit of data to establish the stream, then close
            try:
                stream_resp.raw.read(100)
            except:
                pass

            # Close the stream - this should release the tuner
            stream_resp.close()
            del stream_resp

            # Find the active tuner
            for tuner in status:
                if tuner.get('VctNumber') == channel_num:
                    result = {
                        'channel': channel_num,
                        'name': channel_name,
                        'signal_strength': tuner.get('SignalStrengthPercent', 0),
                        'signal_quality': tuner.get('SignalQualityPercent', 0),
                        'symbol_quality': tuner.get('SymbolQualityPercent', 0)
                    }
                    results.append(result)
                    print(f"SS:{result['signal_strength']}% SQ:{result['signal_quality']}% SYM:{result['symbol_quality']}%")
                    break
            else:
                print("FAILED")

        except Exception as e:
            print(f"ERROR: {e}")

    return results

def scan_all_channels_quiet():
    """Scan all channels without printing progress - for continuous monitoring"""
    channels = get_channels()

    channels = [ch for ch in channels if ch['GuideNumber'] in MAJOR_CHANNELS]

    results = []
    failed_channels = []

    for channel in channels:
        channel_num = channel['GuideNumber']
        channel_name = channel['GuideName']

        try:
            # Start the stream (this tunes the tuner)
            stream_resp = start_stream(channel_num)

            # Wait a moment for tuner to lock
            time.sleep(1)

            # Check status while stream is active
            status = get_status()

            # Read a tiny bit of data to establish the stream, then close
            try:
                stream_resp.raw.read(100)
            except:
                pass

            # Close the stream - this should release the tuner
            stream_resp.close()
            del stream_resp

            # Find the active tuner
            found = False
            for tuner in status:
                if tuner.get('VctNumber') == channel_num:
                    result = {
                        'channel': channel_num,
                        'name': channel_name,
                        'signal_strength': tuner.get('SignalStrengthPercent', 0),
                        'signal_quality': tuner.get('SignalQualityPercent', 0),
                        'symbol_quality': tuner.get('SymbolQualityPercent', 0)
                    }
                    results.append(result)
                    found = True
                    break

            if not found:
                failed_channels.append(channel_num)

        except Exception as e:
            failed_channels.append(channel_num)

    return results, failed_channels

def monitor_continuously():
    """Continuously monitor channel signal quality"""
    print("Starting continuous monitoring mode...")
    print("Press Ctrl+C to stop\n")
    time.sleep(2)

    try:
        while True:
            # Get current results
            results, failed_channels = scan_all_channels_quiet()

            # Display timestamp and results
            print(f"\n[{datetime.now().strftime('%H:%M:%S')}]", end=" ")

            # Display each channel on one line
            channel_strs = []
            for r in results:
                channel_strs.append(f"{r['channel']}:{r['signal_quality']}%")

            # Add failed channels
            for ch in failed_channels:
                channel_strs.append(f"{ch}:FAIL")

            print(" | ".join(channel_strs), end="")

            # Calculate and display minimum
            if len(failed_channels) > 0:
                print(f" | MIN:FAILED")
            elif len(results) > 0:
                min_signal_quality = min(r['signal_quality'] for r in results)
                print(f" | MIN:{min_signal_quality}%")
            else:
                print()

            # Wait a bit before next scan
            time.sleep(2)

    except KeyboardInterrupt:
        print("\n\nMonitoring stopped.")
        sys.exit(0)

def main():
    # Check for watch mode
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

    results = scan_all_channels()
    
    # Calculate summary stats
    if len(results) > 0:
        avg_signal_strength = sum(r['signal_strength'] for r in results) / len(results)
        avg_signal_quality = sum(r['signal_quality'] for r in results) / len(results)
        channels_100_quality = sum(1 for r in results if r['signal_quality'] == 100)
    else:
        avg_signal_strength = 0
        avg_signal_quality = 0
        channels_100_quality = 0
    
    output = {
        'timestamp': timestamp,
        'summary': {
            'total_channels': len(results),
            'avg_signal_strength': round(avg_signal_strength, 1),
            'avg_signal_quality': round(avg_signal_quality, 1),
            'channels_with_100_quality': channels_100_quality
        },
        'channels': results
    }
    
    with open(filename, 'w') as f:
        json.dump(output, f, indent=2)
    
    print(f"\n=== SUMMARY ===")
    print(f"Total channels: {len(results)}")
    print(f"Avg signal strength: {avg_signal_strength:.1f}%")
    print(f"Avg signal quality: {avg_signal_quality:.1f}%")
    print(f"Channels with 100% quality: {channels_100_quality}/{len(results)}")
    print(f"\nResults saved to: {filename}")

if __name__ == "__main__":
    main()