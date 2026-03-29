#!/bin/bash

# Check if ffmpeg is installed
if ! command -v ffmpeg &> /dev/null; then
    echo "Error: ffmpeg is not installed. Please install ffmpeg and try again."
    exit 1
fi

# Set the VBR quality level (0 is highest, 9 is lowest quality)
VBR_QUALITY=0

# Convert all FLAC files to MP3
for file in *.flac; do
    # Skip if no flac files are found
    [ -e "$file" ] || continue

    # Extract filename without extension
    base_name="${file%.flac}"
    
    # Convert to MP3 with VBR encoding
    ffmpeg -i "$file" -codec:a libmp3lame -qscale:a $VBR_QUALITY "${base_name}.mp3"
    
    echo "Converted: $file -> ${base_name}.mp3"

done

# remove all flac
rm *.flac
