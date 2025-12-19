#!/usr/bin/env fish

# Comprehensive Pixoo Integration Test Script
# Tests all entities, services, and optimistic state behavior

if test -z "$SUPERVISOR_TOKEN"
    echo "ERROR: SUPERVISOR_TOKEN not set in environment"
    echo "Please set it with: set -x SUPERVISOR_TOKEN your_token"
    exit 1
end

echo "=================================================="
echo "Pixoo Integration Comprehensive Test"
echo "=================================================="
echo ""

# Helper functions
function api_get
    set entity_id $argv[1]
    ssh homeassistant "curl -s -H 'Authorization: Bearer $SUPERVISOR_TOKEN' http://supervisor/core/api/states/$entity_id" 2>/dev/null | python3 -m json.tool 2>/dev/null
end

function api_call_service
    set domain $argv[1]
    set service $argv[2]
    set data $argv[3]
    ssh homeassistant "curl -s -X POST -H 'Authorization: Bearer $SUPERVISOR_TOKEN' -H 'Content-Type: application/json' -d '$data' http://supervisor/core/api/services/$domain/$service" 2>/dev/null
end

function check_state
    set entity_id $argv[1]
    set state (api_get $entity_id | grep '"state"' | head -1 | sed 's/.*: "\([^"]*\)".*/\1/')
    echo "  $entity_id: $state"
end

# Test 1: Check all entity states
echo "=== TEST 1: Entity States ==="
echo ""
echo "Light entities:"
check_state "light.pixoo_display"

echo ""
echo "Select entities (optimistic):"
check_state "select.pixoo_channel"
check_state "select.pixoo_clock_face"
check_state "select.pixoo_visualizer"
check_state "select.pixoo_custom_page"
check_state "select.pixoo_screen_rotation"

echo ""
echo "Switch entities (optimistic):"
check_state "switch.pixoo_timer"
check_state "switch.pixoo_alarm"
check_state "switch.pixoo_stopwatch"
check_state "switch.pixoo_scoreboard"
check_state "switch.pixoo_noise_meter"
check_state "switch.pixoo_mirror_mode"

echo ""
echo "Number entities (optimistic):"
check_state "number.pixoo_timer_minutes"
check_state "number.pixoo_timer_seconds"
check_state "number.pixoo_alarm_hour"
check_state "number.pixoo_alarm_minute"
check_state "number.pixoo_scoreboard_red"
check_state "number.pixoo_scoreboard_blue"
check_state "number.pixoo_gallery_interval"

echo ""
echo "Sensor entities:"
check_state "sensor.pixoo_pixoo_ip_address"
check_state "sensor.pixoo_pixoo_active_channel"
check_state "sensor.pixoo_pixoo_brightness"

echo ""
echo "Button entities:"
check_state "button.pixoo_dismiss_notification"
check_state "button.pixoo_buzzer"

echo ""
echo "=== TEST 2: Test Channel Select (Optimistic) ==="
echo ""
echo "Setting channel to 'visualizer'..."
api_call_service "select" "select_option" '{"entity_id": "select.pixoo_channel", "option": "visualizer"}'
sleep 2
check_state "select.pixoo_channel"

echo ""
echo "Setting channel to 'faces'..."
api_call_service "select" "select_option" '{"entity_id": "select.pixoo_channel", "option": "faces"}'
sleep 2
check_state "select.pixoo_channel"

echo ""
echo "=== TEST 3: Test Timer Configuration ==="
echo ""
echo "Setting timer to 5 minutes..."
api_call_service "number" "set_value" '{"entity_id": "number.pixoo_timer_minutes", "value": 5}'
sleep 1
check_state "number.pixoo_timer_minutes"

echo ""
echo "Setting timer to 30 seconds..."
api_call_service "number" "set_value" '{"entity_id": "number.pixoo_timer_seconds", "value": 30}'
sleep 1
check_state "number.pixoo_timer_seconds"

echo ""
echo "Starting timer..."
api_call_service "switch" "turn_on" '{"entity_id": "switch.pixoo_timer"}'
sleep 2
check_state "switch.pixoo_timer"

echo ""
echo "Stopping timer..."
api_call_service "switch" "turn_off" '{"entity_id": "switch.pixoo_timer"}'
sleep 2
check_state "switch.pixoo_timer"

echo ""
echo "=== TEST 4: Test Alarm Configuration ==="
echo ""
echo "Setting alarm to 7:30..."
api_call_service "number" "set_value" '{"entity_id": "number.pixoo_alarm_hour", "value": 7}'
sleep 1
api_call_service "number" "set_value" '{"entity_id": "number.pixoo_alarm_minute", "value": 30}'
sleep 1
check_state "number.pixoo_alarm_hour"
check_state "number.pixoo_alarm_minute"

echo ""
echo "Enabling alarm..."
api_call_service "switch" "turn_on" '{"entity_id": "switch.pixoo_alarm"}'
sleep 2
check_state "switch.pixoo_alarm"

echo ""
echo "=== TEST 5: Test Brightness Control ==="
echo ""
echo "Setting brightness to 50%..."
api_call_service "light" "turn_on" '{"entity_id": "light.pixoo_display", "brightness": 128}'
sleep 2
set brightness (api_get "light.pixoo_display" | grep '"brightness"' | sed 's/.*: \([0-9]*\).*/\1/')
echo "  Current brightness: $brightness"

echo ""
echo "=== TEST 6: Test Services ==="
echo ""
echo "Testing display_text service..."
api_call_service "pixoo" "display_text" '{"entity_id": "light.pixoo_display", "text": "TEST", "x": 0, "y": 0, "color": [255, 255, 255]}'
sleep 2
echo "  Text displayed (check device)"

echo ""
echo "Testing clear_display service..."
api_call_service "pixoo" "clear_display" '{"entity_id": "light.pixoo_display"}'
sleep 2
echo "  Display cleared"

echo ""
echo "=== TEST 7: Monitor States Over Time ==="
echo ""
echo "Monitoring entity states for 30 seconds..."
for i in (seq 1 6)
    echo ""
    echo "Check $i/6 (after "(math $i \* 5)" seconds):"
    check_state "select.pixoo_channel"
    check_state "number.pixoo_timer_minutes"
    check_state "switch.pixoo_timer"
    check_state "light.pixoo_display"
    
    if test $i -lt 6
        sleep 5
    end
end

echo ""
echo "=================================================="
echo "Test Complete"
echo "=================================================="
echo ""
echo "Expected Results:"
echo "- Optimistic entities should retain values immediately"
echo "- Real entities (light, sensors) should update within 30s"
echo "- No 'unavailable' or 'unknown' states after initial load"
echo "- Services should execute without errors"
