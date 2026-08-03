# Local APK Store - Android Client

This directory is reserved for the Android Client App, built to resemble the classic "Android Market" before it became the Google Play Store. 
Because setting up a complete Android build system natively via CLI requires Android Studio or standard SDK/Gradle setups not fully bootstrapped here yet, this serves as the foundational plan and skeleton.

## Planned Features
- **Retro UI:** Green/Black/White color scheme. Tabbed layout with "Apps", "Games", and "Downloads".
- **Dynamic Fetching:** Uses Retrofit or standard HTTPURLConnections to pull the JSON manifest from `http://<YOUR_LOCAL_IP>:8443/api/apps`.
- **Search Capabilities:** Top search bar that filters the list of available applications natively or via the backend `?q=` parameter.
- **Silent Installation (Shizuku & Dhizuku):** Instead of standard intents, the app will heavily rely on [Shizuku](https://shizuku.rikka.app/) (ADB/Root API access) and [Dhizuku](https://github.com/iamr0s/Dhizuku) (Device Owner API access) to perform true background/silent APK installations and updates, perfectly mimicking the seamless native Play Store experience without user prompts.

## Next Steps for Development
1. Open this folder in **Android Studio**.
2. Create an Empty Views Activity project.
3. Configure `AndroidManifest.xml` to request `INTERNET` and declare Shizuku/Dhizuku API bindings.
4. Add the Shizuku API dependencies to `build.gradle`.
5. Implement the UI components mimicking Android OS 2.3 (Gingerbread) Market style.
