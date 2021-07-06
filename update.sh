#!/bin/bash
BLISSHOME=$(dirname $0)
BLISSMAP="$BLISSHOME/makecdmap.py"
BLISSLIST="$BLISSHOME/makecdlist.py"
INKSCAPE="inkscape --shell"
OUTPUT="/dev/null"
TAGS=""
NOMAPS=""
NOLISTS=""

AREAS=(
    'Derrick Road'
    'Kelseyton'
    'Oakleyville'
    'Robbins Creek'
    'Pickle Street',
    'Sessions Road'
    'Timber Lake'
    'Uptonville'
)

function exportCmd() {
    # Note: Inkscape version dependant
    #echo "file-open:'$1'; export-type:pdf; export-do;"
    SVGFILE="$1"
    PDFFILE="${1%.svg}.pdf"
    echo "'$SVGFILE'" --export-pdf "'$PDFFILE'"
}

function exportAreaCmd() {
    if [[ -z $NOMAPS ]]; then
        exportCmd "$1 Map.svg"
    fi
    if [[ -z $NOLISTS ]]; then
        exportCmd "$1 Addresses.svg"
    fi
}

function exportAreasCmd() {
    for AREA in "${AREAS[@]}"; do
        if [[ -z $TAGS || $TAGS =~ $AREA ]]; then
            exportAreaCmd "$AREA"
        fi
    done
    echo "quit"
}

function exportAreas() {
    exportAreasCmd | $INKSCAPE >>$OUTPUT
}

function updateArea() {
    if [[ -z $NOMAPS ]]; then
        $BLISSMAP "$1.csv" "$1 Map.svg"
    fi
    if [[ -z $NOLISTS ]]; then
        $BLISSLIST "$1.csv" "$1 Addresses.svg"
    fi
}

function updateAreas() {
    for AREA in "${AREAS[@]}"; do
        if [[ -z $TAGS || $TAGS =~ $AREA ]]; then
            updateArea "$AREA"
        fi
    done
}

function usage()
{
    cat <<EOF
usage: $0 [options] [tags]

options:
    -m                       don't update the address lists
    -l                       don't update the maps
    -n                       don't update the maps or the address lists

tags:
    <areas>                  only update those areas specified
EOF
}

function parseArgs()
{
    while [ $# -gt 0 ]; do
        case "$1" in
            -m) NOLISTS=1; shift;;
            -l) NOMAPS=1; shift;;
            -n|-ml|-lm) NOLISTS=1; NOMAPS=1; shift;;
            -*) usage; exit 0;;
            *)  TAGS="$TAGS $1"; shift;;
        esac
    done
}

parseArgs "$@"
updateAreas
exportAreas
git commit -a -m "update"; git push


