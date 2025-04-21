FROM node:20-alpine

WORKDIR /app

COPY . .

RUN npm install

# Build
RUN npm run build

EXPOSE 3000

# Run
CMD ["npm", "start"]
