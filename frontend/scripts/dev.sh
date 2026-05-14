#!/bin/sh
set -e

npm install --prefer-offline --no-audit
exec npm run dev
