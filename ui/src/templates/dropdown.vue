<template>
  <div class="dropdown">
    <button class="btn btn-secondary dropdown-toggle" type="button" data-toggle="dropdown" aria-haspopup="true" aria-expanded="false">
      {{ buttonText }}
    </button>
    <div class="dropdown-menu" aria-labelledby="dropdownMenuButton">
      <a class="dropdown-item" v-for="(item, index) in items" :key="index" @click="handleItemClick(item)">
        {{ item.label }}
      </a>
    </div>
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
    buttonText: {
      type: String,
      default: 'Dropdown'
    }
  },
  methods: {
    handleItemClick(item) {
      this.$emit('item-click', item);
    }
  }
}
</script>
