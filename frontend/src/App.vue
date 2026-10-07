<template>
  <div class="app-shell">
    <!-- Header -->
    <header class="app-header" id="app-header">
      <div class="header-inner">
        <div class="header-left">
          <img src="/logo.jpg" alt="VisionQuery Logo" class="header-logo" />
          <div>
            <h1 class="header-title">VisionQuery</h1>
            <p class="header-subtitle">CCTV / Video Search & Retrieval</p>
          </div>
        </div>
        <div class="header-right">
          <button
            class="connection-indicator-btn"
            :class="computer1Status"
            @click="openRemoteConfigModal"
            title="Click to configure Computer 1 address (LAN / Remote / Another City)"
          >
            <span class="conn-dot"></span>
            <span class="conn-label">Computer 1: {{ computer1StatusText }}</span>
            <span class="conn-edit-icon">⚙️</span>
          </button>
          <div class="cache-indicator" :class="{ stale: isCacheStale }">
            <span class="cache-dot"></span>
            <span class="cache-label">{{ cacheStatusText }}</span>
          </div>
          <button
            id="refresh-events-btn"
            class="refresh-btn"
            :class="{ spinning: refreshing }"
            @click="refreshEvents"
            :disabled="refreshing"
          >
            <span class="refresh-icon">⟳</span>
            Refresh Events
          </button>
        </div>
      </div>
    </header>

    <!-- Main Content -->
    <main class="main-content">
      <!-- Filter Panel -->
      <aside class="filter-panel" id="filter-panel">
        <div class="filter-panel-header">
          <h2 class="filter-title">🔍 Filters</h2>
          <button class="filter-clear-btn" @click="clearFilters" v-if="hasActiveFilters">
            ✕ Clear All
          </button>
        </div>

        <!-- Object Type -->
        <div class="filter-group">
          <label class="filter-label" for="filter-object-type">Object Type</label>
          <select id="filter-object-type" class="filter-select" v-model="filters.object_type">
            <option value="">All Types</option>
            <option v-for="t in uniqueObjectTypes" :key="t" :value="t">{{ t }}</option>
          </select>
        </div>

        <!-- Camera Name -->
        <div class="filter-group">
          <label class="filter-label" for="filter-camera-name">Camera</label>
          <select id="filter-camera-name" class="filter-select" v-model="filters.camera_name">
            <option value="">All Cameras</option>
            <option v-for="c in uniqueCameraNames" :key="c" :value="c">{{ c }}</option>
          </select>
        </div>

        <!-- Source Type -->
        <div class="filter-group">
          <label class="filter-label" for="filter-source-type">Video Source</label>
          <select id="filter-source-type" class="filter-select" v-model="filters.source_type">
            <option value="">All Sources</option>
            <option value="uploaded">Uploaded Video</option>
            <option value="nvr">NVR / IP Camera</option>
          </select>
        </div>

        <!-- Event ID -->
        <div class="filter-group">
          <label class="filter-label" for="filter-event-id">Event ID</label>
          <input
            id="filter-event-id"
            class="filter-input"
            type="number"
            placeholder="e.g. 11"
            v-model="filters.event_id"
          />
        </div>

        <!-- Track ID -->
        <div class="filter-group">
          <label class="filter-label" for="filter-track-id">Track ID</label>
          <input
            id="filter-track-id"
            class="filter-input"
            type="number"
            placeholder="e.g. 1"
            v-model="filters.track_id"
          />
        </div>

        <!-- Shirt Color -->
        <div class="filter-group" v-if="!filters.object_type || filters.object_type === 'person'">
          <label class="filter-label" for="filter-shirt">Shirt Color</label>
          <select id="filter-shirt" class="filter-select" v-model="filters.shirt">
            <option value="">Any</option>
            <option v-for="c in uniqueShirtColors" :key="c" :value="c">{{ c }}</option>
          </select>
        </div>

        <!-- Pants Color -->
        <div class="filter-group" v-if="!filters.object_type || filters.object_type === 'person'">
          <label class="filter-label" for="filter-pants">Pants Color</label>
          <select id="filter-pants" class="filter-select" v-model="filters.pants">
            <option value="">Any</option>
            <option v-for="c in uniquePantsColors" :key="c" :value="c">{{ c }}</option>
          </select>
        </div>

        <!-- Time Range -->
        <div class="filter-group">
          <label class="filter-label" for="filter-start-after">Start After</label>
          <input
            id="filter-start-after"
            class="filter-input"
            type="datetime-local"
            v-model="filters.start_after"
          />
        </div>

        <div class="filter-group">
          <label class="filter-label" for="filter-start-before">Start Before</label>
          <input
            id="filter-start-before"
            class="filter-input"
            type="datetime-local"
            v-model="filters.start_before"
          />
        </div>

        <!-- Active Filters Summary -->
        <div class="active-filters" v-if="hasActiveFilters">
          <div class="active-filter-tag" v-for="tag in activeFilterTags" :key="tag.key">
            <span>{{ tag.label }}</span>
            <button class="tag-remove" @click="removeFilter(tag.key)">✕</button>
          </div>
        </div>
      </aside>

      <!-- Events Grid -->
      <section class="events-section" id="events-section">
        <!-- Natural Language Prompt Search Bar -->
        <div class="prompt-search-bar" id="prompt-search-bar">
          <div class="prompt-input-wrapper">
            <span class="prompt-icon">🤖</span>
            <input
              id="prompt-input"
              class="prompt-input"
              type="text"
              v-model="searchQuery"
              placeholder="Ask in natural language (e.g. 'person in red shirt near front gate' or 'car after 8 PM')..."
              @keyup.enter="performAiSearch"
            />
            <button
              v-if="searchQuery"
              class="prompt-clear-btn"
              @click="clearAiSearch"
              title="Clear search prompt"
            >
              ✕
            </button>
            <button
              id="prompt-submit-btn"
              class="prompt-submit-btn"
              :class="{ loading: aiSearchLoading }"
              @click="performAiSearch"
              :disabled="aiSearchLoading || !searchQuery.trim()"
            >
              <span v-if="aiSearchLoading" class="btn-spinner"></span>
              <span v-else>Search</span>
            </button>
          </div>

          <!-- Quick Prompt Chips -->
          <div class="quick-prompts">
            <span class="quick-prompt-label">Try asking:</span>
            <button
              v-for="preset in quickPresets"
              :key="preset"
              class="quick-chip"
              @click="runPresetPrompt(preset)"
            >
              "{{ preset }}"
            </button>
          </div>

          <!-- AI Search Intent Feedback Badge -->
          <div v-if="aiSearchIntent" class="intent-banner">
            <div class="intent-info">
              <span class="intent-title">✨ Extracted Intent:</span>
              <span class="intent-badge" v-if="aiSearchIntent.object_type">Type: <strong>{{ aiSearchIntent.object_type }}</strong></span>
              <span class="intent-badge" v-if="aiSearchIntent.shirt">Shirt: <strong>{{ aiSearchIntent.shirt }}</strong></span>
              <span class="intent-badge" v-if="aiSearchIntent.pants">Pants: <strong>{{ aiSearchIntent.pants }}</strong></span>
              <span class="intent-badge" v-if="aiSearchIntent.camera_name">Camera: <strong>{{ aiSearchIntent.camera_name }}</strong></span>
              <span class="intent-badge" v-if="aiSearchIntent.time_after">After: <strong>{{ aiSearchIntent.time_after }}</strong></span>
              <span class="intent-badge" v-if="aiSearchIntent.time_before">Before: <strong>{{ aiSearchIntent.time_before }}</strong></span>
              <span class="intent-badge" v-if="aiSearchIntent.track_id">Track: <strong>{{ aiSearchIntent.track_id }}</strong></span>
              <span class="intent-badge fallback" v-if="aiSearchUsedFallback">Keyword Engine</span>
              <span class="intent-badge llm" v-else>Ollama LLM</span>
            </div>
            <button class="reset-search-link" @click="clearAiSearch">Show All Events</button>
          </div>
        </div>

        <!-- Stats Bar -->
        <div class="stats-bar">
          <div class="stat-chip">
            <span class="stat-value">{{ filteredEvents.length }}</span>
            <span class="stat-label">{{ filteredEvents.length === 1 ? 'Event' : 'Events' }}</span>
          </div>
          <div class="stat-chip persons">
            <span class="stat-value">{{ personCount }}</span>
            <span class="stat-label">Persons</span>
          </div>
          <div class="stat-chip vehicles">
            <span class="stat-value">{{ vehicleCount }}</span>
            <span class="stat-label">Vehicles</span>
          </div>
          <div class="stat-chip uploaded">
            <span class="stat-value">{{ uploadedCount }}</span>
            <span class="stat-label">Uploaded</span>
          </div>
          <div class="stat-chip nvr">
            <span class="stat-value">{{ nvrCount }}</span>
            <span class="stat-label">NVR</span>
          </div>
        </div>

        <!-- Loading State -->
        <div v-if="loading" class="loading-state">
          <div class="loading-spinner-large"></div>
          <p>Loading events from Computer 1...</p>
        </div>

        <!-- Error State -->
        <div v-else-if="error" class="error-state">
          <div class="error-icon">⚠️</div>
          <h3>Connection Error</h3>
          <p>{{ error }}</p>
          <button class="retry-btn" @click="refreshEvents">Retry</button>
        </div>

        <!-- Empty State -->
        <div v-else-if="filteredEvents.length === 0 && allEvents.length > 0" class="empty-state">
          <div class="empty-icon">🔍</div>
          <h3>No matching events</h3>
          <p>Try adjusting your filters to find events.</p>
          <button class="retry-btn" @click="clearFilters">Clear Filters</button>
        </div>

        <div v-else-if="allEvents.length === 0" class="empty-state">
          <div class="empty-icon">📡</div>
          <h3>Waiting for events</h3>
          <p>No events in the pipeline yet. Events will appear here as the CV pipeline processes video.</p>
        </div>

        <!-- Events Grid -->
        <div v-else class="events-grid" id="events-grid">
          <EventCard
            v-for="event in filteredEvents"
            :key="event.event_id"
            :event="event"
            @view-details="openDetailModal"
          />
        </div>
      </section>
    </main>

    <!-- Detail Modal -->
    <div v-if="detailEvent" class="modal-overlay" @click.self="detailEvent = null">
      <div class="detail-modal">
        <button class="modal-close" @click="detailEvent = null">✕</button>
        <div class="modal-header">
          <div class="modal-type-badge" :class="detailEvent.object_type">
            {{ detailEvent.object_type === 'person' ? '🧍' : '🚗' }}
            {{ detailEvent.object_type }}
          </div>
          <div class="modal-ids">
            <span class="modal-id">Event #{{ detailEvent.event_id }}</span>
            <span class="modal-id">Track #{{ detailEvent.track_id }}</span>
            <span class="modal-id" v-if="detailEvent.camera_name">📷 {{ detailEvent.camera_name }}</span>
          </div>
        </div>

        <!-- Unified Video Player (Renders for ALL events: Uploaded & NVR) -->
        <div class="modal-video-container">
          <video
            ref="videoPlayer"
            class="modal-video-player"
            controls
            autoplay
            preload="auto"
            :src="detailVideoUrl"
            @error="onVideoError"
            @loadeddata="onVideoLoadedData"
            @timeupdate="onVideoTimeUpdate"
          >
            Your browser does not support HTML5 video tag.
          </video>

          <div v-if="videoError" class="video-error-banner">
            ⚠️ Could not play video stream. Please check that video files are available.
          </div>

          <!-- Video Notice & Actions for Uploaded Videos -->
          <div class="video-notice" v-if="detailVideoSourceType === 'uploaded'">
            <div class="clip-info">
              <span class="clip-file">🎬 <strong>{{ detailShortFilename }}</strong></span>
              <span class="clip-badge source-uploaded">📁 Uploaded Video</span>
              <span class="clip-badge">
                ⏱ Clip: <strong>{{ formatTimeSec(clipStartSec) }}</strong> ➔ <strong>{{ formatTimeSec(clipEndSec) }}</strong> ({{ clipDurationSec }}s)
              </span>
            </div>
            <div class="clip-actions">
              <button class="clip-btn replay" @click="replayClip" title="Replay event clip">🔄 Replay Clip</button>
              <button
                class="clip-btn toggle"
                :class="{ unlocked: !enforceClipEnd }"
                @click="enforceClipEnd = !enforceClipEnd"
                :title="enforceClipEnd ? 'Stop at clip end time' : 'Play beyond clip end time'"
              >
                {{ enforceClipEnd ? '🔒 Clip Only' : '🔓 Full Video' }}
              </button>
            </div>
          </div>

          <!-- Video Notice & Actions for NVR Events -->
          <div class="video-notice" v-else>
            <div class="clip-info">
              <span class="clip-file">🎥 <strong>{{ detailEvent.camera_name || 'Camera ' + detailEvent.camera_id }}</strong></span>
              <span class="clip-badge" :class="detailVideoSourceType === 'nvr' ? 'source-nvr' : ''">
                🎥 {{ detailNvrManufacturer || 'NVR' }} Stream Preview
              </span>
              <span class="clip-badge">
                ⏱ {{ formatTimeSec(clipStartSec) }} ➔ {{ formatTimeSec(clipEndSec) }} ({{ clipDurationSec }}s)
              </span>
            </div>
            <div class="clip-actions">
              <button class="clip-btn replay" @click="replayClip" title="Replay event clip">🔄 Replay Clip</button>
              <button
                class="clip-btn toggle"
                :class="{ unlocked: !enforceClipEnd }"
                @click="enforceClipEnd = !enforceClipEnd"
                :title="enforceClipEnd ? 'Stop at clip end time' : 'Play beyond clip end time'"
              >
                {{ enforceClipEnd ? '🔒 Clip Only' : '🔓 Full Video' }}
              </button>
            </div>
          </div>

          <!-- NVR Stream Details Box (shown for NVR events below video player) -->
          <div class="nvr-playback-info" v-if="detailVideoSourceType === 'nvr'">
            <div class="nvr-header">
              <span class="nvr-icon">📡</span>
              <h3>NVR Stream Information</h3>
              <span class="nvr-manufacturer-badge">{{ detailNvrManufacturer }}</span>
            </div>
            <div class="nvr-details">
              <div class="nvr-field">
                <span class="nvr-field-label">NVR IP</span>
                <span class="nvr-field-value">{{ detailEvent.nvr_ip }}</span>
              </div>
              <div class="nvr-field">
                <span class="nvr-field-label">Channel</span>
                <span class="nvr-field-value">{{ detailEvent.nvr_channel }}</span>
              </div>
              <div class="nvr-field">
                <span class="nvr-field-label">Manufacturer</span>
                <span class="nvr-field-value">{{ detailNvrManufacturer }}</span>
              </div>
            </div>
            <div class="nvr-rtsp-url">
              <span class="nvr-field-label">RTSP Playback URL (For VLC / Network Stream)</span>
              <code class="rtsp-url-code">{{ detailRtspUrl || 'Not available' }}</code>
              <button
                v-if="detailRtspUrl"
                class="copy-rtsp-btn"
                @click="copyRtspUrl"
                :title="rtspCopied ? 'Copied!' : 'Copy RTSP URL'"
              >
                {{ rtspCopied ? '✅ Copied' : '📋 Copy URL' }}
              </button>
            </div>
            <div class="nvr-error" v-if="detailVideoSourceError">
              ⚠️ {{ detailVideoSourceError }}
            </div>
            <p class="nvr-hint">
              Browsers do not support RTSP directly, so simulated CCTV camera footage is playing above. Copy the RTSP URL to open the live stream in VLC.
            </p>
          </div>
        </div>

        <div class="modal-body">
          <div class="modal-field" v-if="detailEvent.camera_name">
            <span class="modal-field-label">Camera</span>
            <span class="modal-field-value">{{ detailEvent.camera_name }} (ID: {{ detailEvent.camera_id }})</span>
          </div>
          <div class="modal-field">
            <span class="modal-field-label">Start Time</span>
            <span class="modal-field-value">{{ detailEvent.start_time }}</span>
          </div>
          <div class="modal-field">
            <span class="modal-field-label">End Time</span>
            <span class="modal-field-value">{{ detailEvent.end_time }}</span>
          </div>
          <div class="modal-field">
            <span class="modal-field-label">Duration</span>
            <span class="modal-field-value">{{ computeDuration(detailEvent) }}</span>
          </div>
          <div class="modal-field" v-if="detailEvent.attributes && detailEvent.attributes.shirt">
            <span class="modal-field-label">Shirt</span>
            <span class="modal-field-value attr-color">
              <span class="color-swatch" :style="{ background: detailEvent.attributes.shirt }"></span>
              {{ detailEvent.attributes.shirt }}
            </span>
          </div>
          <div class="modal-field" v-if="detailEvent.attributes && detailEvent.attributes.pants">
            <span class="modal-field-label">Pants</span>
            <span class="modal-field-value attr-color">
              <span class="color-swatch" :style="{ background: detailEvent.attributes.pants }"></span>
              {{ detailEvent.attributes.pants }}
            </span>
          </div>
          <div class="modal-field">
            <span class="modal-field-label">Video Source</span>
            <span class="modal-field-value">
              <template v-if="detailVideoSourceType === 'uploaded'">📁 Uploaded ({{ detailShortFilename }})</template>
              <template v-else-if="detailVideoSourceType === 'nvr'">🎥 NVR ({{ detailNvrManufacturer }})</template>
              <template v-else class="muted">Not connected</template>
            </span>
          </div>
        </div>
        <div class="modal-json">
          <div class="json-header">Raw JSON</div>
          <pre class="json-body">{{ JSON.stringify(detailEventClean, null, 2) }}</pre>
        </div>
      </div>
    </div>

    <!-- Remote Connection Modal (Another City / Cloud Tunnel / VPN) -->
    <div v-if="showRemoteModal" class="modal-overlay" @click.self="showRemoteModal = false">
      <div class="remote-modal">
        <button class="modal-close" @click="showRemoteModal = false">✕</button>
        <div class="remote-modal-header">
          <span class="remote-icon">🌐</span>
          <div>
            <h3>Computer 1 Remote Connection</h3>
            <p>Connect to Computer 1 on LAN, across the internet, or in another city</p>
          </div>
        </div>

        <div class="remote-modal-body">
          <div class="current-status-banner" :class="computer1Status">
            <span class="conn-dot"></span>
            <div class="status-desc">
              <strong>Status: {{ computer1StatusText }}</strong>
              <span class="status-url">{{ currentComputer1Url || 'No URL configured' }}</span>
            </div>
          </div>

          <div class="form-group">
            <label class="form-label" for="remote-url-input">Computer 1 Address / URL</label>
            <div class="input-with-action">
              <input
                id="remote-url-input"
                class="remote-input"
                type="text"
                v-model="remoteUrlInput"
                placeholder="https://xxxx.ngrok-free.app or http://192.168.0.155:5000"
                @keyup.enter="saveRemoteConnection"
              />
              <button
                class="save-conn-btn"
                :class="{ loading: savingRemoteConfig }"
                @click="saveRemoteConnection"
                :disabled="savingRemoteConfig || !remoteUrlInput.trim()"
              >
                <span v-if="savingRemoteConfig" class="btn-spinner"></span>
                <span v-else>Connect & Save</span>
              </button>
            </div>
          </div>

          <div class="remote-presets">
            <span class="presets-label">Quick Presets:</span>
            <button class="preset-chip" @click="remoteUrlInput = 'http://192.168.0.155:5000'">
              🏠 LAN (192.168.0.155:5000)
            </button>
            <button class="preset-chip" @click="remoteUrlInput = 'http://localhost:5000'">
              💻 Same PC (localhost:5000)
            </button>
          </div>

          <div class="remote-instructions">
            <h4>💡 How to connect across different cities:</h4>
            <div class="instruction-grid">
              <div class="instruction-card">
                <strong>Method 1: Free Cloud Tunnel (Recommended & Easiest)</strong>
                <p>On Computer 1, run <code class="code-inline">ngrok http 5000</code> or Cloudflare Tunnel (<code class="code-inline">cloudflared tunnel --url http://localhost:5000</code>). Paste the public HTTPS URL above.</p>
              </div>
              <div class="instruction-card">
                <strong>Method 2: Virtual Mesh VPN (Tailscale / ZeroTier)</strong>
                <p>Install Tailscale on both computers. Enter Computer 1's Tailscale IP: <code class="code-inline">http://100.x.y.z:5000</code>.</p>
              </div>
              <div class="instruction-card">
                <strong>Method 3: Public IP & Port Forwarding</strong>
                <p>Forward port 5000 on Computer 1's router, and enter its public IP: <code class="code-inline">http://[PUBLIC_IP]:5000</code>.</p>
              </div>
            </div>
          </div>

          <div v-if="remoteSaveFeedback" class="remote-feedback" :class="remoteSaveFeedback.type">
            {{ remoteSaveFeedback.message }}
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script>
import EventCard from './components/EventCard.vue'

const API_BASE = 'http://localhost:5000'
const CACHE_TTL_MS = 60_000 // 60 seconds

export default {
  name: 'App',
  components: { EventCard },
  data() {
    return {
      allEvents: [],
      loading: false,
      refreshing: false,
      error: null,
      computer1Status: 'unknown',   // 'connected', 'unreachable', 'unknown'
      detailEvent: null,
      videoError: false,
      videoSrcFallback: false,
      clipStartSec: 0,
      clipEndSec: 0,
      clipDurationSec: 0,
      enforceClipEnd: true,
      hasSeekedToStart: false,
      rtspCopied: false,
      cacheTimestamp: null,
      showRemoteModal: false,
      remoteUrlInput: '',
      currentComputer1Url: '',
      savingRemoteConfig: false,
      remoteSaveFeedback: null,
      searchQuery: '',
      aiSearchLoading: false,
      aiSearchResults: null,
      aiSearchIntent: null,
      aiSearchUsedFallback: false,
      quickPresets: [
        'person in red shirt',
        'person near front gate',
        'person with blue pants',
        'car',
      ],
      filters: {
        object_type: '',
        camera_name: '',
        source_type: '',
        event_id: '',
        track_id: '',
        shirt: '',
        pants: '',
        start_after: '',
        start_before: '',
      },
    }
  },
  computed: {
    computer1StatusText() {
      if (this.computer1Status === 'connected') return 'Connected'
      if (this.computer1Status === 'unreachable') return 'Unreachable'
      return 'Checking...'
    },
    isCacheStale() {
      if (!this.cacheTimestamp) return true
      return Date.now() - this.cacheTimestamp > CACHE_TTL_MS
    },
    cacheStatusText() {
      if (!this.cacheTimestamp) return 'No data loaded'
      const ago = Math.round((Date.now() - this.cacheTimestamp) / 1000)
      if (ago < 5) return 'Just refreshed'
      if (ago < 60) return `Cached ${ago}s ago`
      return `Cache stale (${Math.round(ago / 60)}m ago)`
    },
    filteredEvents() {
      let events = this.aiSearchResults !== null ? [...this.aiSearchResults] : [...this.allEvents]

      if (this.filters.object_type) {
        events = events.filter(e => e.object_type === this.filters.object_type)
      }
      if (this.filters.camera_name) {
        events = events.filter(e => e.camera_name === this.filters.camera_name)
      }
      if (this.filters.source_type) {
        if (this.filters.source_type === 'uploaded') {
          events = events.filter(e => !!e.video_file)
        } else if (this.filters.source_type === 'nvr') {
          events = events.filter(e => !!e.nvr_ip)
        }
      }
      if (this.filters.event_id) {
        const id = parseInt(this.filters.event_id)
        if (!isNaN(id)) {
          events = events.filter(e => e.event_id === id)
        }
      }
      if (this.filters.track_id) {
        const id = parseInt(this.filters.track_id)
        if (!isNaN(id)) {
          events = events.filter(e => e.track_id === id)
        }
      }
      if (this.filters.shirt) {
        events = events.filter(e =>
          e.attributes && e.attributes.shirt &&
          e.attributes.shirt.toLowerCase() === this.filters.shirt.toLowerCase()
        )
      }
      if (this.filters.pants) {
        events = events.filter(e =>
          e.attributes && e.attributes.pants &&
          e.attributes.pants.toLowerCase() === this.filters.pants.toLowerCase()
        )
      }
      if (this.filters.start_after) {
        const after = new Date(this.filters.start_after)
        events = events.filter(e => {
          // Skip relative timestamps for date filtering
          if (this.isRelativeTimestamp(e.start_time)) return true
          const d = new Date(e.start_time.replace(' ', 'T'))
          return d >= after
        })
      }
      if (this.filters.start_before) {
        const before = new Date(this.filters.start_before)
        events = events.filter(e => {
          if (this.isRelativeTimestamp(e.start_time)) return true
          const d = new Date(e.start_time.replace(' ', 'T'))
          return d <= before
        })
      }

      return events
    },
    personCount() {
      return this.filteredEvents.filter(e => e.object_type === 'person').length
    },
    vehicleCount() {
      return this.filteredEvents.filter(e => e.object_type !== 'person').length
    },
    uploadedCount() {
      return this.filteredEvents.filter(e => !!e.video_file).length
    },
    nvrCount() {
      return this.filteredEvents.filter(e => !!e.nvr_ip && !e.video_file).length
    },
    uniqueObjectTypes() {
      return [...new Set(this.allEvents.map(e => e.object_type))].sort()
    },
    uniqueCameraNames() {
      return [...new Set(
        this.allEvents
          .filter(e => e.camera_name)
          .map(e => e.camera_name)
      )].sort()
    },
    uniqueShirtColors() {
      return [...new Set(
        this.allEvents
          .filter(e => e.attributes && e.attributes.shirt)
          .map(e => e.attributes.shirt)
      )].sort()
    },
    uniquePantsColors() {
      return [...new Set(
        this.allEvents
          .filter(e => e.attributes && e.attributes.pants)
          .map(e => e.attributes.pants)
      )].sort()
    },
    hasActiveFilters() {
      return Object.values(this.filters).some(v => v !== '')
    },
    activeFilterTags() {
      const tags = []
      if (this.filters.object_type) tags.push({ key: 'object_type', label: `Type: ${this.filters.object_type}` })
      if (this.filters.camera_name) tags.push({ key: 'camera_name', label: `Camera: ${this.filters.camera_name}` })
      if (this.filters.source_type) tags.push({ key: 'source_type', label: `Source: ${this.filters.source_type}` })
      if (this.filters.event_id) tags.push({ key: 'event_id', label: `Event #${this.filters.event_id}` })
      if (this.filters.track_id) tags.push({ key: 'track_id', label: `Track #${this.filters.track_id}` })
      if (this.filters.shirt) tags.push({ key: 'shirt', label: `Shirt: ${this.filters.shirt}` })
      if (this.filters.pants) tags.push({ key: 'pants', label: `Pants: ${this.filters.pants}` })
      if (this.filters.start_after) tags.push({ key: 'start_after', label: `After: ${this.filters.start_after}` })
      if (this.filters.start_before) tags.push({ key: 'start_before', label: `Before: ${this.filters.start_before}` })
      return tags
    },
    // ── Detail modal computed ──
    detailVideoSource() {
      if (!this.detailEvent) return null
      return this.detailEvent.video_source || null
    },
    detailVideoSourceType() {
      return this.detailVideoSource?.source_type || 'unsupported'
    },
    detailVideoUrl() {
      if (this.videoSrcFallback) return '/dummy.mp4'
      if (!this.detailEvent) return '/dummy.mp4'
      if (this.detailVideoSourceType === 'uploaded') {
        const url = this.detailVideoSource?.video_url || ''
        if (url) {
          const filename = url.split('/').pop()
          return `${API_BASE}/proxy/video/${filename}`
        }
      }
      return '/dummy.mp4'
    },
    detailRtspUrl() {
      return this.detailVideoSource?.rtsp_url || ''
    },
    detailNvrManufacturer() {
      const mfr = this.detailVideoSource?.manufacturer || ''
      return mfr ? mfr.charAt(0).toUpperCase() + mfr.slice(1) : 'Unknown'
    },
    detailVideoSourceError() {
      return this.detailVideoSource?.error || ''
    },
    detailShortFilename() {
      if (!this.detailEvent || !this.detailEvent.video_file) return ''
      const parts = this.detailEvent.video_file.split('/')
      return parts[parts.length - 1]
    },
    detailEventClean() {
      // Return event without the enriched video_source for cleaner JSON display
      if (!this.detailEvent) return {}
      const { video_source, ...clean } = this.detailEvent
      return clean
    },
  },
  methods: {
    isRelativeTimestamp(dt) {
      if (!dt) return false
      return dt.length <= 8 && dt.includes(':') && !dt.includes('-')
    },
    async fetchEvents(force = false) {
      // Use cache if valid and not forcing
      if (!force && this.cacheTimestamp && !this.isCacheStale) {
        return
      }

      if (!this.cacheTimestamp) {
        this.loading = true
      }
      this.error = null

      try {
        const response = await fetch(`${API_BASE}/api/events`)
        if (!response.ok) {
          throw new Error(`Server error (${response.status})`)
        }
        const data = await response.json()
        this.allEvents = data.events || []
        this.cacheTimestamp = Date.now()

        // Check Computer 1 status from response
        this.computer1Status = data.source === 'computer_1' ? 'connected' : 'unreachable'
      } catch (err) {
        if (err.name === 'TypeError' && err.message.includes('fetch')) {
          this.error = 'Unable to connect to the backend server. Make sure Flask is running on http://localhost:5000'
        } else {
          this.error = err.message
        }
        this.computer1Status = 'unreachable'
      } finally {
        this.loading = false
        this.refreshing = false
      }
    },
    async performAiSearch() {
      const q = this.searchQuery.trim()
      if (!q) return

      this.aiSearchLoading = true
      this.error = null

      try {
        const response = await fetch(`${API_BASE}/api/search`, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ query: q }),
        })
        if (!response.ok) {
          throw new Error(`Search error (${response.status})`)
        }
        const data = await response.json()
        this.aiSearchResults = data.results || []
        this.aiSearchIntent = data.intent || {}
        this.aiSearchUsedFallback = !!data.used_fallback
      } catch (err) {
        this.error = `Search failed: ${err.message}`
      } finally {
        this.aiSearchLoading = false
      }
    },
    runPresetPrompt(preset) {
      this.searchQuery = preset
      this.performAiSearch()
    },
    clearAiSearch() {
      this.searchQuery = ''
      this.aiSearchResults = null
      this.aiSearchIntent = null
      this.aiSearchUsedFallback = false
    },
    async refreshEvents() {
      this.refreshing = true
      await this.fetchEvents(true)
    },
    clearFilters() {
      this.filters = {
        object_type: '',
        camera_name: '',
        source_type: '',
        event_id: '',
        track_id: '',
        shirt: '',
        pants: '',
        start_after: '',
        start_before: '',
      }
    },
    removeFilter(key) {
      this.filters[key] = ''
    },
    openDetailModal(event) {
      this.videoError = false
      this.videoSrcFallback = false
      this.detailEvent = event
      this.enforceClipEnd = true
      this.hasSeekedToStart = false
      this.rtspCopied = false

      const bounds = this.getClipBounds(event)
      this.clipStartSec = bounds.start
      this.clipEndSec = bounds.end
      this.clipDurationSec = Math.max(0, bounds.end - bounds.start)

      this.$nextTick(() => {
        const video = this.$refs.videoPlayer
        if (video) {
          video.currentTime = bounds.start
          video.play().catch(() => {})
        }
      })
    },
    getClipBounds(event) {
      if (!event) return { start: 0, end: 10 }

      // 1. Uploaded video with explicit seconds offset from backend
      const vs = event.video_source
      if (vs && vs.source_type === 'uploaded' && typeof vs.start_sec === 'number' && typeof vs.end_sec === 'number') {
        return { start: vs.start_sec, end: vs.end_sec }
      }

      // 2. Relative time offset (HH:MM:SS format, e.g. "00:00:29" - "00:00:33")
      if (this.isRelativeTimestamp(event.start_time)) {
        try {
          const sParts = event.start_time.split(':').map(Number)
          const eParts = event.end_time.split(':').map(Number)
          const startSec = (sParts[0] || 0) * 3600 + (sParts[1] || 0) * 60 + (sParts[2] || 0)
          const endSec = (eParts[0] || 0) * 3600 + (eParts[1] || 0) * 60 + (eParts[2] || 0)
          return { start: startSec, end: Math.max(startSec + 3, endSec) }
        } catch { /* ignore */ }
      }

      // 3. Wall-clock datetime (NVR events, e.g. "2026-10-05 20:55:08")
      try {
        const timeStrStart = event.start_time.includes(' ') ? event.start_time.split(' ')[1] : event.start_time
        const timeStrEnd = event.end_time.includes(' ') ? event.end_time.split(' ')[1] : event.end_time
        const sParts = timeStrStart.split(':').map(Number)
        const eParts = timeStrEnd.split(':').map(Number)
        const startSec = (sParts[0] || 0) * 3600 + (sParts[1] || 0) * 60 + (sParts[2] || 0)
        const endSec = (eParts[0] || 0) * 3600 + (eParts[1] || 0) * 60 + (eParts[2] || 0)
        return { start: startSec, end: Math.max(startSec + 3, endSec) }
      } catch {
        return { start: 0, end: 30 }
      }
    },
    onVideoLoadedData() {
      this.videoError = false
      const video = this.$refs.videoPlayer
      if (video && !this.hasSeekedToStart) {
        this.hasSeekedToStart = true
        if (video.duration && this.clipStartSec > video.duration) {
          video.currentTime = this.clipStartSec % Math.max(1, Math.floor(video.duration))
        } else {
          video.currentTime = this.clipStartSec
        }
        video.play().catch(() => {})
      }
    },
    onVideoTimeUpdate() {
      const video = this.$refs.videoPlayer
      if (!video) return
      if (this.enforceClipEnd && this.clipEndSec > this.clipStartSec) {
        if (video.currentTime >= this.clipEndSec) {
          video.pause()
          video.currentTime = this.clipEndSec
        }
      }
    },
    replayClip() {
      const video = this.$refs.videoPlayer
      if (video) {
        if (video.duration && this.clipStartSec > video.duration) {
          video.currentTime = this.clipStartSec % Math.max(1, Math.floor(video.duration))
        } else {
          video.currentTime = this.clipStartSec
        }
        video.play().catch(() => {})
      }
    },
    formatTimeSec(sec) {
      if (isNaN(sec) || sec < 0) return '00:00:00'
      const h = Math.floor(sec / 3600)
      const m = Math.floor((sec % 3600) / 60)
      const s = Math.floor(sec % 60)
      return `${String(h).padStart(2, '0')}:${String(m).padStart(2, '0')}:${String(s).padStart(2, '0')}`
    },
    onVideoError(e) {
      console.warn('Video failed to play source, falling back to /dummy.mp4:', e)
      if (!this.videoSrcFallback) {
        this.videoSrcFallback = true
        const video = this.$refs.videoPlayer
        if (video) {
          video.src = '/dummy.mp4'
          video.load()
          video.currentTime = this.clipStartSec
          video.play().catch(() => {})
        }
      } else {
        this.videoError = true
      }
    },
    copyRtspUrl() {
      if (this.detailRtspUrl) {
        navigator.clipboard.writeText(this.detailRtspUrl).then(() => {
          this.rtspCopied = true
          setTimeout(() => { this.rtspCopied = false }, 2000)
        }).catch(err => {
          console.error('Failed to copy RTSP URL:', err)
        })
      }
    },
    computeDuration(event) {
      const st = event.start_time
      const et = event.end_time

      // Try full datetime
      try {
        const start = new Date(st.replace(' ', 'T'))
        const end = new Date(et.replace(' ', 'T'))
        if (!isNaN(start) && !isNaN(end) && start.getFullYear() > 1970) {
          const diff = Math.round((end - start) / 1000)
          return diff >= 0 ? `${diff}s` : '?'
        }
      } catch { /* ignore */ }

      // Try relative time offset (HH:MM:SS)
      try {
        const sParts = st.split(':').map(Number)
        const eParts = et.split(':').map(Number)
        if (sParts.length >= 2 && eParts.length >= 2) {
          const sSec = (sParts[0] || 0) * 3600 + (sParts[1] || 0) * 60 + (sParts[2] || 0)
          const eSec = (eParts[0] || 0) * 3600 + (eParts[1] || 0) * 60 + (eParts[2] || 0)
          const diff = eSec - sSec
          return diff >= 0 ? `${diff}s` : '?'
        }
      } catch { /* ignore */ }

      return '?'
    },
    async openRemoteConfigModal() {
      this.showRemoteModal = true
      this.remoteSaveFeedback = null
      try {
        const resp = await fetch(`${API_BASE}/api/config/computer-1`)
        if (resp.ok) {
          const data = await resp.json()
          this.currentComputer1Url = data.url || ''
          this.remoteUrlInput = data.url || ''
          this.computer1Status = data.status === 'connected' ? 'connected' : 'unreachable'
        }
      } catch (e) {
        console.warn('Could not fetch remote config:', e)
      }
    },
    async saveRemoteConnection() {
      const target = this.remoteUrlInput.trim()
      if (!target) return
      this.savingRemoteConfig = true
      this.remoteSaveFeedback = null

      try {
        const resp = await fetch(`${API_BASE}/api/config/computer-1`, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ url: target }),
        })
        const data = await resp.json()
        if (resp.ok) {
          this.currentComputer1Url = data.url
          this.computer1Status = data.status === 'connected' ? 'connected' : 'unreachable'
          this.remoteSaveFeedback = {
            type: data.status === 'connected' ? 'success' : 'error',
            message: data.status === 'connected'
              ? `Connected successfully to Computer 1 at ${data.url}!`
              : `Saved URL ${data.url}, but Computer 1 is currently unreachable. Make sure the server or tunnel is running on Computer 1.`,
          }
          if (data.status === 'connected') {
            await this.refreshEvents()
          }
        } else {
          this.remoteSaveFeedback = {
            type: 'error',
            message: data.error || 'Failed to update Computer 1 configuration.',
          }
        }
      } catch (err) {
        this.remoteSaveFeedback = {
          type: 'error',
          message: `Network error: ${err.message}`,
        }
      } finally {
        this.savingRemoteConfig = false
      }
    },
    async checkRemoteConfig() {
      try {
        const resp = await fetch(`${API_BASE}/api/config/computer-1`)
        if (resp.ok) {
          const data = await resp.json()
          this.currentComputer1Url = data.url || ''
          this.remoteUrlInput = data.url || ''
          this.computer1Status = data.status === 'connected' ? 'connected' : 'unreachable'
        }
      } catch { /* ignore */ }
    },
  },
  watch: {
    'filters.object_type'(newType) {
      if (newType && newType !== 'person') {
        this.filters.shirt = ''
        this.filters.pants = ''
      }
    },
  },
  mounted() {
    this.checkRemoteConfig()
    this.fetchEvents()

    // Update cache status text every second
    this._cacheTimer = setInterval(() => {
      this.$forceUpdate()
    }, 1000)
  },
  unmounted() {
    if (this._cacheTimer) clearInterval(this._cacheTimer)
  },
}
</script>
