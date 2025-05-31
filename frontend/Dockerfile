# Use official Node.js image
FROM node:18-alpine

# Set working directory
WORKDIR /app

# Copy package files and install dependencies
COPY package*.json ./
RUN npm install

# Copy rest of the project files
COPY . .

# Build the Next.js app
RUN npm run build

# Expose the port Next.js runs on
EXPOSE 3000

# Start the application
CMD ["npm", "run", "start"]