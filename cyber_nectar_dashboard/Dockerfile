# Stage 1: Build the Flutter web application
FROM ghcr.io/cirruslabs/flutter:stable AS builder

# Set the working directory
WORKDIR /app

# Copy dependency files and get packages
COPY pubspec.* ./
RUN flutter pub get

# Copy the rest of the project files
COPY . .

# Build the Flutter web application for release
RUN flutter build web --release

# Stage 2: Serve the application with Nginx
FROM nginx:alpine

# Copy the static files from the builder stage
COPY --from=builder /app/build/web /usr/share/nginx/html

# Expose port 80
EXPOSE 80

# Start Nginx
CMD ["nginx", "-g", "daemon off;"]
