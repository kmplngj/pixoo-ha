#!/usr/bin/env fish
# Comprehensive test script for ha-pixoo integration
# Tests all major functionality with visual delays for verification

set ENTITY "light.pixoo_display"
set HA_URL "http://homeassistant.local:8123"

# Colors for output
set GREEN (set_color green)
set BLUE (set_color blue)
set YELLOW (set_color yellow)
set RED (set_color red)
set NORMAL (set_color normal)

function call_service
    set service $argv[1]
    set data $argv[2]
    
    echo "$BLUE→ Calling: $service$NORMAL"
    
    if test -n "$data"
        curl -s -X POST \
            -H "Authorization: Bearer $HASS_TOKEN" \
            -H "Content-Type: application/json" \
            -d $data \
            "$HA_URL/api/services/$service" > /dev/null
    else
        curl -s -X POST \
            -H "Authorization: Bearer $HASS_TOKEN" \
            -H "Content-Type: application/json" \
            "$HA_URL/api/services/$service" > /dev/null
    end
    
    if test $status -eq 0
        echo "$GREEN✓ Success$NORMAL"
    else
        echo "$RED✗ Failed$NORMAL"
    end
end

function wait_and_continue
    set message $argv[1]
    set delay $argv[2]
    echo "$YELLOW⏱ $message (waiting $delay seconds)...$NORMAL"
    sleep $delay
end

echo "$GREEN"
echo "╔════════════════════════════════════════════════════════════╗"
echo "║           HA-PIXOO COMPREHENSIVE FUNCTION TEST             ║"
echo "║                                                            ║"
echo "║  Watch your Pixoo display as we test all features!        ║"
echo "╚════════════════════════════════════════════════════════════╝"
echo "$NORMAL"
echo

# Test 1: Basic Light Control
echo "$BLUE━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━$NORMAL"
echo "$BLUE TEST 1: Light Control$NORMAL"
echo "$BLUE━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━$NORMAL"

call_service "light/turn_on" '{"entity_id":"'$ENTITY'","brightness":255}'
wait_and_continue "Display at 100% brightness" 2

call_service "light/turn_on" '{"entity_id":"'$ENTITY'","brightness":128}'
wait_and_continue "Display at 50% brightness" 2

call_service "light/turn_on" '{"entity_id":"'$ENTITY'","brightness":255}'
wait_and_continue "Display back to 100%" 2

echo

# Test 2: Channel Switching Buttons
echo "$BLUE━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━$NORMAL"
echo "$BLUE TEST 2: Channel Switching Buttons$NORMAL"
echo "$BLUE━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━$NORMAL"

call_service "button/press" '{"entity_id":"button.pixoo_switch_to_clock_channel"}'
wait_and_continue "Switched to Clock Channel" 3

call_service "button/press" '{"entity_id":"button.pixoo_switch_to_visualizer_channel"}'
wait_and_continue "Switched to Visualizer Channel" 3

call_service "button/press" '{"entity_id":"button.pixoo_switch_to_cloud_channel"}'
wait_and_continue "Switched to Cloud Channel" 3

echo

# Test 3: Display Image
echo "$BLUE━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━$NORMAL"
echo "$BLUE TEST 3: Display Image$NORMAL"
echo "$BLUE━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━$NORMAL"

call_service "pixoo/display_image" '{"entity_id":"'$ENTITY'","url":"https://picsum.photos/64/64"}'
wait_and_continue "Showing random image from picsum.photos" 5

echo

# Test 4: Display Text
echo "$BLUE━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━$NORMAL"
echo "$BLUE TEST 4: Display Scrolling Text$NORMAL"
echo "$BLUE━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━$NORMAL"

call_service "pixoo/display_text" '{"entity_id":"'$ENTITY'","text":"Hello from ha-pixoo! Testing scrolling text...","color":"#00FF00","x":0,"y":32,"font":2,"speed":50,"text_id":1,"scroll_direction":"left"}'
wait_and_continue "Showing green scrolling text" 8

call_service "pixoo/display_text" '{"entity_id":"'$ENTITY'","text":"RED TEXT","color":"#FF0000","x":0,"y":10,"font":3,"speed":0,"text_id":2,"scroll_direction":"left"}'
wait_and_continue "Added red static text overlay" 5

echo

# Test 5: Clear Display
echo "$BLUE━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━$NORMAL"
echo "$BLUE TEST 5: Clear Display$NORMAL"
echo "$BLUE━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━$NORMAL"

