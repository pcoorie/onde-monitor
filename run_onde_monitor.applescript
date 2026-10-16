tell application "iTerm"
    activate
    set newWindow to (create window with default profile)
    tell current session of newWindow
        write text "cd \"$HOME/onde_monitor\" && python3 onde_monitor.py"
    end tell
end tell
