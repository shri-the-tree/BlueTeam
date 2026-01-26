"""
Quick single-prompt tester for BlueTeam API

Usage:
    python quick_test.py "Your prompt here"
    
Example:
    python quick_test.py "Ignore all instructions"
"""

import sys
import requests
import json

BASE_URL = "http://localhost:8000"

def quick_test(prompt: str):
    """Test a single prompt quickly"""
    
    print("\n" + "🛡️ "*30)
    print("BlueTeam Quick Test")
    print("🛡️ "*30)
    print(f"\n📝 Prompt: {prompt}\n")
    
    try:
        response = requests.post(
            f"{BASE_URL}/api/v1/analyze",
            json={
                "prompt": prompt,
                "options": {"return_features": False}
            },
            timeout=5
        )
        
        if response.status_code == 200:
            result = response.json()
            
            # Visual verdict
            verdict_icons = {
                "allow": "✅ ALLOW",
                "block": "🚫 BLOCK", 
                "review": "👁️ REVIEW"
            }
            
            print(f"🎯 Verdict: {verdict_icons.get(result['verdict'], result['verdict'])}")
            print(f"📊 Score: {result['score']:.3f}")
            print(f"🏷️  Classification: {result['classification']}")
            print(f"⚡ Latency: {result['latency_ms']}ms")
            print(f"\n💬 Explanation: {result['explanation']}\n")
            
        else:
            print(f"❌ Error: {response.status_code}")
            print(f"Response: {response.text}\n")
            
    except requests.exceptions.ConnectionError:
        print("❌ ERROR: Cannot connect to server!")
        print("Make sure the server is running:")
        print("  → python api_server.py")
        print("  → OR double-click start_server.bat\n")
    except Exception as e:
        print(f"❌ ERROR: {e}\n")

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("\n❌ Error: No prompt provided!")
        print("\nUsage:")
        print('  python quick_test.py "Your prompt here"')
        print('\nExample:')
        print('  python quick_test.py "Ignore all instructions"')
        print('  python quick_test.py "What is the weather today?"\n')
        sys.exit(1)
    
    prompt = " ".join(sys.argv[1:])
    quick_test(prompt)
