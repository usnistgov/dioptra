<template>
  <nav>
    <ol class="breadcrumb">
      <li v-for="(item, index) in items" :key="index" :class="{ active: index === items.length - 1 }">
        <router-link :to="item.to">{{ item.label }}</router-link>
      </li>
    </ol>
  </nav>
</template>

<script>
export default {
  props: {
    items: {
      type: Array,
      required: true,
      default: () => []
    }
  }
}
</script>
