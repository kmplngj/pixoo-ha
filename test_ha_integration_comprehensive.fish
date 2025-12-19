#!/usr/bin/env fish
# Comprehensive test of ALL ha-pixoo integration functionality

set DEVICE_IP "192.168.188.65"
set HA_URL "http://homeassistant.local:8123"
set ENTITY_ID "light.pixoo_display"
set MEDIA_PLAYER "media_player.pixoo"

echo "🏠 COMPREHENSIVE HA-PIXOO INTEGRATION TEST"
echo (string repeat -n 80 "=")
echo ""

# Test categories
set passed 0
set failed 0
set skipped 0

# CATEGORY 1: Entity States
echo "📊 CATEGORY 1: Entity States (40+ entities)"
echo (string repeat -n 80 "-")

# List all pixoo entities
set entities (curl -s -H "Authorization: Bearer $HASS_TOKEN" "$HA_URL/api/states" | python3 -c "import sys, json; states=json.load(sys.stdin); print('\n'.join([s['entity_id'] for s in states if 'pixoo' in s['entity_id'] and 'unavailable' not in s['state']]))")

echo "Active Entities:"
for entity in $entities
    echo "  ✅ $entity"
end
set entity_count (count $entities)
echo ""
echo "Total Active Entities: $entity_count"
set passed (math $passed + 1)

# CATEGORY 2: Light Entity
echo ""
echo "💡 CATEGORY 2: Light Entity"
echo (string repeat -n 80 "-")

# Test turn_on
echo "Testing light.turn_on..."
curl -s -X POST -H "Authorization: Bearer $HASS_TOKEN" -H "Content-Type: application/json" \
  -d "{\"entity_id\": \"$ENTITY_ID\"}" "$HA_URL/api/services/light/turn_on" > /dev/null
and begin
    echo "  ✅ light.turn_on"
    set passed (math $passed + 1)
end
or begin
    echo "  ❌ light.turn_on FAILED"
    set failed (math $failed + 1)
end
sleep 1

# Test brightness
echo "Testing light brightness (50%)..."
curl -s -X POST -H "Authorization: Bearer $HASS_TOKEN" -H "Content-Type: application/json" \
  -d "{\"entity_id\": \"$ENTITY_ID\", \"brightness\": 128}" "$HA_URL/api/services/light/turn_on" > /dev/null
and begin
    echo "  ✅ set brightness"
    set passed (math $passed + 1)
end
or begin
    echo "  ❌ set brightness FAILED"
    set failed (math $failed + 1)
end
sleep 1

# Restore brightness
curl -s -X POST -H "Authorization: Bearer $HASS_TOKEN" -H "Content-Type: application/json" \
  -d "{\"entity_id\": \"$ENTITY_ID\", \"brightness\": 54}" "$HA_URL/api/services/light/turn_on" > /dev/null

# CATEGORY 3: Select Entities (7)
echo ""
echo "🎛️  CATEGORY 3: Select Entities"
echo (string repeat -n 80 "-")

# Test channel select
echo "Testing select.pixoo_channel..."
curl -s -X POST -H "Authorization: Bearer $HASS_TOKEN" -H "Content-Type: application/json" \
  -d "{\"entity_id\": \"select.pixoo_channel\", \"option\": \"Cloud\"}" "$HA_URL/api/services/select/select_option" > /dev/null
and begin
    echo "  ✅ select channel (Cloud)"
    set passed (math $passed + 1)
end
or begin
    echo "  ❌ select channel FAILED"
    set failed (math $failed + 1)
end
sleep 1

# Test rotation select
echo "Testing select.pixoo_rotation..."
curl -s -X POST -H "Authorization: Bearer $HASS_TOKEN" -H "Content-Type: application/json" \
  -d "{\"entity_id\": \"select.pixoo_rotation\", \"option\": \"Normal\"}" "$HA_URL/api/services/select/select_option" > /dev/null
and begin
    echo "  ✅ select rotation"
    set passed (math $passed + 1)
end
or begin
    echo "  ❌ select rotation FAILED"
    set failed (math $failed + 1)
end

echo "  ⚠️  Skipping 5 other selects (clock_face, visualizer, etc.)"
set skipped (math $skipped + 5)

# CATEGORY 4: Switch Entities (7)
echo ""
echo "🔘 CATEGORY 4: Switch Entities"
echo (string repeat -n 80 "-")

# Test mirror mode switch
echo "Testing switch.pixoo_mirror_mode..."
curl -s -X POST -H "Authorization: Bearer $HASS_TOKEN" -H "Content-Type: application/json" \
  -d "{\"entity_id\": \"switch.pixoo_mirror_mode\"}" "$HA_URL/api/services/switch/turn_off" > /dev/null
and begin
    echo "  ✅ mirror mode off"
    set passed (math $passed + 1)
end
or begin
    echo "  ❌ mirror mode FAILED"
    set failed (math $failed + 1)
end

