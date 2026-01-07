<template>
<<<<<<< HEAD
  <table 
    class="text-left"
    :class="{ 'no-pointer': disabled }"
  >
    <tr v-for="(row, index) in rows" :key="index" :class="{ 'disabled': disabled }">
      <td class="text-bold" :style="{ 'min-width': firstColumnMinWidth }">{{ row.label }}</td>
      <td :style="secondColumnFullWidth ? { width: '100%' } : {}">
        <!-- Render as plain text OR use a custom slot -->
        <slot :name="row.slot" v-bind="row.props">
          {{ row.value }}
        </slot>
      </td>
    </tr>
  </table>
=======
  <q-markup-table flat bordered separator="cell" class="text-left">
    <tbody>
      <tr v-for="(row, index) in rows" :key="index" :class="{ 'disabled': disabled }">
        <td 
          class="text-weight-bold" 
          :class="$q.dark.isActive ? 'bg-grey-9 text-grey-4' : 'bg-grey-2 text-grey-9'"
          style="min-width: 150px; width: 150px;"
        >
          {{ row.label }}
        </td>
        
        <td :style="secondColumnFullWidth ? { width: '100%' } : { minWidth: '20vw' }">
          <slot :name="row.slot" v-bind="row.props">
            {{ row.value }}
          </slot>
        </td>
      </tr>
    </tbody>
  </q-markup-table>
>>>>>>> f0524b85 (feat: add table styling WIP)
</template>

<script setup>
defineProps({
<<<<<<< HEAD
  rows: {
    type: Array,
    required: true
  },
  disabled: {
    type: Boolean,
    default: false
  },
  firstColumnMinWidth: {
    type: String,
    default: '150px'
  },
  secondColumnFullWidth: {
    type: Boolean,
    default: false
  }
=======
  rows: { type: Array, required: true },
  disabled: { type: Boolean, default: false },
  secondColumnFullWidth: { type: Boolean, default: false }
>>>>>>> f0524b85 (feat: add table styling WIP)
})
</script>

<style scoped>
<<<<<<< HEAD
  table {
    border-collapse: collapse;
  }

  td {
    border: 1px solid #cecece;
  }

  td {
    padding: 10px;
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
=======
/* Only functional utility classes remain */
.disabled {
  pointer-events: none;
  opacity: 0.6;
}
>>>>>>> f0524b85 (feat: add table styling WIP)
</style>