<template>
  <div class="chat-window" ref="chatContainer">
    <!-- Empty state -->
    <div v-if="messages.length === 0" class="chat-empty">
      <div class="chat-empty-icon">🎥</div>
      <h3>Video Search Assistant</h3>
      <p>Search through recorded camera footage using natural language. Try one of these examples:</p>
      <div class="example-queries">
        <button
          v-for="q in exampleQueries"
          :key="q"
          class="example-query"
          @click="$emit('example', q)"
        >
          {{ q }}
        </button>
      </div>
    </div>

    <!-- Messages -->
    <ChatMessage
      v-for="(msg, index) in messages"
      :key="index"
      :message="msg"
      @play="$emit('play', $event)"
    />
  </div>
</template>

<script>
import ChatMessage from './ChatMessage.vue'

export default {
  name: 'ChatWindow',
  components: { ChatMessage },
  props: {
    messages: {
      type: Array,
      default: () => [],
    },
  },
  emits: ['example', 'play'],
  data() {
    return {
      exampleQueries: [
        'Show the person wearing a red shirt after 10 PM',
        'Find a person wearing a blue shirt',
        'Show vehicles after 8 PM',
        'Find a person in camera 1 after 9 PM',
      ],
    }
  },
  watch: {
    messages: {
      handler() {
        this.$nextTick(() => {
          this.scrollToBottom()
        })
      },
      deep: true,
    },
  },
  methods: {
    scrollToBottom() {
      const container = this.$refs.chatContainer
      if (container) {
        container.scrollTop = container.scrollHeight
      }
    },
  },
}
</script>
