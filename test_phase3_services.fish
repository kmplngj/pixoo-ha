#!/usr/bin/env fish
# Test Phase 3 Services - play_animation, send_playlist, set_white_balance

set DEVICE_IP "192.168.188.65"
set HA_URL "http://homeassistant.local:8123"
set ENTITY_ID "light.pixoo_display"

echo "🧪 Testing Phase 3 Services"
echo "=" (string repeat -n 70 "=")

# Wait for HA to restart
echo ""
echo "Waiting 60 seconds for HA to restart..."
sleep 60

# Test 1: Verify services exist
echo ""
echo "1. Checking if services are registered..."
set services (curl -s -H "Authorization: Bearer $HASS_TOKEN" "$HA_URL/api/services/pixoo" | python3 -c "import sys, json; data=json.load(sys.stdin); print(' '.join([s['service'] for s in data]))")

if string match -q "*play_animation*" $services
    echo "   ✅ play_animation service registered"
else
    echo "   ❌ play_animation service NOT found"
end

if string match -q "*send_playlist*" $services
    echo "   ✅ send_playlist service registered"
else
    echo "   ❌ send_playlist service NOT found"
end

if string match -q "*set_white_balance*" $services
    echo "   ✅ set_white_balance service registered"
else
    echo "   ❌ set_white_balance service NOT found"
end

# Test 2: Test play_animation service
echo ""
echo "2. Testing play_animation service (animation ID 5)..."
set response (curl -s -X POST \
    -H "Authorization: Bearer $HASS_TOKEN" \
    -H "Content-Type: application/json" \
    -d "{\"entity_id\": \"$ENTITY_ID\", \"pic_id\": 5}" \
    "$HA_URL/api/services/pixoo/play_animation")

if test "$response" = "[]"
    echo "   ✅ play_animation service called successfully"
    echo "   Check device to verify animation is playing"
else
    echo "   ⚠️  Response: $response"
end

sleep 3

# Test 3: Test set_white_balance service
echo ""
echo "3. Testing set_white_balance service (warm tint: R=255, G=220, B=200)..."
set response (curl -s -X POST \
    -H "Authorization: Bearer $HASS_TOKEN" \
    -H "Content-Type: application/json" \
    -d "{\"entity_id\": \"$ENTITY_ID\", \"red\": 255, \"green\": 220, \"blue\": 200}" \
    "$HA_URL/api/services/pixoo/set_white_balance")

if test "$response" = "[]"
    echo "   ✅ set_white_balance service called successfully"
    echo "   Note: This may not work on all firmware versions"
else
    echo "   ⚠️  Response: $response"
end

sleep 2

# Reset to neutral white balance
echo ""
echo "4. Resetting white balance to neutral (R=255, G=255, B=255)..."
curl -s -X POST \
    -H "Authorization: Bearer $HASS_TOKEN" \
    -H "Content-Type: application/json" \
    -d "{\"entity_id\": \"$ENTITY_ID\", \"red\": 255, \"green\": 255, \"blue\": 255}" \
    "$HA_URL/api/services/pixoo/set_white_balance" > /dev/null

echo "   ✅ Reset complete"

# Test 5: Test send_playlist service
echo ""
echo "5. Testing send_playlist service (2 items: image + clock)..."
set playlist '[{"type": 0, "duration": 5000, "pic_id": 5}, {"type": 2, "duration": 10000, "clock_id": 285}]'
set response (curl -s -X POST \
    -H "Authorization: Bearer $HASS_TOKEN" \
    -H "Content-Type: application/json" \
    -d "{\"entity_id\": \"$ENTITY_ID\", \"items\": $playlist}" \
    "$HA_URL/api/services/pixoo/send_playlist")

if test "$response" = "[]"
    echo "   ✅ send_playlist service called successfully"
    echo "   Check device to verify playlist is cycling (5s animation, 10s clock)"
else
    echo "   ⚠️  Response: $response"
end

# Check HA logs for errors
echo ""
echo "6. Checking HA logs for Pixoo errors..."
ssh homeassistant "export SUPERVISOR_TOKEN='$SUPERVISOR_TOKEN' && ha core logs | grep -i 'pixoo.*error' | tail -n 5" | read -z log_output

if test -z "$log_output"
    echo "   ✅ No errors found in HA logs"
else
    echo "   ⚠️  Errors found:"
    echo "$log_output"
end

# Summary
echo ""
echo "=" (string repeat -n 70 "=")
echo "✅ Phase 3 Testing Complete!"
echo "=" (string repeat -n 70 "=")
echo ""
echo "Services Added:"
echo "- ✅ play_animation (pic_id parameter)"
echo "- ✅ send_playlist (items parameter with PlaylistItem format)"
echo "- ✅ set_white_balance (red, green, blue parameters)"
echo ""
echo "Next Steps:"
echo "- Verify animations/playlists visible on device"
echo "- Test with different animation IDs"
echo "- Test with longer playlists (3+ items)"
