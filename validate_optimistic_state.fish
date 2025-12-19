#!/usr/bin/env fish

# Pixoo Integration Validation Script
# Tests optimistic state behavior on live Home Assistant instance

set -x SUPERVISOR_TOKEN (cat /Volumes/config/.supervisor_token)

echo "=================================================="
echo "Pixoo Integration Optimistic State Validation"
echo "=================================================="

# Function to get entity state
function get_state
    set entity_id $argv[1]
    ssh homeassistant "export SUPERVISOR_TOKEN='$SUPERVISOR_TOKEN' && ha state get $entity_id" 2>/dev/null
end

# Function to call service
function call_service
    set domain $argv[1]
    set service $argv[2]
    set entity_id $argv[3]
    set extra_args $argv[4..-1]
    
    if test (count $extra_args) -gt 0
        set args_json "{\"entity_id\": \"$entity_id\", $extra_args}"
    else
        set args_json "{\"entity_id\": \"$entity_id\"}"
    end
    
    ssh homeassistant "export SUPERVISOR_TOKEN='$SUPERVISOR_TOKEN' && ha service call $domain.$service --arguments '$args_json'" 2>/dev/null
end

echo ""
echo "=== 1. List All Pixoo Entities ==="
echo ""
ssh homeassistant "export SUPERVISOR_TOKEN='$SUPERVISOR_TOKEN' && ha state list | grep 'pixoo'" | grep -v "^$"

echo ""
echo "=== 2. Test Channel Select (Optimistic) ==="
echo ""
echo "Current channel state:"
get_state "select.pixoo_divoom_pixoo_64_channel"

echo ""
echo "Changing to 'visualizer'..."
call_service "select" "select_option" "select.pixoo_divoom_pixoo_64_channel" "\"option\": \"visualizer\""

sleep 1

echo ""
echo "After change:"
get_state "select.pixoo_divoom_pixoo_64_channel"

echo ""
echo "=== 3. Test Timer Numbers (Optimistic) ==="
echo ""
echo "Timer minutes before:"
get_state "number.pixoo_divoom_pixoo_64_timer_minutes"

echo ""
echo "Setting to 5 minutes..."
call_service "number" "set_value" "number.pixoo_divoom_pixoo_64_timer_minutes" "\"value\": 5"

sleep 1

echo ""
echo "Timer minutes after:"
get_state "number.pixoo_divoom_pixoo_64_timer_minutes"

echo ""
echo "Timer seconds before:"
get_state "number.pixoo_divoom_pixoo_64_timer_seconds"

echo ""
echo "Setting to 30 seconds..."
call_service "number" "set_value" "number.pixoo_divoom_pixoo_64_timer_seconds" "\"value\": 30"

sleep 1

echo ""
echo "Timer seconds after:"
get_state "number.pixoo_divoom_pixoo_64_timer_seconds"

echo ""
echo "=== 4. Test Timer Switch (Optimistic) ==="
echo ""
echo "Timer switch before:"
get_state "switch.pixoo_divoom_pixoo_64_timer"

echo ""
echo "Turning on..."
call_service "switch" "turn_on" "switch.pixoo_divoom_pixoo_64_timer"

sleep 1

echo ""
echo "Timer switch after:"
get_state "switch.pixoo_divoom_pixoo_64_timer"

echo ""
echo "Turning off..."
call_service "switch" "turn_off" "switch.pixoo_divoom_pixoo_64_timer"

sleep 1

echo ""
echo "Timer switch after turning off:"
get_state "switch.pixoo_divoom_pixoo_64_timer"

echo ""
echo "=== 5. Test Alarm Configuration (Optimistic) ==="
echo ""
echo "Alarm hour:"
get_state "number.pixoo_divoom_pixoo_64_alarm_hour"

echo ""
echo "Setting to 7..."
call_service "number" "set_value" "number.pixoo_divoom_pixoo_64_alarm_hour" "\"value\": 7"

