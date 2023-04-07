<template>
  <a :href="href" :class="linkClass" @click.prevent="handleClick">
    {{ linkText }}
  </a>
</template>

<script>
export default {
  props: {
    href: {
      type: String,
      required: true
    },
    linkText: {
      type: String,
      default: 'Link'
    },
    linkClass: {
      type: String,
      default: 'link'
    }
  },
  methods: {
    handleClick() {
      this.$emit('click');
    }
  }
};
</script>
