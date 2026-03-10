# ------------------------------------------------------------------------------
# HealthOps Studio - Frontend Dockerfile
# ------------------------------------------------------------------------------
# This Dockerfile builds the Next.js application into a production static/standalone build.

# --- Stage 1: Dependencies ---
FROM node:20.11-alpine AS deps
RUN apk add --no-cache libc6-compat
WORKDIR /app

# Copy package headers
COPY package.json package-lock.json ./
# Clean install exactly what is in package-lock.json
RUN npm ci

# --- Stage 2: Builder ---
FROM node:20.11-alpine AS builder
WORKDIR /app
COPY --from=deps /app/node_modules ./node_modules
COPY . .

# Next.js telemetry can be annoying during build
ENV NEXT_TELEMETRY_DISABLED=1

# Build the Next.js application
RUN npm run build

# --- Stage 3: Runner ---
FROM node:20.11-alpine AS runner
WORKDIR /app

ENV NODE_ENV=production
ENV NEXT_TELEMETRY_DISABLED=1

# Don't run production as root
RUN addgroup --system --gid 1001 nodejs
RUN adduser --system --uid 1001 nextjs

# Set the correct permission for prerender cache
RUN mkdir .next
RUN chown nextjs:nodejs .next

# Copy built assets from builder stage
COPY --from=builder /app/public ./public
# Next.js standalone output isolates only the necessary files for production
COPY --from=builder --chown=nextjs:nodejs /app/.next/standalone ./
COPY --from=builder --chown=nextjs:nodejs /app/.next/static ./.next/static

USER nextjs

EXPOSE 3000

ENV PORT=3000

# Server.js is created by Next.js standalone output mode
CMD ["node", "server.js"]
