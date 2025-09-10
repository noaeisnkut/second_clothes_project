print_status "Initializing Git workflow..."
git checkout -b develop
git push -u origin develop

if [ ! -f .gitignore ]; then
    echo "node_modules/" >> .gitignore
    echo "*.log" >> .gitignore
    echo ".env" >> .gitignore
fi

git add .gitignore
git commit -m "Add project .gitignore"