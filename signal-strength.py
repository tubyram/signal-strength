#!/usr/bin/env python3
import requests
import time
import json
import sys
from datetime import datetime

HDHOMERUN_IP = "hdhomerun.local"  # or use IP like "192.168.68.xxx"

def get_channels():
    """Get list of all channels from HDHomeRun"""
    resp = requests.get(f"http://{HDHOMERUN_IP}/lineup.json")
    return resp.json()

def tune_channel(channel_number):
    """Tune to a specific channel"""
    # Use tuner0 for scanning
    url = f"http://{HDHOMERUN_IP}:5004/auto/v{channel_number}"
    requests.get(url, timeout=2)
    time.sleep(2)  # Wait for signal to stabilize

def get_status():
    """Get current tuner status"""
    resp = requests.get(f"http://{HDHOMERUN_IP}/status.json")
    return resp.json()

def scan_all_channels():
    """Scan all channels and record signal quality"""
    channels = get_channels()
    results = []
    
    print(f"Scanning {len(channels)} channels...")
    
    for idx, channel in enumerate(channels):
        channel_num = channel['GuideNumber']
        channel_name = channel['GuideName']
        
        print(f"[{idx+1}/{len(channels)}] Tuning to {channel_num} {channel_name}...", end=' ')
        
        try:
            tune_channel(channel_num)
            status = get_status()
            
            # Find the tuner that's currently active
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
            
        time.sleep(0.5)  # Brief pause between channels
    
    return results

def main():
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    
    if len(sys.argv) > 1:
        orientation = sys.argv[1]  # e.g., "210deg"
        filename = f"antenna_scan_{orientation}_{timestamp}.json"
    else:
        filename = f"antenna_scan_{timestamp}.json"
    
    print(f"Starting channel scan at {datetime.now()}")
    print(f"Results will be saved to: {filename}\n")
    
    results = scan_all_channels()
    
    # Calculate summary stats
    avg_signal_strength = sum(r['signal_strength'] for r in results) / len(results)
    avg_signal_quality = sum(r['signal_quality'] for r in results) / len(results)
    channels_100_quality = sum(1 for r in results if r['signal_quality'] == 100)
    
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