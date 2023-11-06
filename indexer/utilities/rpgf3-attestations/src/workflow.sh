#!/bin/bash

echo "*******************************************"
echo "Indexing local version of OSS Directory..."
python src/oss_directory.py
echo ""

echo "*******************************************"
echo "Reviewing EAS applications..."
python src/fetch_from_eas.py
echo ""

echo "*******************************************"
echo "Analyzing projects' contribution links & impact metrics..."
python src/analyze_apps.py
echo ""

echo "*******************************************"
echo "Updating the canonical list of projects..."
python src/canonical.py

#python src/reviewer.py