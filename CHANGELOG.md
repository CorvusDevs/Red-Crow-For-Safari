# Changelog

## v1.0 Beta 2 (2026-04-28)

### iOS Support
- Added iOS app target with SwiftUI welcome screen and extension status detection
- Added iOS Safari Web Extension target sharing all extension resources with macOS
- Supports iPhone and iPad (iOS 17+)
- App icon and asset catalog for iOS

### Settings Page
- Parent-child settings now use collapsible reveal (children hidden when parent off, smooth animation when toggled on)
- Sections with parent-child groups automatically use single-column layout to eliminate dead space
- Removed red modified-indicator dots and sidebar badge counts
- Removed Diagnostics & Profiling section and Copy Debug Log button
- Fixed sidebar navigation highlighting not reaching Manage (last section)
- Fixed race condition where updateDependencies ran before settings loaded

## v1.0 Beta 1 (2026-04-28)

Initial release of Red Crow for Safari — a comprehensive YouTube enhancement extension.

### Playback
- Default speed, volume, and quality controls
- Per-channel speed profiles
- Remember speed and position across sessions
- Pitch preservation toggle
- Quality fallback chain (auto-downgrade when preferred quality unavailable)
- Fullscreen-specific quality override
- Codec control: block/force VP9, block AV1, block HFR
- Disable autoplay and playlist autoplay

### Player UI
- Custom toolbar with 19 buttons (screenshot, copy URL, loop, A-B loop, bookmark, reverse, shuffle, cinema, PiP, pop-out, wide, expand, flip H/V, rotate, stats, share, audio only, transcript)
- Drag-to-reorder toolbar buttons with per-button visibility toggles
- Toolbar auto-hide and position options (below, inside-top, inside-bottom)
- Cinema mode with adjustable opacity and background color
- Wide player and expand player modes
- Mini-player with drag-to-reposition and corner presets
- Always-show progress bar
- Custom endscreen overlay with thumbnail grid, metadata, and ESC to close
- Double-tap to seek with configurable amount
- Video filters (brightness, contrast, saturation, blur, warmth, grayscale, sepia, hue rotate, invert)

### Navigation & Behavior
- Auto theater mode
- Auto-expand description
- Convert Shorts to regular videos
- Redirect homepage to subscriptions
- Scroll-wheel volume control (with right-click modifier option)
- Prevent idle pause ("Are you still watching?")
- Prevent background tab autoplay
- Auto PiP on tab switch
- Auto fullscreen on play
- Strip tracking parameters from URLs
- Auto-skip "leave site?" dialogs
- Middle-click to pop out video

### Hide & Clean
- Hide: comments, related videos, end cards, Shorts, chat, notifications, trending, mixes, watermark, share/clip/thanks/membership buttons, pause overlay, ambient mode, info cards, premium upsell, search suggestions, AI summaries, sponsored content, animated thumbnails, member-only content, homepage
- Dim watched videos
- Filter by duration (min/max)
- Block channels, keywords (with regex support), and categories
- Channel whitelist

### Integrations
- SponsorBlock: skip sponsor, intro, outro, interaction, self-promo, music, preview, filler segments with progress bar overlay and skip/mute options
- Return YouTube Dislike: show dislike count and like/dislike ratio bar
- DeArrow: replace clickbait titles and thumbnails with community submissions, auto-format titles, fallback thumbnail options

### Keyboard Shortcuts
- Configurable shortcuts for: loop, screenshot, PiP, pop-out, expand, cinema, bookmark, mute, volume up/down, seek forward/back (5s and 10s), next/prev chapter, frame forward/back, wide player

### Appearance
- Force YouTube theme (light/dark/off)
- Scheduled dark mode with configurable time range
- Videos per row and Shorts per row customization
- Search results grid layout
- Custom CSS injection
- Header transparency and scroll-to-top button

### Settings Page
- Full-featured settings page with collapsible sections
- Live toolbar preview strip with SVG icons
- Section reset buttons
- Presets (Podcast, Minimal, Privacy, Cinema)
- Import settings from other extensions
- Settings profiles (save/load/delete)
- Collapsible parent-child settings with smooth reveal animation

### Other
- Usage timer with configurable duration and sound alert
- Time saved tracker (SponsorBlock skips and speed changes)
- Comment search
- Sort comments by newest
- Comments sidebar mode
- Timestamp bookmarks with export
- Remaining duration display
- Feature toast notifications
- Per-channel settings profiles
- 14-locale App Store metadata (EN, ES, FR, DE, IT, JA, KO, PT-BR, RU, ZH-Hans, ZH-Hant, AR, TH, TR, NL)

### Bug Fixes (pre-release)
- Fixed SponsorBlock not activating on initial page load
- Fixed endscreen scrollbar, missing dates, and control bar bleeding through
- Fixed settings-dependent functions running before settings loaded
- Added null-safety guards for endscreen cleanup and audio graph
- Removed unreliable Web Audio features (EQ, loudness normalization, volume boost) due to Safari MSE incompatibility
- Fixed 13 missing settings defaults for new installs
- Removed stale tbShowVolBoost default
- Fixed toolbar preview using emoji instead of SVG icons
- Fixed Reset button stretching to full width
