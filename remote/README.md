# Nostromo Remote

Android companion app for the Nostromo terminal. Share YouTube links from the YouTube app directly to Nostromo, and control playback (seek, volume, pause) from your phone.

## Requirements

- [Flutter SDK](https://docs.flutter.dev/get-started/install) 3.8+
- Android SDK (installed via `flutter doctor`)
- Java 21+

## Build APK

```bash
cd remote
flutter pub get
flutter build apk --release
```

The APK will be at:

```
build/app/outputs/flutter-apk/app-release.apk
```

Transfer it to your phone and install (enable "Install from unknown sources" if needed).

## How it works

1. Open the app, enter Nostromo's IP address (e.g. `192.168.1.42` or `palm.local`), tap **LINK**
2. **Share a YouTube video** from the YouTube app — choose "Nostromo Remote" in the share menu
3. The video starts playing on Nostromo automatically
4. Use the on-screen controls for **seek** (-10s / +10s), **pause/play**, and **volume**

## API endpoints (server side)

The app communicates with the Nostromo HTTP API on port 8080:

| Method | Endpoint  | Body                    | Description            |
|--------|-----------|-------------------------|------------------------|
| GET    | /ping     | —                       | Health check           |
| GET    | /status   | —                       | Player state           |
| POST   | /play     | `{"url": "..."}`        | Queue YouTube video    |
| POST   | /seek     | `{"seconds": 10}`       | Seek (negative = back) |
| POST   | /volume   | `{"delta": 0.1}`        | Volume (negative = down) |
| POST   | /pause    | `{}`                    | Toggle pause           |

The server code lives in `software/api/server.py`.

## Troubleshooting

**Build fails with JVM target mismatch:**
The `kotlin.jvm.target.validation.mode=ignore` line in `android/gradle.properties` handles this. If it reappears after updating dependencies, verify that line is still present.

**App can't connect:**
Make sure your phone and Nostromo are on the same network. Check that port 8080 is not blocked by a firewall on the Pi.