sleep 1

echo ""
echo "Alarm hour after:"
get_state "number.pixoo_divoom_pixoo_64_alarm_hour"

echo ""
echo "Alarm minute:"
get_state "number.pixoo_divoom_pixoo_64_alarm_minute"

echo ""
echo "Setting to 30..."
call_service "number" "set_value" "number.pixoo_divoom_pixoo_64_alarm_minute" "\"value\": 30"

sleep 1

echo ""
echo "Alarm minute after:"
get_state "number.pixoo_divoom_pixoo_64_alarm_minute"

echo ""
echo "Alarm switch:"
get_state "switch.pixoo_divoom_pixoo_64_alarm"

echo ""
echo "Enabling alarm..."
call_service "switch" "turn_on" "switch.pixoo_divoom_pixoo_64_alarm"

sleep 1

echo ""
echo "Alarm switch after:"
get_state "switch.pixoo_divoom_pixoo_64_alarm"

echo ""
echo "=== 6. Test Stopwatch Switch (Optimistic) ==="
echo ""
echo "Stopwatch before:"
get_state "switch.pixoo_divoom_pixoo_64_stopwatch"

echo ""
echo "Starting..."
call_service "switch" "turn_on" "switch.pixoo_divoom_pixoo_64_stopwatch"

sleep 1

echo ""
echo "Stopwatch after starting:"
get_state "switch.pixoo_divoom_pixoo_64_stopwatch"

echo ""
echo "=== 7. Test Scoreboard (Optimistic) ==="
echo ""
echo "Scoreboard red:"
get_state "number.pixoo_divoom_pixoo_64_scoreboard_red"

echo ""
echo "Setting to 10..."
call_service "number" "set_value" "number.pixoo_divoom_pixoo_64_scoreboard_red" "\"value\": 10"

sleep 1

echo ""
echo "Scoreboard red after:"
get_state "number.pixoo_divoom_pixoo_64_scoreboard_red"

echo ""
echo "Scoreboard blue:"
get_state "number.pixoo_divoom_pixoo_64_scoreboard_blue"

echo ""
echo "Setting to 8..."
call_service "number" "set_value" "number.pixoo_divoom_pixoo_64_scoreboard_blue" "\"value\": 8"

sleep 1

echo ""
echo "Scoreboard blue after:"
get_state "number.pixoo_divoom_pixoo_64_scoreboard_blue"

echo ""
echo "Scoreboard switch:"
get_state "switch.pixoo_divoom_pixoo_64_scoreboard"

echo ""
echo "Enabling..."
call_service "switch" "turn_on" "switch.pixoo_divoom_pixoo_64_scoreboard"

sleep 1

echo ""
echo "Scoreboard switch after:"
get_state "switch.pixoo_divoom_pixoo_64_scoreboard"

echo ""
echo "=== 8. Test Noise Meter Switch (Optimistic) ==="
echo ""
echo "Noise meter before:"
get_state "switch.pixoo_divoom_pixoo_64_noise_meter"

echo ""
echo "Enabling..."
call_service "switch" "turn_on" "switch.pixoo_divoom_pixoo_64_noise_meter"

sleep 1

echo ""
echo "Noise meter after:"
get_state "switch.pixoo_divoom_pixoo_64_noise_meter"

echo ""
echo "=== 9. Test Light Entity (Real State) ==="
echo ""
echo "Light state:"
get_state "light.pixoo_divoom_pixoo_64"

echo ""
echo "Brightness:"
get_state "light.pixoo_divoom_pixoo_64" | grep brightness

echo ""
echo "=================================================="
echo "Validation Complete"
echo "=================================================="
echo ""
echo "Expected Behavior:"
echo "- All optimistic entities should update immediately"
echo "- Values should persist after changes"
echo "- No errors should occur"
echo ""
echo "Check for 'assumed_state' attribute in select/switch entities"
echo "indicating they use optimistic state pattern."
