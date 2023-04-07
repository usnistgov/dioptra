<template>
  <button :class="btnClass" @click="handleClick">
    {{ buttonText }}
  </button>
</template>

<script>
export default {
  props: {
    buttonText: {
      type: String,
      default: 'Button'
    },
    btnClass: {
      type: String,
      default: 'btn'
    }
  },
  methods: {
    handleClick() {
      this.$emit('click');
    }
  }
};
</script>
