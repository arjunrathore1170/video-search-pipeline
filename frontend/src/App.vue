<template>
  <div class="app-shell">
    <!-- Header -->
    <header class="app-header" id="app-header">
      <div class="header-inner">
        <div class="header-left">
          <img src="/logo.jpg" alt="Video Search Logo" class="header-logo" />
          <div>
            <h1 class="header-title">Video Search Pipeline</h1>
            <p class="header-subtitle">YOLO + Tracking Event Browser</p>
          </div>
        </div>
        <div class="header-right">
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
              placeholder="Ask in natural language (e.g. 'person in orange shirt with blue pants' or 'car after 8 PM')..."
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
        </div>

        <!-- Loading State -->
        <div v-if="loading" class="loading-state">
          <div class="loading-spinner-large"></div>
          <p>Loading events from pipeline...</p>
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
          </div>
        </div>

        <!-- Video Player -->
        <div class="modal-video-container">
          <video
            ref="videoPlayer"
            class="modal-video-player"
            controls
            autoplay
            preload="metadata"
            :src="getVideoSrc(detailEvent)"
            @error="onVideoError"
            @loadeddata="onVideoLoadedData"
            @timeupdate="onVideoTimeUpdate"
          >
            Your browser does not support HTML5 video tag.
          </video>
          <div v-if="videoError" class="video-error-banner">
            ⚠️ Could not play video. Ensure the file is an H.264/AAC encoded MP4 or WebM file.
          </div>
          <div class="video-notice" v-else>
            <div class="clip-info">
              <span class="clip-file">🎬 <strong>{{ detailEvent.video_file || 'dummy.mp4' }}</strong></span>
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
        </div>

        <div class="modal-body">
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
            <span class="modal-field-label">Video File</span>
            <span class="modal-field-value" :class="{ muted: !detailEvent.video_file }">
              {{ detailEvent.video_file || 'Not connected' }}
            </span>
          </div>
        </div>
        <div class="modal-json">
          <div class="json-header">Raw JSON</div>
          <pre class="json-body">{{ JSON.stringify(detailEvent, null, 2) }}</pre>
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
      detailEvent: null,
      videoError: false,
      clipStartSec: 0,
      clipEndSec: 0,
      clipDurationSec: 0,
      enforceClipEnd: true,
      hasSeekedToStart: false,
      cacheTimestamp: null,
      searchQuery: '',
      aiSearchLoading: false,
      aiSearchResults: null,
      aiSearchIntent: null,
      aiSearchUsedFallback: false,
      quickPresets: [
        'person in orange shirt',
        'person in red shirt with blue pants',
        'car',
        'track 1',
      ],
      filters: {
        object_type: '',
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
          const d = new Date(e.start_time.replace(' ', 'T'))
          return d >= after
        })
      }
      if (this.filters.start_before) {
        const before = new Date(this.filters.start_before)
        events = events.filter(e => {
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
    uniqueObjectTypes() {
      return [...new Set(this.allEvents.map(e => e.object_type))].sort()
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
      if (this.filters.event_id) tags.push({ key: 'event_id', label: `Event #${this.filters.event_id}` })
      if (this.filters.track_id) tags.push({ key: 'track_id', label: `Track #${this.filters.track_id}` })
      if (this.filters.shirt) tags.push({ key: 'shirt', label: `Shirt: ${this.filters.shirt}` })
      if (this.filters.pants) tags.push({ key: 'pants', label: `Pants: ${this.filters.pants}` })
      if (this.filters.start_after) tags.push({ key: 'start_after', label: `After: ${this.filters.start_after}` })
      if (this.filters.start_before) tags.push({ key: 'start_before', label: `Before: ${this.filters.start_before}` })
      return tags
    },
  },
  methods: {
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
      } catch (err) {
        if (err.name === 'TypeError' && err.message.includes('fetch')) {
          this.error = 'Unable to connect to the backend server. Make sure Flask is running on http://localhost:5000'
        } else {
          this.error = err.message
        }
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
      this.detailEvent = event
      this.enforceClipEnd = true
      this.hasSeekedToStart = false

      const bounds = this.getClipBounds(event)
      this.clipStartSec = bounds.start
      this.clipEndSec = bounds.end
      this.clipDurationSec = Math.max(0, bounds.end - bounds.start)
    },
    getClipBounds(event) {
      if (!event) return { start: 0, end: 10 }
      if (typeof event.start_sec === 'number' && typeof event.end_sec === 'number') {
        return { start: event.start_sec, end: event.end_sec }
      }
      try {
        const timeStrStart = event.start_time.includes(' ') ? event.start_time.split(' ')[1] : event.start_time
        const timeStrEnd = event.end_time.includes(' ') ? event.end_time.split(' ')[1] : event.end_time
        const startParts = timeStrStart.split(':').map(Number)
        const endParts = timeStrEnd.split(':').map(Number)
        const startSec = startParts[0] * 3600 + startParts[1] * 60 + (startParts[2] || 0)
        const endSec = endParts[0] * 3600 + endParts[1] * 60 + (endParts[2] || 0)
        return { start: startSec, end: Math.max(startSec + 5, endSec) }
      } catch {
        return { start: 0, end: 30 }
      }
    },
    onVideoLoadedData() {
      this.videoError = false
      const video = this.$refs.videoPlayer
      if (video && !this.hasSeekedToStart) {
        this.hasSeekedToStart = true
        video.currentTime = this.clipStartSec
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
        video.currentTime = this.clipStartSec
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
      console.warn('Video failed to play:', e)
      this.videoError = true
    },
    getVideoSrc(event) {
      if (!event) return '/dummy.mp4'
      if (event.video_file) {
        if (
          event.video_file.startsWith('http://') ||
          event.video_file.startsWith('https://') ||
          event.video_file.startsWith('/')
        ) {
          return event.video_file
        }
        return `/${event.video_file}`
      }
      return '/dummy.mp4'
    },
    computeDuration(event) {
      try {
        const start = new Date(event.start_time.replace(' ', 'T'))
        const end = new Date(event.end_time.replace(' ', 'T'))
        const diff = Math.round((end - start) / 1000)
        return diff >= 0 ? `${diff}s` : '?'
      } catch {
        return '?'
      }
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
