tell application "iTerm"
    activate
    set newWindow to (create window with default profile)
    tell current session of newWindow
        write text "cd \"$HOME/onde_monitor\" && ./run_onde_monitor_firefox.sh"
    end tell
end tell
