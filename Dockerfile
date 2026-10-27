FROM node:20-slim

WORKDIR /app

# کپی package.json و نصب
COPY package.json bun.lock ./
RUN npm install --legacy-peer-deps

# کپی پروژه
COPY . .

# build
RUN npm run build

EXPOSE 3000

CMD ["npm", "start"]
