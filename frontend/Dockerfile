FROM node:20-alpine AS builder
WORKDIR /app
COPY package.json ./
RUN npm install --legacy-peer-deps
COPY . .
RUN npm run build

FROM nginx:alpine
COPY --from=builder /app/build /usr/share/nginx/html
COPY nginx.conf.template /etc/nginx/templates/default.conf.template
LABEL org.opencontainers.image.source=https://github.com/KrapfalAT/kellerlog
ENV BACKEND_HOST=backend
EXPOSE 80
