# Specification Document: Web-Based Linux IPTV Playlist Manager with Automated Nightly Validation

---

## Executive Summary

This specification details the architecture and comprehensive design for a modern web-based application to manage, aggregate, clean, and deliver IPTV M3U playlists from a Linux server. The proposed solution provides an intuitive user interface for playlist management, aggregates multiple IPTV sources, and performs nightly, automated validation—removing dead streams and duplicates to ensure a seamless, up-to-date IPTV experience for client devices on the same network. The system leverages robust open-source technologies, adheres to security and deployment best practices, and is designed to be extensible and maintainable.

---

## Table: Key Components and Their Roles

| Component                   | Primary Role                                                              | Technology/Frameworks                   |
| --------------------------- | ------------------------------------------------------------------------- | --------------------------------------- |
| **Frontend UI**             | User interaction, playlist upload, channel management, feedback on issues | React.js, Bootstrap, Vue.js (alt)       |
| **Backend App Server**      | Business logic, playlist aggregation, REST APIs, orchestrator             | Python (Flask/FastAPI), Node.js, Django |
| **M3U Parser/Generator**    | Robustly parse, merge, deduplicate, and generate M3U playlists            | Python m3u8, m3u8-parser (NodeJS)       |
| **Validation Engine**       | Validate live stream URLs, remove dead/duplicate channels, update logs    | Requests+concurrency, FFmpeg, custom    |
| **Nightly Scheduler**       | Automates nightly validation and cleaning workflow                        | systemd timers, cron                    |
| **Data Storage**            | Configuration/data persistency (user, playlists, logs, etc.)              | SQLite, PostgreSQL, Filesystem JSON     |
| **Authentication/Security** | Secures app and API endpoints, restricts access                           | JWT/OAuth2/Basic Auth, HTTPS, CORS      |
| **Containerization/Deploy** | Streamlined deployment, scaling, environment isolation                    | Docker, docker-compose                  |
| **Logging & Monitoring**    | Track app health, errors, validation status                               | Python logging, Prometheus, Grafana     |
| **API Interface**           | Enables integration (e.g., trigger validation, webhooks)                  | RESTful API (Flask/FastAPI/Express)     |

Each component is further elaborated in the sections below, with considerations for open-source alternatives, configuration, and scaling.

---

## Architecture Overview

A layered architecture ensures clear separation between user interaction, business logic, M3U handling, and system operations:

- **Frontend Layer:** Provides a responsive and intuitive interface for uploading playlists, managing channels, and reviewing cleaning results.
- **API Layer:** Exposes all playlist and channel management functions, validation reporting, and settings through RESTful endpoints.
- **Core Logic Layer:** Central engine for playlist aggregation, parsing, deduplication, and cleaning. Composed of modular subsystems for robustness.
- **Persistence Layer:** Stores user preferences, playlist links, validation logs, and application settings—favorably using SQLite for simplicity and portability.
- **System Services Layer:** Handles scheduled tasks (via systemd or cron), log rotation, and system integrations.
- **Deployment Layer:** Containerized via Docker for straightforward deployment and high environmental consistency.

