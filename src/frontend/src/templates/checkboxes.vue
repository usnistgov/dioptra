<template>
  <div>
    <label v-for="(item, index) in items" :key="index">
      <input type="checkbox" :value="item.value" v-model="selectedItems">
      {{ item.label }}
    </label>
  </div>
</template>

<script>
export default {
  props: {
    items: {
      type: Array,
      required: true,
      default: () => []
    },
    value: {
      type: Array,
      default: () => []
    }
  },
  data() {
    return {
      selectedItems: this.value
    }
  },
  watch: {
    selectedItems(newValue) {
      this.$emit('input', newValue);
    }
  }
}
</script>
