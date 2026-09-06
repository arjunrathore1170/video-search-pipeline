<template>
  <div class="search-input-container">
    <div class="search-input-wrapper">
      <input
        ref="inputRef"
        v-model="query"
        type="text"
        placeholder="Ask something about the recorded videos..."
        @keydown.enter="handleSubmit"
        :disabled="loading"
      />
      <button
        class="search-btn"
        @click="handleSubmit"
        :disabled="loading || !query.trim()"
      >
        <span v-if="loading" class="spinner"></span>
        <template v-else>🔍 Search</template>
      </button>
    </div>
  </div>
</template>

<script>
export default {
  name: 'SearchInput',
  props: {
    loading: {
      type: Boolean,
      default: false,
    },
  },
  emits: ['search'],
  data() {
    return {
      query: '',
    }
  },
  methods: {
    handleSubmit() {
      const trimmed = this.query.trim()
      if (!trimmed || this.loading) return
      this.$emit('search', trimmed)
      this.query = ''
    },
    /** Public: set the input value (used for example queries) */
    setQuery(text) {
      this.query = text
      this.$nextTick(() => {
        this.$refs.inputRef?.focus()
      })
    },
  },
}
</script>