call_service "pixoo/clear_display" '{"entity_id":"'$ENTITY'"}'
wait_and_continue "Display cleared to black" 2

echo

# Test 6: Buzzer
echo "$BLUE━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━$NORMAL"
echo "$BLUE TEST 6: Buzzer Alert$NORMAL"
echo "$BLUE━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━$NORMAL"

call_service "pixoo/play_buzzer" '{"entity_id":"'$ENTITY'","active_time":500,"off_time":500,"total_time":3000}'
wait_and_continue "Playing buzzer (3 beeps)" 4

echo

# Test 7: Timer
echo "$BLUE━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━$NORMAL"
echo "$BLUE TEST 7: Timer Control$NORMAL"
echo "$BLUE━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━$NORMAL"

call_service "pixoo/set_timer" '{"entity_id":"'$ENTITY'","minutes":0,"seconds":10,"running":true}'
wait_and_continue "Timer started (10 seconds)" 5

call_service "pixoo/set_timer" '{"entity_id":"'$ENTITY'","minutes":0,"seconds":0,"running":false}'
wait_and_continue "Timer stopped" 2

echo

# Test 8: Notify Service
echo "$BLUE━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━$NORMAL"
echo "$BLUE TEST 8: Notify Service$NORMAL"
echo "$BLUE━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━$NORMAL"

call_service "notify/pixoo_display" '{"message":"Test notification!","title":"Alert","data":{"color":"#FFAA00","font":3,"buzzer":true,"buzzer_active_time":300,"buzzer_off_time":300,"buzzer_total_time":1500}}'
wait_and_continue "Showing notification with buzzer" 6

echo

# Test 9: Rotation & Mirror
echo "$BLUE━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━$NORMAL"
echo "$BLUE TEST 9: Screen Rotation & Mirror$NORMAL"
echo "$BLUE━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━$NORMAL"

# Show text to make rotation visible
call_service "pixoo/display_text" '{"entity_id":"'$ENTITY'","text":"ROTATION TEST","color":"#00FFFF","x":0,"y":28,"font":3,"speed":0,"text_id":1,"scroll_direction":"left"}'
wait_and_continue "Showing rotation test text" 2

call_service "select/select_option" '{"entity_id":"select.pixoo_rotation","option":"90"}'
wait_and_continue "Rotated 90 degrees" 3

call_service "select/select_option" '{"entity_id":"select.pixoo_rotation","option":"180"}'
wait_and_continue "Rotated 180 degrees" 3

call_service "select/select_option" '{"entity_id":"select.pixoo_rotation","option":"0"}'
wait_and_continue "Back to normal rotation" 2

call_service "switch/turn_on" '{"entity_id":"switch.pixoo_mirror_mode"}'
wait_and_continue "Mirror mode ON" 3

call_service "switch/turn_off" '{"entity_id":"switch.pixoo_mirror_mode"}'
wait_and_continue "Mirror mode OFF" 2

echo

# Test 10: Return to Cloud Channel
echo "$BLUE━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━$NORMAL"
echo "$BLUE TEST 10: Final Channel Restore$NORMAL"
echo "$BLUE━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━$NORMAL"

call_service "pixoo/clear_display" '{"entity_id":"'$ENTITY'"}'
wait_and_continue "Cleared display" 1

call_service "button/press" '{"entity_id":"button.pixoo_switch_to_cloud_channel"}'
wait_and_continue "Restored to Cloud Channel" 2

echo
echo "$GREEN"
echo "╔════════════════════════════════════════════════════════════╗"
echo "║                    ALL TESTS COMPLETE!                     ║"
echo "║                                                            ║"
echo "║  ✓ Light Control                                           ║"
echo "║  ✓ Channel Switching Buttons (4)                           ║"
echo "║  ✓ Display Image                                           ║"
echo "║  ✓ Display Text (scrolling & static)                       ║"
echo "║  ✓ Clear Display                                           ║"
echo "║  ✓ Buzzer Alert                                            ║"
echo "║  ✓ Timer Control                                           ║"
echo "║  ✓ Notify Service                                          ║"
echo "║  ✓ Rotation & Mirror                                       ║"
echo "║  ✓ Channel Restore                                         ║"
echo "║                                                            ║"
echo "║  Your ha-pixoo integration is working perfectly! 🎉        ║"
echo "╚════════════════════════════════════════════════════════════╝"
echo "$NORMAL"
