<template>
  <div class="intent-card">
    <div class="intent-card-header">
      <span class="intent-card-title">🎯 Structured Intent</span>
      <span class="intent-card-badge">JSON</span>
    </div>
    <div class="intent-json" v-html="formattedJson"></div>
  </div>
</template>

<script>
export default {
  name: 'IntentCard',
  props: {
    intent: {
      type: Object,
      required: true,
    },
  },
  computed: {
    formattedJson() {
      const raw = JSON.stringify(this.intent, null, 2)
      // Syntax-highlight the JSON
      return raw
        .replace(/&/g, '&amp;')
        .replace(/</g, '&lt;')
        .replace(/>/g, '&gt;')
        .replace(/"([^"]+)"(?=\s*:)/g, '<span class="json-key">"$1"</span>')
        .replace(/:\s*"([^"]+)"/g, ': <span class="json-string">"$1"</span>')
        .replace(/[{}[\]]/g, '<span class="json-bracket">$&</span>')
    },
  },
}
</script>
