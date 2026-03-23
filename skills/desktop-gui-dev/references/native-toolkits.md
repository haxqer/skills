# Native Toolkits

Use this reference when the app should be built with a native UI toolkit instead of a web-shell desktop framework.

## Support Boundary

- This reference is for toolkit selection, architecture, and release-readiness guidance. It is not a replacement for toolkit-specific API docs, IDE setup guides, or vendor packaging instructions.
- If the repo already uses a specific toolkit, read that toolkit's official docs before changing generated project files, build settings, signing, or installer configuration.
- Use this skill to decide structure and cross-layer boundaries; use the official toolkit docs to resolve toolkit-specific commands and APIs.

## Official Docs

- Qt docs: <https://doc.qt.io/>
- Qt Creator getting started: <https://doc.qt.io/qtcreator/creator-getting-started.html>
- SwiftUI: <https://developer.apple.com/swiftui/>
- AppKit: <https://developer.apple.com/documentation/AppKit>
- WinUI overview: <https://learn.microsoft.com/en-us/windows/apps/winui/winui3/>
- WinUI setup: <https://learn.microsoft.com/en-us/windows/apps/how-tos/hello-world-winui3>
- WPF overview: <https://learn.microsoft.com/en-us/dotnet/desktop/wpf/overview/>
- GTK getting started: <https://docs.gtk.org/gtk4/getting_started.html>
- .NET MAUI overview: <https://learn.microsoft.com/en-us/dotnet/maui/>
- .NET MAUI first app: <https://learn.microsoft.com/en-us/dotnet/maui/get-started/first-app>

If project templates, IDE setup, or packaging behavior differ from this reference, prefer the official docs for the chosen toolkit.

## When To Use

- Native controls, accessibility fidelity, or platform conventions matter more than web-stack reuse.
- The app relies heavily on OS-native windowing, input, menu, or graphics behavior.
- Cross-platform reuse is still useful, but a browser-style renderer is the wrong abstraction.

## Toolkit Selection Heuristic

- Choose SwiftUI or AppKit when the app is Apple-only or macOS-first.
- Choose WinUI or WPF when the app is Windows-first and native Windows behavior matters.
- Choose Qt when the app needs mature cross-platform native widgets and a C++ or Python-friendly ecosystem.
- Choose GTK or libadwaita when Linux desktop integration is the main concern.
- Choose .NET MAUI when the team is invested in .NET and wants broader client-platform reuse.

## Creation Guidance

- Use the official project template or IDE starter for the chosen toolkit.
- Preserve the generated project structure unless there is a strong reason to change it.
- Establish app identity, icons, bundle identifiers, and platform entitlements early.
- Treat packaging, signing, and store-specific setup as toolkit- and OS-specific work. Read the vendor docs before editing those flows.

## Repository Entry Points

- Qt: inspect `CMakeLists.txt` or `.pro` first, then the app entry point such as `main.cpp`, UI resources such as `.qrc`, and deployment metadata used by the repo.
- SwiftUI or AppKit: inspect the `.xcodeproj` or `.xcworkspace`, `App.swift` or `AppDelegate.swift`, `Info.plist`, entitlements, and any login-item or helper targets before changing app behavior.
- WinUI or WPF: inspect the `.sln`, the main `.csproj`, `App.xaml`, the startup window or page, and packaging manifests such as `Package.appxmanifest` or a Windows packaging project when present.
- GTK or libadwaita: inspect `meson.build`, the main source entry point, `.desktop` metadata, icons, and any Flatpak or distro packaging files the repo ships with.
- .NET MAUI: inspect the `.sln`, main `.csproj`, `MauiProgram.cs`, `App.xaml`, and the `Platforms/` directory for OS-specific integrations.
- Before editing, read the real project manifests, entitlements, and packaging files instead of assuming the starter-template layout is still intact.

## Default Working Pattern

- Organize around screens or windows, view models or controllers, services, persistence, and platform adapters.
- Keep file dialogs, notifications, menu commands, background work, and persistence out of the view layer.
- Treat view-model or controller boundaries as the equivalent of the bridge boundary used in web-shell apps.

## Validation Checklist

- The app launches through the native runtime or IDE target, not just through isolated component previews.
- Resize behavior, keyboard navigation, accessibility hooks, and high-DPI rendering are tested on the target OS.
- Packaging metadata, signing requirements, and installer settings are updated together with the code.
- Any unsupported OS path or toolkit-specific limitation is made explicit instead of guessed from a different toolkit.
