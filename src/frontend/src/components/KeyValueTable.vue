<template>
  <table 
    class="text-left"
    :class="{ 'no-pointer': disabled }"
  >
    <tr v-for="(row, index) in rows" :key="index" :class="{ 'disabled': disabled }">
      <td>{{ row.label }}</td>
      <td :style="secondColumnFullWidth ? { width: '100%' } : {}">
        <!-- Render as plain text OR use a custom slot -->
        <slot :name="row.slot" v-bind="row.props">
          {{ row.value }}
        </slot>
      </td>
    </tr>
  </table>
</template>

<script setup>
defineProps({
  rows: {
    type: Array,
    required: true
  },
  disabled: {
    type: Boolean,
    default: false
  },
  secondColumnFullWidth: {
    type: Boolean,
    default: false
  }
})
</script>

<style scoped>
  table {
    border-collapse: collapse;
  }

  td {
    border: 1px solid #cecece;
  }

  td {
    padding: 10px;
  }

  td:first-child {
    font-weight: bold;
    min-width: 150px;
  }

  td:nth-child(2) {
    min-width: 20vw;
  }

  .body--dark td:first-child {
    background-color: rgb(31, 39, 45);
    color: rgb(146, 164, 179);
  }

  .body--light td:first-child {
    background-color: rgb(246, 247, 249);
  }

  .no-pointer {
    cursor: not-allowed;
  }

  .disabled {
    pointer-events: none;
  }
</style>