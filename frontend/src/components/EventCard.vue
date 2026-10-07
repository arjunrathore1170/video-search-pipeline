<template>
  <div
    class="event-card"
    :class="[event.object_type, { expanded: isHovered }]"
    @mouseenter="isHovered = true"
    @mouseleave="isHovered = false"
    @click="$emit('view-details', event)"
    :id="`event-card-${event.event_id}`"
  >
    <!-- Type Badge -->
    <div class="card-type-strip" :class="event.object_type"></div>

    <div class="card-header">
      <div class="card-type-icon">
        {{ event.object_type === 'person' ? '🧍' : '🚗' }}
      </div>
      <div class="card-ids">
        <span class="card-event-id">#{{ event.event_id }}</span>
        <span class="card-track-id">Track {{ event.track_id }}</span>
      </div>
      <div class="card-object-type-badge" :class="event.object_type">
        {{ event.object_type }}
      </div>
    </div>

    <!-- Camera Info -->
    <div class="card-camera" v-if="event.camera_name">
      <span class="camera-icon">📷</span>
      <span class="camera-name">{{ event.camera_name }}</span>
      <span class="camera-id" v-if="event.camera_id">· Cam {{ event.camera_id }}</span>
    </div>

    <!-- Source Badge -->
    <div class="card-source-badge" :class="sourceType">
      <span v-if="sourceType === 'uploaded'" class="source-icon">📁</span>
      <span v-else-if="sourceType === 'nvr'" class="source-icon">🎥</span>
      <span v-else class="source-icon">❓</span>
      <span class="source-label">{{ sourceLabel }}</span>
    </div>

    <!-- Timestamps -->
    <div class="card-times">
      <div class="card-time-row">
        <span class="time-label">Start</span>
        <span class="time-value">{{ formatTime(event.start_time) }}</span>
      </div>
      <div class="card-time-row">
        <span class="time-label">End</span>
        <span class="time-value">{{ formatTime(event.end_time) }}</span>
      </div>
      <div class="card-time-row duration">
        <span class="time-label">Duration</span>
        <span class="time-value accent">{{ duration }}</span>
      </div>
    </div>

    <!-- Attributes -->
    <div class="card-attributes" v-if="hasAttributes">
      <div class="attr-item" v-if="event.attributes.shirt">
        <span class="attr-label">Shirt</span>
        <span class="attr-value">
          <span class="color-dot" :style="{ background: colorMap(event.attributes.shirt) }"></span>
          {{ event.attributes.shirt }}
        </span>
      </div>
      <div class="attr-item" v-if="event.attributes.pants">
        <span class="attr-label">Pants</span>
        <span class="attr-value">
          <span class="color-dot" :style="{ background: colorMap(event.attributes.pants) }"></span>
          {{ event.attributes.pants }}
        </span>
      </div>
    </div>
    <div class="card-attributes empty" v-else>
      <span class="no-attrs">No attributes</span>
    </div>

    <!-- Video file / NVR indicator -->
    <div class="card-footer">
      <span class="video-status" :class="sourceType">
        <template v-if="sourceType === 'uploaded'">
          🎬 {{ shortFilename }}
        </template>
        <template v-else-if="sourceType === 'nvr'">
          🎥 NVR {{ event.nvr_ip }}:{{ event.nvr_channel }}
        </template>
        <template v-else>
          ⚠️ No video source
        </template>
      </span>
      <button class="card-play-btn" title="Play video clip" @click.stop="$emit('view-details', event)">
        ▶ Play Video
      </button>
    </div>
  </div>
</template>

<script>
const CSS_COLORS = {
  red: '#ef4444', blue: '#3b82f6', green: '#22c55e',
  yellow: '#eab308', white: '#e5e7eb', black: '#1f2937',
  gray: '#6b7280', grey: '#6b7280', orange: '#f97316',
  purple: '#a855f7', pink: '#ec4899', brown: '#92400e',
  silver: '#94a3b8',
}

export default {
  name: 'EventCard',
  props: {
    event: { type: Object, required: true },
  },
  emits: ['view-details'],
  data() {
    return { isHovered: false }
  },
  computed: {
    duration() {
      const st = this.event.start_time
      const et = this.event.end_time

      // Try full datetime first
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
    hasAttributes() {
      const a = this.event.attributes
      return a && Object.keys(a).length > 0
    },
    sourceType() {
      if (this.event.video_file) return 'uploaded'
      if (this.event.nvr_ip) return 'nvr'
      return 'unknown'
    },
    sourceLabel() {
      if (this.sourceType === 'uploaded') return 'Uploaded'
      if (this.sourceType === 'nvr') {
        const mfr = this.event.video_source?.manufacturer
        return mfr ? mfr.charAt(0).toUpperCase() + mfr.slice(1) : 'NVR'
      }
      return 'Unknown'
    },
    shortFilename() {
      if (!this.event.video_file) return ''
      const parts = this.event.video_file.split('/')
      return parts[parts.length - 1]
    },
  },
  methods: {
    formatTime(dt) {
      if (!dt) return ''
      // Show just HH:MM:SS for compact display
      const parts = dt.split(' ')
      return parts.length > 1 ? parts[1] : dt
    },
    colorMap(name) {
      return CSS_COLORS[name?.toLowerCase()] || '#94a3b8'
    },
  },
}
</script>
