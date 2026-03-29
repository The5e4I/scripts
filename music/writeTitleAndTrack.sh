#!/bin/bash

# Requires: eyeD3
# Format expected: "01 - Title.mp3"

shopt -s nullglob

for file in *.mp3; do
    # Get filename without extension
    base=$(basename "$file" .mp3)

    # Check for pattern "track - title"
    if [[ "$base" =~ ^([0-9]+)[[:space:]]*-[[:space:]]*(.+)$ ]]; then
        track="${BASH_REMATCH[1]}"
        title="${BASH_REMATCH[2]}"
    else
        track=""
        title="$base"
    fi

    # Update metadata using eyeD3
    if [[ -n "$track" ]]; then
        eyed3 --title="$title" --track="$track" "$file"
    else
        eyed3 --title="$title" "$file"
    fi

    echo "Updated: $file -> Title='$title' Track='${track:-N/A}'"
done
