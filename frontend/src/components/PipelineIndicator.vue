<template>
  <div class="pipeline-indicator">
    <div class="pipeline-title">🔄 Processing Pipeline</div>
    <div class="pipeline-steps">
      <div
        v-for="(step, index) in steps"
        :key="step.label"
      >
        <div class="pipeline-step" :class="stepClass(index)">
          <div class="pipeline-step-icon">
            <span v-if="stepClass(index) === 'done'">✓</span>
            <span v-else-if="stepClass(index) === 'active'">⟳</span>
            <span v-else>○</span>
          </div>
          <span>{{ step.label }}</span>
          <span v-if="stepClass(index) === 'done' && step.detail" style="margin-left: auto; font-size: 0.75rem; opacity: 0.7;">
            {{ step.detail }}
          </span>
        </div>
        <div v-if="index < steps.length - 1" class="pipeline-connector"></div>
      </div>
    </div>
  </div>
</template>

<script>
export default {
  name: 'PipelineIndicator',
  props: {
    /** Current step index (0–3). -1 = not started, 4 = all done */
    currentStep: {
      type: Number,
      default: -1,
    },
    /** Number of results found (shown on last step) */
    resultCount: {
      type: Number,
      default: 0,
    },
  },
  computed: {
    steps() {
      return [
        { label: 'Query received' },
        { label: 'Intent extracted' },
        { label: 'Database searched' },
        {
          label: `${this.resultCount} matching clip${this.resultCount !== 1 ? 's' : ''} found`,
          detail: '',
        },
      ]
    },
  },
  methods: {
    stepClass(index) {
      if (index < this.currentStep) return 'done'
      if (index === this.currentStep) return 'active'
      return 'pending'
    },
  },
}
</script>