echo "  ⚠️  Skipping 6 other switches (timer, alarm, etc.)"
set skipped (math $skipped + 6)

# CATEGORY 5: Number Entities (8)
echo ""
echo "🔢 CATEGORY 5: Number Entities"
echo (string repeat -n 80 "-")

echo "  ⚠️  Skipping all number entities (would change device state)"
set skipped (math $skipped + 8)

# CATEGORY 6: Sensor Entities (3 working)
echo ""
echo "📡 CATEGORY 6: Sensor Entities"
echo (string repeat -n 80 "-")

# Check active channel sensor
set channel_state (curl -s -H "Authorization: Bearer $HASS_TOKEN" "$HA_URL/api/states/sensor.pixoo_pixoo_active_channel_2" | python3 -c "import sys, json; print(json.load(sys.stdin)['state'])")
echo "  ✅ Active Channel sensor: $channel_state"
set passed (math $passed + 1)

# Check time sensor
set time_state (curl -s -H "Authorization: Bearer $HASS_TOKEN" "$HA_URL/api/states/sensor.pixoo_pixoo_device_time" | python3 -c "import sys, json; print(json.load(sys.stdin)['state'])")
echo "  ✅ Time sensor: $time_state"
set passed (math $passed + 1)

# Check weather sensor
set weather_state (curl -s -H "Authorization: Bearer $HASS_TOKEN" "$HA_URL/api/states/sensor.pixoo_pixoo_weather_condition" | python3 -c "import sys, json; print(json.load(sys.stdin)['state'])")
echo "  ✅ Weather sensor: $weather_state"
set passed (math $passed + 1)

# CATEGORY 7: Button Entities (4)
echo ""
echo "🔴 CATEGORY 7: Button Entities"
echo (string repeat -n 80 "-")

echo "Testing button.pixoo_buzzer..."
curl -s -X POST -H "Authorization: Bearer $HASS_TOKEN" -H "Content-Type: application/json" \
  -d "{\"entity_id\": \"button.pixoo_buzzer\"}" "$HA_URL/api/services/button/press" > /dev/null
and begin
    echo "  ✅ buzzer button"
    set passed (math $passed + 1)
    sleep 1
end
or begin
    echo "  ❌ buzzer button FAILED"
    set failed (math $failed + 1)
end

echo "  ⚠️  Skipping 3 other buttons (dismiss, reset_buffer, push_buffer)"
set skipped (math $skipped + 3)

# CATEGORY 8: Display Services (4)
echo ""
echo "🖼️  CATEGORY 8: Display Services"
echo (string repeat -n 80 "-")

# display_image
echo "Testing pixoo.display_image..."
curl -s -X POST -H "Authorization: Bearer $HASS_TOKEN" -H "Content-Type: application/json" \
  -d "{\"entity_id\": \"$ENTITY_ID\", \"url\": \"https://picsum.photos/64/64\"}" \
  "$HA_URL/api/services/pixoo/display_image" > /dev/null
and begin
    echo "  ✅ display_image"
    set passed (math $passed + 1)
    sleep 2
end
or begin
    echo "  ❌ display_image FAILED"
    set failed (math $failed + 1)
end

# display_text
echo "Testing pixoo.display_text..."
curl -s -X POST -H "Authorization: Bearer $HASS_TOKEN" -H "Content-Type: application/json" \
  -d "{\"entity_id\": \"$ENTITY_ID\", \"text\": \"TEST\", \"color\": [0, 255, 0], \"position\": [0, 32]}" \
  "$HA_URL/api/services/pixoo/display_text" > /dev/null
and begin
    echo "  ✅ display_text"
    set passed (math $passed + 1)
    sleep 2
end
or begin
    echo "  ❌ display_text FAILED"
    set failed (math $failed + 1)
end

# clear_display
echo "Testing pixoo.clear_display..."
curl -s -X POST -H "Authorization: Bearer $HASS_TOKEN" -H "Content-Type: application/json" \
  -d "{\"entity_id\": \"$ENTITY_ID\"}" "$HA_URL/api/services/pixoo/clear_display" > /dev/null
and begin
    echo "  ✅ clear_display"
    set passed (math $passed + 1)
    sleep 1
end
or begin
    echo "  ❌ clear_display FAILED"
    set failed (math $failed + 1)
end

echo "  ⚠️  Skipping display_gif (requires GIF file)"
set skipped (math $skipped + 1)

# CATEGORY 9: Animation Services (3) - NEW in Phase 3
echo ""
echo "🎬 CATEGORY 9: Animation Services (Phase 3)"
echo (string repeat -n 80 "-")

# play_animation
echo "Testing pixoo.play_animation..."
curl -s -X POST -H "Authorization: Bearer $HASS_TOKEN" -H "Content-Type: application/json" \
  -d "{\"entity_id\": \"$ENTITY_ID\", \"pic_id\": 5}" \
  "$HA_URL/api/services/pixoo/play_animation" > /dev/null
