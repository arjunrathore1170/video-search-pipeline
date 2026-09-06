<template>
  <div class="video-result-card">
    <div class="video-thumbnail">
      <span class="thumbnail-camera">📷 {{ result.camera_id }}</span>
      <button class="thumbnail-play" @click="handlePlay" title="Play clip">▶</button>
      <span class="thumbnail-duration">{{ result.duration }}</span>
    </div>
    <div class="video-card-body">
      <div class="video-card-camera">{{ result.camera_id }}</div>
      <div class="video-card-time">
        <span>{{ result.start_time }}</span>
        <span class="arrow">→</span>
        <span>{{ result.end_time }}</span>
      </div>
      <div class="video-card-attrs" v-if="attributeTags.length">
        <span class="attr-tag" v-for="tag in attributeTags" :key="tag">{{ tag }}</span>
      </div>
      <button class="video-play-btn" @click="handlePlay">
        ▶ Play Clip
      </button>
    </div>
  </div>
</template>

<script>
export default {
  name: 'VideoResultCard',
  props: {
    result: {
      type: Object,
      required: true,
    },
  },
  emits: ['play'],
  computed: {
    attributeTags() {
      const tags = []
      if (this.result.object_type) tags.push(this.result.object_type)
      if (this.result.shirt) tags.push(`shirt: ${this.result.shirt}`)
      if (this.result.pants) tags.push(`pants: ${this.result.pants}`)
      if (this.result.vehicle_type) tags.push(this.result.vehicle_type)
      if (this.result.vehicle_color) tags.push(`color: ${this.result.vehicle_color}`)
      return tags
    },
  },
  methods: {
    handlePlay() {
      this.$emit('play', this.result)
    },
  },
}
</script>
