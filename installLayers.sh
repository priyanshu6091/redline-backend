#!/bin/bash

# Define the root directory
root_directory="./layers"


# Function to install requirements from a given requirements file
install_requirements() {
    requirements_file="$1"
    directory=$(dirname "$requirements_file")
    pip3 install --platform manylinux2014_x86_64 --only-binary=:all: --upgrade -t "$directory/python/" -r "$requirements_file"
}

install_requirements_normal(){
    requirements_file="$1"
    directory=$(dirname "$requirements_file")
    pip3 install -t "$directory/python/" -r "$requirements_file"

}

# Use find to locate all requirements files and install the dependencies
find "$root_directory" -type f -name '*-requirements.txt' -print | while read -r requirements_file; do
    # Extract the directory name without the root_directory
    relative_directory=$(realpath --relative-to="$root_directory" "$(dirname "$requirements_file")")

    # Check if 'python' directory already exists in the relative_directory
    if [ ! -d "$root_directory/$relative_directory/python" ]; then
        echo "Installing requirements for $requirements_file..."
        install_requirements "$requirements_file"
    else
        echo "Python directory already exists in $relative_directory. Skipping installation."
    fi
done


find "$root_directory" -type f -name '*-requirements.txt' -print | while read -r requirements_file; do
    # Extract the directory name without the root_directory
    relative_directory=$(realpath --relative-to="$root_directory" "$(dirname "$requirements_file")")

    # Check if 'python' directory already exists in the relative_directory
    if [ ! -d "$root_directory/$relative_directory/python" ]; then
        echo "Installing requirements for $requirements_file..."
        install_requirements_normal "$requirements_file"
    else
        echo "Python directory already exists in $relative_directory. Skipping installation."
    fi
done