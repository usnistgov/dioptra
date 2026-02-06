<template>
  <q-markup-table flat bordered separator="cell" class="text-left">
    <tbody>
      <tr
        v-for="(row, index) in rows"
        :key="index"
        :class="{ disabled: disabled }"
      >
        <td
          class="text-weight-bold"
          :class="
            $q.dark.isActive ? 'bg-grey-9 text-grey-4' : 'bg-grey-2 text-grey-9'
          "
          style="min-width: 150px; width: 150px"
        >
          {{ row.label }}
        </td>

        <td
          :style="
            secondColumnFullWidth ? { width: '100%' } : { minWidth: '20vw' }
          "
        >
          <slot :name="row.slot" v-bind="row.props">
            {{ row.value }}
          </slot>
        </td>
      </tr>
    </tbody>
  </q-markup-table>
</template>

<script setup>
defineProps({
  rows: { type: Array, required: true },
  disabled: { type: Boolean, default: false },
  secondColumnFullWidth: { type: Boolean, default: false },
});
</script>

<style scoped>
.disabled {
  pointer-events: none;
  opacity: 0.6;
}
</style>
