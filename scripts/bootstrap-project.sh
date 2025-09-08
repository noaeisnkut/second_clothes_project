# Add to your bootstrap script
print_status "Initializing Git workflow..."

# Create development branch
git checkout -b develop
git push -u origin develop

# Create basic .gitignore if not exists
if [ ! -f .gitignore ]; then
    # Add .gitignore content based on your tech stack
    echo "node_modules/" >> .gitignore
    echo "*.log" >> .gitignore
    echo ".env" >> .gitignore
    # Add more based on your stack
fi

git add .gitignore
git commit -m "Add project .gitignore"