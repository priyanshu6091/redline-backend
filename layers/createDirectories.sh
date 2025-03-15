#!/bin/bash

# List of dependencies with versions
dependencies=("pymongo" "pytz" "requests")


# Function to create a directory and a requirements.txt file inside

# Function to create a directory and a requirements.txt file inside
create_dependency_directory() {
    dependency="$1"
    directory="${dependency%%==*}Dependency"  # Extract dependency name without version
    
    # Create the directory if it doesn't exist
    mkdir -p "$directory"
    
    # Create the requirements.txt file and write the dependency with its version
    echo "$dependency" > "$directory/${directory}-requirements.txt"
}

# Create directories and requirements.txt files


for dep in "${dependencies[@]}"; do
    create_dependency_directory "$dep"
done

# aws lambda publish-layer-version --layer-name wandDependency \
#     --description "Wand + ImageMagick" \
#     --zip-file fileb://D:/Redline/redline-backend/wand-layer.zip
#     --compatible-runtimes python3.10
#     D:\Redline\redline-backend\wand-layer.zip