This architecture draws upon lessons learned and capabilities of leading open-source systems such as [M3U_Manager-v3](https://github.com/rafikb/M3U_Manager-v3), hmlendea’s [iptv-playlist-aggregator](https://github.com/hmlendea/iptv-playlist-aggregator), and [m3u-playlist-cleaner](https://github.com/SeanRiggs/m3u-playlist-cleaner).

---

## Technology and Framework Choices

### Backend Frameworks

- **Python (Flask/FastAPI):** 
  - Lightweight, high-performance, and popular for RESTful APIs and scriptable automation.
  - Easy integration with m3u8 parsing, validation scripts, and robust scheduler logic via the threading, asyncio, or concurrent.futures modules.
  - Well-suited for background jobs and containerized deployments.
- **Node.js/Express:** 
  - Chosen for applications already invested in the JavaScript ecosystem; offers fast async operations and compatibility with npm-based IPTV and playlist utilities (e.g., m3u8-parser, express-basic-auth).
- **Django:** 
  - Suitable for more monolithic, enterprise-scale web apps with built-in admin, ORM, and robust security features.

**Justification:** Projects such as [iptv-manager (Flask)](https://github.com/bjakushka/iptv-manager), [IPTV-Solution (Django)](https://github.com/coach1988/IPTV-Solution), and m3u-merger demonstrate success in Python for manipulating M3U playlists with persistence and scheduling needs.

### Frontend UI Technologies

- **React.js:** 
  - Recommended for rich, interactive, modular UI. Large component ecosystem, excellent for forms, controls, modal feedback, and live status.
- **Vue.js:** 
  - More lightweight, great for rapidly building simpler admin dashboards.
- **Bootstrap:** 
  - For layout, grid system, mobile responsiveness, and form controls.
  
**User Interface Examples:** Multiple UI/UX concepts for IPTV management are available as inspiration on Behance and other design platforms, emphasizing clean layouts, intuitive grouping, and rapid feedback.

### M3U Playlist Libraries

- **Python:**
  - [m3u8 (PyPI)](https://pypi.org/project/m3u8/), [M3UManager (NuGet)](https://www.nuget.org/packages/M3UManager), custom parsers.
- **Node.js:**
  - [m3u8-parser (npm)](https://www.npmjs.com/package/m3u8-parser).
- **Go:** 
  - [m3ucat](https://github.com/nadiamoe/m3ucat) for command-line merging/deduplication.

These libraries parse, modify, and generate standards-compliant M3U files with strong support for IPTV-specific tags (#EXTINF, tvg-id, group-title, etc.).

### Stream Validation/Testing Tools

- **Standard Python concurrent HTTP checkers:** e.g., requests, aiohttp, concurrent.futures for parallel validation.
- **FFmpeg:** To probe streams beyond HEAD/GET (checking for playable audio/video codecs, not just HTTP 200).
- **M3U Playlist Cleaners/Scrubbers:** [m3u-playlist-cleaner](https://github.com/SeanRiggs/m3u-playlist-cleaner), [IPTV-M3U-Validator](https://github.com/binuengoor/IPTV-M3U-Validator).

### Data Storage

- **SQLite:** Default for server-side state (user prefs, playlist configs, logs, dedup info). Use a simple schema with user info, playlists, and records of deleted/cleaned channels.
- **Filesystem JSON:** For small-scale deployments, user and state data can be kept in JSON files.
- **PostgreSQL/MongoDB:** For scaling up, advanced query requirements, or collaborative/multi-user setups.

### Scheduling (Nightly Validation)

- **systemd timers/services:** Modern, robust, event-logged scheduling for Linux systems.
- **cron:** Traditional, fast setup through crontab; systemd preferred for its recovery and logging options.

### Containerization and Deployment

- **Docker:** Ubiquitous, supports multi-platform (amd64, arm64), repeatable deployment.
- **docker-compose:** For multi-container orchestration, e.g., app, reverse proxy, database.

### Logging and Monitoring

- **Prometheus:** Offers application-wide metrics, health, and alerting; ideal for more advanced setups, especially with Grafana for dashboards.
- **Python logging module:** For application and validation logs.
- **Log rotation:** Managed either by the app or logrotate/systemd.

### Security & Authentication

- **JWT tokens:** For user login to the UI/API (stateless, robust, supports granular access).
- **HTTPS/TLS:** Strong recommendation; use Let’s Encrypt for SSL certificates.
- **CORS policy:** Restricts API access to trusted clients.
- **Basic Auth:** As a fallback for simple local networks.
- **Reverse proxy:** Optionally use Traefik or nginx as a secure HTTP(S) gateway.
- **Container isolation:** As a best practice for security and deployment.

---

## User Interface Design

### Functional UI Requirements

- **Add M3U Playlist**: Upload file or paste URL; supports playlist naming and group classification.
- **List All Playlists and Channels**: Paginated view with filters (by group, provider, channel name), status indicators for validity.
- **Edit Channel/Stream Data**: Change name, logo, group, or stream URL; allow adding multiple URLs per channel.
- **Unified Playlist Preview/Download**: Displays the final clean playlist, exportable as .m3u (and optionally as JSON).
- **Status and Logs**: Exposes last validation time, broken/removed channel list, and change logs.
- **Manual Revalidate**: Trigger an immediate cleaning job.
- **Settings / Nightly Job Configuration**: Set update intervals, validation time, retry parameters.

### UI/UX Best Practices

- **Responsive:** Mobile-first; works on tablets, desktops, smart TVs.
- **Feedback:** Progress bars or spinner animations for long-running operations (playlist aggregation/validation).
- **Accessibility:** High contrast, ARIA roles, keyboard navigation, for inclusive usability.
- **Error Handling:** Clear, descriptive error messages for failed uploads, format errors, or external connectivity problems.
- **Theming:** Optional dark/light mode toggles, favicon, and support for custom logos.

**Reference UIs:** [Behance IPTV UI Examples](https://www.behance.net/search/projects/iptv%20apps%20ui%20design), [HogoNext IPTV UI Customization Guide](https://hogonext.com/how-to-create-and-customize-your-iptv-user-interface/).

---

## Backend Logic & Workflows

### Playlist Ingestion

1. **Receive playlist links/files** via API (with permission check).
2. **Parse** each playlist, extract all channels, and standardize metadata (#EXTINF, logos, tvg-id, group-title).
3. **Normalize** streams (trim whitespace, canonicalize group/channel names, resolve indirect links if needed).
4. **Aggregate** into a temporary in-memory structure or database; map channels by a suitable deduplication key (e.g., "channel name + group + stream URL").

### Deduplication

- **Key Principle:** Remove channels that have an identical stream URL or the same name/group and are functionally duplicates, preferring:
  - Streams with working statuses (from previous validations).
  - Higher resolution or lower latency streams (basis for ranking).
- **Algorithm:** Use hashmaps for stream URLs; track seen channel names and merge metadata (logo, tvg, group).

**Reference algorithm:** m3u-merger combines streams by URL, removing duplicates, and preserves all metadata.

### Nightly Validation Process

- **Scheduling:** Automated through systemd timers or cron tables, configurable by the user.
- **Operation:**
  1. Lock playlist datastore to avoid concurrent updates.
  2. For each channel, test the stream:
      - For HTTP/HTTPS, send a HEAD/GET and evaluate HTTP 2xx/3xx result.
      - For HLS/MPEG-TS, optionally launch ffprobe/ffmpeg for a few seconds to verify playable audio/video codecs.
      - Handle timeouts and connection errors distinctly.
  3. For each failed (dead) stream, mark for deletion or demotion (user-configurable: e.g., retain but disable).
  4. Remove or annotate duplicate channels.
  5. Log actions, report removed/dead streams in a persistent file and optionally through the UI.
  6. Write a fresh, unified .m3u file for use by downstream IPTV clients.
- **Output:** Playlist at a configurable URL ("http(s)://server:PORT/playlist.m3u") for the IPTV client.
- **Advanced:** Allow custom pre/post-validation hooks for advanced users (e.g., run a custom script or notify via email upon cleanup completion).

**Validation Tools:** [m3u-playlist-cleaner](https://github.com/SeanRiggs/m3u-playlist-cleaner), [IPTV-M3U-Validator](https://github.com/binuengoor/IPTV-M3U-Validator), and [Stream Checker utilities](https://github.com/eyaadh/IPTV-Stream-Checker) are proven technologies for such tasks.

### Error Handling

- **Partial/Temporary Failures:** Mark as "inactive"; retain for N validation cycles before final removal (user-configurable).
- **Geo-blocking/403s:** Optionally detect and flag streams that may require VPN or specific headers; inform user directly in UI/logs.
- **Malformed Entries:** Log dropped/parsing-failed lines, display in the UI with suggested corrections.

---

## Data Storage and Management

- **User/Playlist Config Table:** Stores each playlist’s source (file/upload/URL), group info, and metadata.
- **Channel Table:** Unique key on "channel name + group", with fields for all relevant metadata, raw/source URLs, and working status.
- **Validation Log Table:** Detailed entry for each validation run (time, action, removed and working totals, warnings).
- **User Accounts/Sessions Table:** For authentication, session expiration tracking, and permission level.

In minimal setups, these are simple SQLite tables with basic indices for fast lookup.

---

## Containerization & Deployment

- **Dockerfile:** 
  - Installs OS dependencies (Python/Node, FFmpeg, m3u8-parser libs).
  - Copies app source.
  - Entrypoint runs the backend server and, if configured, the nightly validator.
- **docker-compose.yml:** 
  - Multi-service: web server, reverse proxy (nginx/Caddy/Traefik), and data volume.
  - Health checks for application and validation status.

**Multi-Platform Testing:** Supports both amd64 and arm64 builds for wide server compatibility (including Raspberry Pi).

**Example:** [tvapp2](https://github.com/TheBinaryNinja/tvapp2) and [streamdock](https://github.com/limmer55/streamdock) document Docker deployment patterns for similar IPTV playlist applications.

---

## Logging, Metrics, and Monitoring

- **Validation Logs:** Output to both UI and a file (validator.log, latest X runs visible via the frontend).
- **System/Access Logs:** Standard server logging (access time, IP, operation).
- **Metrics Export:** Prometheus-compatible endpoint for health checks and statistics, with best-practice labels and error counters.
- **Real-Time Monitoring:** Prometheus and Grafana integration advised for larger deployments.

---

## Security and Authentication

- **JWT Authentication:** For all user and API access; tokens short-lived, refresh mechanism built-in for persistent sessions. Follows best practices as per Flask-JWT-Extended or similar tooling.
- **Role-Based Access:** Admin vs. viewer/user classes for larger/multi-user setups.
- **Password/Session Management:** Secure password hashing, force HTTPS.
- **Basic Auth Fallback:** Fast intranet deployments can use express-basic-auth or Flask-HTTPAuth for a quick secure start.
- **CORS:** Restrict to local subnet or configure as necessary for remote admin access.

---

## Existing Solutions and Open-Source Inspirations

- **[M3UIPTV Plugin (Enigma2)](https://www.linuxsat-support.com/thread/159610-m3uiptv-plugin-for-iptv-managment/):** Deeply integrated playlist and EPG management for set-top box, supports M3U/M3U8, dynamic URLs, EPG import, catchup, etc.
- **[M3U_Manager-v3](https://github.com/rafikb/M3U_Manager-v3):** Web-based app for channel management, playlist import/export, real-time validation, smart/tag-based filtering—proved lightweight effectiveness for personal/server use.
- **[m3u-merger](https://github.com/bobbymaher/m3u-merger):** Set of Python scripts for playlist download, combination, deduplication, and channel testing.
- **[iptv-playlist-aggregator (C#)](https://github.com/hmlendea/iptv-playlist-aggregator):** Multi-source ingest, matching and merging, running as a background Linux service via systemd service/timer.
- **[M3U Playlist Cleaner & Scrubber](https://github.com/SeanRiggs/m3u-playlist-cleaner):** Docker-packaged playlist cleaner for validation, deduplication; logs all cleaning operations to a persistent log file—demonstrates the ideal separation of playlist manipulation from the main application.

The landscape shows a clear need for a generic, customizable, web-based, automatic cleaning and management solution with Docker support, extensible to fit a variety of user requirements.

---

## Advanced/Optional Features

For extensible growth and advanced users:

- **EPG (Electronic Program Guide) Integration:** Import and map EPG data from XMLTV providers for channel metadata enrichment.
- **Transcoding Option:** Launch ffmpeg-proxy for formats not supported by all clients or for bandwidth optimization on slower networks.
- **Notifications:** Email, Telegram, or Pushbullet integration for validation results or playlist status changes.
- **Webhooks:** Trigger events on successful playlist cleaning, or when a threshold of dead links is reached.
- **Audit Trail:** Record all playlist updates, user actions, and cleaning history for compliance or troubleshooting.
- **Reverse Proxy/Integration:** e.g. [xTeVe](https://github.com/xteve-project/xTeVe) for compatibility with Plex/Jellyfin/Emby or [Threadfin](https://github.com/Threadfin/Threadfin).
- **Metrics-Driven Alerting:** Set up scheduled alerts for high rates of dead streams or validation failures via Prometheus/Grafana or Dynatrace.

---

## Example Nightly Validation Flow

1. **Scheduled trigger** via systemd timer at 02:00 AM.
2. **Lock database** for exclusive writing or pause frontend edits.
3. **Aggregate all playlist sources** (URLs and local uploads).
4. **Parse and unify playlist channels** via m3u8, cleaning extraneous formatting.
5. **Deduplicate** channels by URL and title.
6. **Validate each stream** (HEAD/GET/optionally ffprobe), up to 10/20 streams concurrently for speed.
7. **Mark broken/timeout channels**. If a fallback/alternative URL is present, prefer or attempt it.
8. **Compose new M3U** with all valid, deduplicated channels.
9. **Write output playlist** to the app’s static directory and to a well-known URL.
10. **Log** the process—list failed and removed streams, stats summary to validator.log and the database.
11. **Notify** users/admin if broken channels exceed a user-defined threshold or at every scheduled run (optional).
12. **Unlock resources**, resume frontend.

---

## Deployment Steps (Example)

1. **Clone repository**; edit a `config.yaml` or use UI for environment settings (paths, schedule times, admin credentials).
2. **Build and run Docker container(s)** (`docker-compose up -d`), ensuring mapped volumes for data and config are in place.
3. **Set up systemd timer** inside the container or host, as appropriate.
4. **Access UI** on `https://<server-ip>:PORT/`; log in with admin credentials.
5. **Upload playlist(s) or enter URLs** via the web UI.
6. **Configure nightly validation**—default 2:00 AM—or test manually.
7. **Point your IPTV client** to `http(s)://<server-ip>:PORT/playlist.m3u`.
8. **Review cleaning logs** via UI or validator.log for transparency.

---

## Security Hardening (for Production)

- Enforce password/secret key of sufficient entropy; disable default passwords on deployment.
- Run under least-privilege system accounts; avoid `root` when possible.
- Restrict firewall access to management ports; optionally proxy UI through nginx with TLS.
- Regularly update dependencies and Docker base images for security patches.
- Configure log rotation and retain only the last N days/weeks of logs.

---

## Extensibility and Maintenance

- Modular design: Each major function (parsing, aggregation, validation, UI, logging) confined in a separate module/package for ease of updates.
- Extensive logging and error reporting for self-diagnosis.
- Configure cleaning/validation parameters via UI for flexibility.
- Open API endpoints for third-party or local automation.
- Community-driven: Leverage active open-source components and document APIs for plugin integrations.

---

## Conclusion

The outlined solution creates a maintainable, robust, and extensible application for managing IPTV playlists on a Linux server, featuring:

- A modern, responsive web UI for managing and reviewing playlists.
- Aggregation and deduplication from multiple sources.
- Automatic nightly cleanup—validating streams, removing broken links, and ensuring only working channels are available for downstream clients.
- Security and monitoring features designed for in-home, business, or small community deployment.
- Open, composable architecture using established open-source tools, Docker containerization, and systemd-based scheduling for reliability.

By following the current best practices, proven patterns from the referenced open-source projects, and paying careful attention to security and usability, this application can provide a rock-solid backbone for IPTV aficionados and server administrators alike to deliver a seamless, always-working media streaming experience.

---

*This document references a wide range of publicly available technologies, frameworks, and community knowledge bases on Linux IPTV management, playlist aggregation, and web-based UI and backend development to ensure that each feature and design decision is solidly grounded in modern, real-world best practices.*
Great! I’m putting together a detailed specification for your Linux-based IPTV playlist manager. It will cover the web UI for adding M3U files, the backend logic for merging and validating streams, and the nightly cleanup process to ensure your IPTV client always has a reliable playlist. This will take me several minutes, so feel free to step away—I’ll keep working in the background. Your report will be saved right here in this conversation.
