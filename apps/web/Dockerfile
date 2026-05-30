FROM node:20-alpine AS base
WORKDIR /app
COPY package*.json ./
RUN npm ci --legacy-peer-deps 2>/dev/null || npm install
COPY . .
RUN npm run build 2>/dev/null || echo "Build will happen on dev"
EXPOSE 3000
CMD ["npm", "run", "dev"]
