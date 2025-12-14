import requests
import time
import json
import sys
from datetime import datetime
import threading

HDHOMERUN_IP = "192.168.68.112"

def get_channels():
    """Get list of all channels from HDHomeRun"""
    resp = requests.get(f"http://{HDHOMERUN_IP}/lineup.json")
    return resp.json()

def start_stream(channel_number):
    """Start streaming a channel (keeps tuner locked)"""
    url = f"http://{HDHOMERUN_IP}:5004/auto/v{channel_number}"
    # Start streaming but don't read it
    resp = requests.get(url, stream=True, timeout=30)
    return resp

def get_status():
    """Get current tuner status"""
    resp = requests.get(f"http://{HDHOMERUN_IP}/status.json")
    return resp.json()

def scan_all_channels():
    """Scan all channels and record signal quality"""
    channels = get_channels()
    
    # Filter to major channels only
    major_channels = ['2.1', '4.1', '5.1', '8.1', '11.1', '13.1', '21.1', '27.1', '33.1']
    channels = [ch for ch in channels if ch['GuideNumber'] in major_channels]
    
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
            time.sleep(2)
            
            # Check status while stream is active
            status = get_status()
            
            # Close the stream
            stream_resp.close()
            
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

def main():
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