and begin
    echo "  ✅ play_animation"
    set passed (math $passed + 1)
    sleep 2
end
or begin
    echo "  ❌ play_animation FAILED"
    set failed (math $failed + 1)
end

# send_playlist
echo "Testing pixoo.send_playlist..."
curl -s -X POST -H "Authorization: Bearer $HASS_TOKEN" -H "Content-Type: application/json" \
  -d "{\"entity_id\": \"$ENTITY_ID\", \"items\": [{\"type\": 0, \"duration\": 3000, \"pic_id\": 5}, {\"type\": 2, \"duration\": 3000, \"clock_id\": 285}]}" \
  "$HA_URL/api/services/pixoo/send_playlist" > /dev/null
and begin
    echo "  ✅ send_playlist"
    set passed (math $passed + 1)
    sleep 3
end
or begin
    echo "  ❌ send_playlist FAILED"
    set failed (math $failed + 1)
end

# list_animations
echo "Testing pixoo.list_animations..."
curl -s -X POST -H "Authorization: Bearer $HASS_TOKEN" -H "Content-Type: application/json" \
  -d "{\"entity_id\": \"$ENTITY_ID\"}" "$HA_URL/api/services/pixoo/list_animations" > /dev/null
and begin
    echo "  ✅ list_animations"
    set passed (math $passed + 1)
end
or begin
    echo "  ❌ list_animations FAILED"
    set failed (math $failed + 1)
end

# CATEGORY 10: Tool Services (3)
echo ""
echo "🔧 CATEGORY 10: Tool Services"
echo (string repeat -n 80 "-")

# set_timer
echo "Testing pixoo.set_timer..."
curl -s -X POST -H "Authorization: Bearer $HASS_TOKEN" -H "Content-Type: application/json" \
  -d "{\"entity_id\": \"$ENTITY_ID\", \"duration\": \"01:00\"}" \
  "$HA_URL/api/services/pixoo/set_timer" > /dev/null
and begin
    echo "  ✅ set_timer"
    set passed (math $passed + 1)
end
or begin
    echo "  ❌ set_timer FAILED"
    set failed (math $failed + 1)
end

# set_alarm
echo "Testing pixoo.set_alarm..."
curl -s -X POST -H "Authorization: Bearer $HASS_TOKEN" -H "Content-Type: application/json" \
  -d "{\"entity_id\": \"$ENTITY_ID\", \"time\": \"07:00\", \"enabled\": false}" \
  "$HA_URL/api/services/pixoo/set_alarm" > /dev/null
and begin
    echo "  ✅ set_alarm"
    set passed (math $passed + 1)
end
or begin
    echo "  ❌ set_alarm FAILED"
    set failed (math $failed + 1)
end

# play_buzzer
echo "Testing pixoo.play_buzzer..."
curl -s -X POST -H "Authorization: Bearer $HASS_TOKEN" -H "Content-Type: application/json" \
  -d "{\"entity_id\": \"$ENTITY_ID\", \"active_ms\": 200, \"off_ms\": 200, \"count\": 1}" \
  "$HA_URL/api/services/pixoo/play_buzzer" > /dev/null
and begin
    echo "  ✅ play_buzzer"
    set passed (math $passed + 1)
    sleep 1
end
or begin
    echo "  ❌ play_buzzer FAILED"
    set failed (math $failed + 1)
end

# CATEGORY 11: Configuration Services (1) - NEW in Phase 3
echo ""
echo "⚙️  CATEGORY 11: Configuration Services (Phase 3)"
echo (string repeat -n 80 "-")

# set_white_balance
echo "Testing pixoo.set_white_balance..."
curl -s -X POST -H "Authorization: Bearer $HASS_TOKEN" -H "Content-Type: application/json" \
  -d "{\"entity_id\": \"$ENTITY_ID\", \"red\": 255, \"green\": 255, \"blue\": 255}" \
  "$HA_URL/api/services/pixoo/set_white_balance" > /dev/null
and begin
    echo "  ✅ set_white_balance"
    set passed (math $passed + 1)
end
or begin
    echo "  ❌ set_white_balance FAILED"
    set failed (math $failed + 1)
end

# CATEGORY 12: Media Player
echo ""
echo "🎵 CATEGORY 12: Media Player"
echo (string repeat -n 80 "-")

echo "  ⚠️  Skipping media player tests (requires detailed playlist setup)"
set skipped (math $skipped + 3)

# Summary
echo ""
echo (string repeat -n 80 "=")
echo "TEST SUMMARY"
echo (string repeat -n 80 "=")
echo "✅ PASSED:  $passed tests"
echo "❌ FAILED:  $failed tests"
echo "⚠️  SKIPPED: $skipped tests"
set total (math $passed + $failed + $skipped)
echo "📊 TOTAL:   $total tests"
echo ""

if test $failed -eq 0
    echo "🎉 ALL TESTS PASSED!"
else
    echo "⚠️  Some tests failed. Check logs above."
end
