#!/bin/bash

SCRIPT=$(readlink -f "$0")
SCRIPTPATH=$(dirname "$SCRIPT")
REQUIREMENTSPATH=$(dirname "$SCRIPTPATH")/requirements
OUTPUTDIR=xxxunspecified

ENVIRONMENT=base
if [ "$#" -eq 1 ]; then
	ENVIRONMENT="$1"
elif [ "$#" -eq 2 ]; then
	ENVIRONMENT="$1"
	OUTPUTDIR="$2"
elif [ "$#" -eq 0 ]; then
	:
else
	echo "$0" \[build_environment\] \[output_dir\]
	exit 3
fi

if [ "$OUTPUTDIR" == "xxxunspecified" ]; then
	OUTPUTDIR=$(pwd)/wheels-${ENVIRONMENT}
fi

ENVIRONMENT_FILE="${REQUIREMENTSPATH}/${ENVIRONMENT}.txt"

echo Building wheels for $ENVIRONMENT from $ENVIRONMENT_FILE
if [ ! -f $ENVIRONMENT_FILE ]; then
	echo No such environment: $ENVIRONMENT
	exit 1
fi

if [ -d $OUTPUTDIR ]; then
	echo Output directory $OUTPUTDIR already exists
	exit 2
fi

PIP=$(which pip3 2>/dev/null) || PIP=$(which pip 2>/dev/null) || { 
	echo Could not find pip or pip3, bailing
	exit 4
}

mkdir $OUTPUTDIR
$PIP wheel --wheel-dir="$OUTPUTDIR" -r "$ENVIRONMENT_FILE"
