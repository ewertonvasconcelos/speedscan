#!/bin/bash
VERSION="v1.1.0"
git add .
git commit -m "Release $VERSION"
git push origin main
git tag -a $VERSION -m "Release $VERSION"
git push origin $VERSION
echo "✅ Release $VERSION criada e enviada. Acompanhe em:"
echo "   https://github.com/ewertonvasconcelos/speedscan/actions"
