FROM node:22-slim AS deps
WORKDIR /app
COPY package*.json ./
RUN npm ci

# `deps` is the target used for local dev (docker-compose.dev.yml) — source
# is bind-mounted over this at runtime and `npm run dev` serves it directly,
# no build step needed.

FROM deps AS build
COPY . .
RUN npm run build

# Production: no Node process at runtime, per docs/deployment.md §1 — just
# the static build, served by a lightweight Nginx that the top-level
# `nginx` service reverse-proxies to.
FROM nginx:1.27-alpine AS production
COPY --from=build /app/dist /usr/share/nginx/html
COPY docker/nginx.conf /etc/nginx/conf.d/default.conf
EXPOSE 80
