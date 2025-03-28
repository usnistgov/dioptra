<template>
  <q-chip
    v-if="statusStyles[status]"
    :label="status"
    :icon-right="statusStyles[status].icon"
    :color="statusStyles[status].color"
    :text-color="statusStyles[status].textColor"
    class="text-capitalize q-my-none"
    :ripple="false"
    :style="statusStyles[status].style"
    style="cursor: default; margin-top: -4px; margin-bottom: -3px;"
  />

</template>

<script setup>
defineProps(['status'])

const statusStyles = {
    finished: {
      icon: "sym_o_check_circle",
      color: "green-2",
      textColor: "green-10",
    },
    queued: {
      icon: "sym_o_hourglass",
      color: "yellow-2",
      textColor: "grey-9",
      style: "min-width: 99px;"
    },
    failed: {
      icon: "sym_o_error",
      color: "red-2",
      textColor: "grey-9",
      style: "min-width: 99px;"
    }
  }

</script>

<style scopped>

</style>