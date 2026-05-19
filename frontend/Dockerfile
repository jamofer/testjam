# syntax=docker/dockerfile:1.7
FROM node:22-alpine

WORKDIR /app

COPY package.json package-lock.json ./
RUN --mount=type=cache,target=/root/.npm npm ci

COPY . .

CMD ["npm", "run", "dev"]
