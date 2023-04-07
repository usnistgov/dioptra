<template>
  <div class="accordion">
    <div v-for="(item, index) in items" :key="index" class="accordion-item">
      <div class="accordion-item-header" @click="toggleAccordion(index)">
        {{ item.title }}
        <span :class="{ 'rotate': isActive(index) }">+</span>
      </div>
      <div v-show="isActive(index)" class="accordion-item-content">
        {{ item.content }}
      </div>
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
    }
  },
  data() {
    return {
      activeIndex: -1
    };
  },
  methods: {
    toggleAccordion(index) {
      if (this.isActive(index)) {
        this.activeIndex = -1;
      } else {
        this.activeIndex = index;
      }
    },
    isActive(index) {
      return this.activeIndex === index;
    }
  }
};
</script>

<style>
/*.accordion-item-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 10px;
  background-color: #f7f7f7;
  border: 1px solid #ddd;
  cursor: pointer;
}

.rotate {
  transform: rotate(45deg);
}

.accordion-item-content {
  padding: 10px;
  border: 1px solid #ddd;
}*/
</style>
