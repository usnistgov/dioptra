<template>
  <q-chip
    v-if="statusStyles[status]"
    :label="status"
    :icon-right="statusStyles[status].icon"
    :color="$q.dark.isActive ? statusStyles[status].colorDark : statusStyles[status].color"
    :text-color="$q.dark.isActive ? statusStyles[status].textColorDark : statusStyles[status].textColor"
    class="text-capitalize q-my-none q-mx-none"
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
      colorDark: "green-9",
      textColorDark: "green-2"
    },
    queued: {
      icon: "sym_o_hourglass",
      color: "yellow-2",
      textColor: "grey-9",
      colorDark: "yellow-10",
      textColorDark: "yellow-2",
      style: "min-width: 99px;"
    },
    started: {
      icon: "sym_o_play_circle",
      color: "blue-5",
      textColor: 'white',
      colorDark: "blue-8",
      textColorDark: "grey-2"
    },
    failed: {
      icon: "sym_o_error",
      color: "red-2",
      textColor: "grey-9",
      colorDark: "red-9",
      textColorDark: "red-2",
      style: "min-width: 99px;"
    }
  }

</script>

<style scopped>

</style>