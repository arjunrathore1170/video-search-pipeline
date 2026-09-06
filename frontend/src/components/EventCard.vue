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

    <!-- Video file indicator -->
    <div class="card-footer">
      <span class="video-status" :class="{ connected: event.video_file }">
        {{ event.video_file ? '🎬 Video attached' : '📡 No video' }}
      </span>
      <span class="view-details-link">View →</span>
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
      try {
        const start = new Date(this.event.start_time.replace(' ', 'T'))
        const end = new Date(this.event.end_time.replace(' ', 'T'))
        const diff = Math.round((end - start) / 1000)
        return diff >= 0 ? `${diff}s` : '?'
      } catch { return '?' }
    },
    hasAttributes() {
      const a = this.event.attributes
      return a && Object.keys(a).length > 0
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
