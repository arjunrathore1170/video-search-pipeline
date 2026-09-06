<template>
  <div class="chat-message" :class="message.role">
    <div class="message-avatar">
      <span v-if="message.role === 'user'">👤</span>
      <span v-else>🤖</span>
    </div>

    <div :class="message.role === 'assistant' ? 'assistant-response-area' : 'message-content'">
      <!-- User message -->
      <template v-if="message.role === 'user'">
        <div class="message-bubble">{{ message.text }}</div>
        <div class="message-time">{{ formatTime(message.timestamp) }}</div>
      </template>

      <!-- Assistant loading -->
      <template v-else-if="message.type === 'loading'">
        <div class="message-bubble">
          <div class="loading-dots">
            <span></span><span></span><span></span>
          </div>
        </div>
      </template>

      <!-- Assistant error -->
      <template v-else-if="message.type === 'error'">
        <div class="message-bubble error-bubble">
          ⚠️ {{ message.text }}
        </div>
        <div class="message-time">{{ formatTime(message.timestamp) }}</div>
      </template>

      <!-- Assistant response with results -->
      <template v-else>
        <!-- Pipeline indicator -->
        <PipelineIndicator
          :currentStep="4"
          :resultCount="message.results ? message.results.length : 0"
        />

        <!-- Fallback notice -->
        <div v-if="message.usedFallback" class="fallback-notice">
          ⚡ Ollama unavailable — used keyword-based intent extraction
        </div>

        <!-- Intent card -->
        <IntentCard v-if="message.intent" :intent="message.intent" />

        <!-- Results -->
        <template v-if="message.results && message.results.length > 0">
          <div class="results-header">
            <span class="results-title">📹 Search Results</span>
            <span class="results-count">{{ message.results.length }} clip{{ message.results.length !== 1 ? 's' : '' }}</span>
          </div>
          <div class="results-grid">
            <VideoResultCard
              v-for="(result, idx) in message.results"
              :key="idx"
              :result="result"
              @play="$emit('play', $event)"
            />
          </div>
        </template>

        <!-- No results -->
        <div v-else-if="message.results && message.results.length === 0" class="no-results">
          <div class="no-results-icon">🔍</div>
          <h4>No matching video events were found.</h4>
          <p>Try changing the person, clothing, camera, or time condition.</p>
        </div>

        <div class="message-time">{{ formatTime(message.timestamp) }}</div>
      </template>
    </div>
  </div>
</template>

<script>
import PipelineIndicator from './PipelineIndicator.vue'
import IntentCard from './IntentCard.vue'
import VideoResultCard from './VideoResultCard.vue'

export default {
  name: 'ChatMessage',
  components: { PipelineIndicator, IntentCard, VideoResultCard },
  props: {
    message: {
      type: Object,
      required: true,
    },
  },
  emits: ['play'],
  methods: {
    formatTime(ts) {
      if (!ts) return ''
      const d = new Date(ts)
      return d.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })
    },
  },
}
</script>
