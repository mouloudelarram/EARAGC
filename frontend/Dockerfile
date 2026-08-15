FROM node:20-alpine

WORKDIR /app

# Install dependencies first (better layer caching)
COPY package*.json ./
RUN npm install

# Copy source
COPY . .

EXPOSE 5173

# Run Vite dev server listening on all interfaces
CMD ["npm", "run", "dev"]

