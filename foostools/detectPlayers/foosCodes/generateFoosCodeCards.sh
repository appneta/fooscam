#!/bin/bash

rm -rf codes
mkdir -p codes

for i in {0..511}; do
    BIN=$(echo "obase=2; $i" | bc)
    BIN=$(echo $BIN | awk '{printf "%09s\n", $0}')
    NUM=$(echo $i | awk '{printf "%03s\n", $0}')
    PATTERN=
    
    if [ "${BIN:0:1}" = "1" ]; then
        PATTERN="$PATTERN\n<ellipse rx=\"14.5904\" ry=\"14.3856\" cx=\"480\" cy=\"300\"/>"
    fi
    if [ "${BIN:1:1}" = "1" ]; then
        PATTERN="$PATTERN\n<ellipse rx=\"14.5904\" ry=\"14.3856\" cx=\"510\" cy=\"300\"/>"
    fi
    if [ "${BIN:2:1}" = "1" ]; then
        PATTERN="$PATTERN\n<ellipse rx=\"14.5904\" ry=\"14.3856\" cx=\"540\" cy=\"300\"/>"
    fi
    if [ "${BIN:3:1}" = "1" ]; then
        PATTERN="$PATTERN\n<ellipse rx=\"14.5904\" ry=\"14.3856\" cx=\"480\" cy=\"330\"/>"
    fi
    if [ "${BIN:4:1}" = "1" ]; then
        PATTERN="$PATTERN\n<ellipse rx=\"14.5904\" ry=\"14.3856\" cx=\"510\" cy=\"330\"/>"
    fi
    if [ "${BIN:5:1}" = "1" ]; then
        PATTERN="$PATTERN\n<ellipse rx=\"14.5904\" ry=\"14.3856\" cx=\"540\" cy=\"330\"/>"
    fi
    if [ "${BIN:6:1}" = "1" ]; then
        PATTERN="$PATTERN\n<ellipse rx=\"14.5904\" ry=\"14.3856\" cx=\"480\" cy=\"360\"/>"
    fi
    if [ "${BIN:7:1}" = "1" ]; then
        PATTERN="$PATTERN\n<ellipse rx=\"14.5904\" ry=\"14.3856\" cx=\"510\" cy=\"360\"/>"
    fi
    if [ "${BIN:8:1}" = "1" ]; then
        PATTERN="$PATTERN\n<ellipse rx=\"14.5904\" ry=\"14.3856\" cx=\"540\" cy=\"360\"/>"
    fi
    
    TEMPLATE=$(cat << EOF
<?xml version="1.0" encoding="UTF-8"?>
<svg xmlns="http://www.w3.org/2000/svg" xmlns:xlink="http://www.w3.org/1999/xlink" fill-opacity="1" color-rendering="auto" 
    color-interpolation="auto" stroke="black" text-rendering="auto" stroke-linecap="square" width="215" stroke-miterlimit="10" 
    stroke-opacity="1" shape-rendering="auto" fill="black" stroke-dasharray="none" font-weight="normal" stroke-width="1" 
    height="215" font-family="'Dialog'" font-style="normal" stroke-linejoin="miter" font-size="12" stroke-dashoffset="0" 
    image-rendering="auto">
    
  <g>
    <g stroke-linecap="butt" transform="matrix(1,0,0,1,-404,-224)" stroke-miterlimit="1.45" font-size="8">
      <rect fill="none" x="419.9794" width="180.0411" height="180.2594" y="239.8703"/>
      <ellipse rx="14.5904" ry="14.3856" cx="450" cy="270"/>
      
      $PATTERN
      
      <text x="430" y="417" text-anchor="middle" stroke="none" fill="#c1c1c1">$NUM</text>
    </g>
  </g>
</svg>
EOF
);

    echo "$TEMPLATE" > tmp.svg
    echo "Creating codes/$NUM.pdf ..."
    inkscape tmp.svg --export-pdf=codes/$NUM.pdf
    rm tmp.svg
    
done

echo "Done."
