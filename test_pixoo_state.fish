#!/usr/bin/env fish
# Test script to verify Pixoo device state reading

# Check if IP address provided
if test (count $argv) -lt 1
    echo "Usage: ./test_pixoo_state.fish <IP_ADDRESS>"
    echo "Example: ./test_pixoo_state.fish 192.168.1.100"
    exit 1
end

set IP $argv[1]

echo "🔌 Testing Pixoo at $IP..."
echo (string repeat -n 80 '=')

# Test 1: Device Info
echo ""
echo "📱 Testing Device Information..."
echo '{"Command":"Device/GetDeviceInfo"}' | curl -s -X POST http://$IP/post \
    -H "Content-Type: application/json" --data-binary @- | python3 -m json.tool

# Test 2: Network Status
echo ""
echo "🌐 Testing Network Status..."
echo '{"Command":"Device/GetNetworkStatus"}' | curl -s -X POST http://$IP/post \
    -H "Content-Type: application/json" --data-binary @- | python3 -m json.tool

# Test 3: System Config
echo ""
echo "⚙️  Testing System Configuration..."
echo '{"Command":"Device/GetSystemConfig"}' | curl -s -X POST http://$IP/post \
    -H "Content-Type: application/json" --data-binary @- | python3 -m json.tool

# Test 4: Weather Info
echo ""
echo "🌤️  Testing Weather Information..."
echo '{"Command":"Device/GetWeatherInfo"}' | curl -s -X POST http://$IP/post \
    -H "Content-Type: application/json" --data-binary @- | python3 -m json.tool

# Test 5: Time Info  
echo ""
echo "🕐 Testing Time Information..."
echo '{"Command":"Device/GetTime"}' | curl -s -X POST http://$IP/post \
    -H "Content-Type: application/json" --data-binary @- | python3 -m json.tool

# Test 6: Animation List
echo ""
echo "🎨 Testing Animation List..."
echo '{"Command":"Draw/GetHttpGifId"}' | curl -s -X POST http://$IP/post \
    -H "Content-Type: application/json" --data-binary @- | python3 -m json.tool

echo ""
echo (string repeat -n 80 '=')
echo "✨ Test Complete!"
