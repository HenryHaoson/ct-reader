#!/bin/bash
# Decode QR code from an image file using zbarimg
# Usage: ./decode_qr.sh <image_path>
# Returns: the decoded URL (first QR code found)

if [ -z "$1" ]; then
  echo "Usage: $0 <image_path>" >&2
  exit 1
fi

if [ ! -f "$1" ]; then
  echo "Error: File not found: $1" >&2
  exit 1
fi

# Decode QR code, output raw data only, quiet mode
URL=$(zbarimg --quiet --raw "$1" 2>/dev/null | head -1)

if [ -z "$URL" ]; then
  echo "Error: No QR code found in image" >&2
  exit 1
fi

echo "$URL"
