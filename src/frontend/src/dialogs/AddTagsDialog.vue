<template>
  <DialogComponent
    v-model="showDialog"
    :hideDraftBtn="true"
    @emitSubmit="emitAddOrEdit"
  >
    <template #title>
      <label id="modalTitle">
        {{ editTag ? "Edit Tag" : "Create Tag" }}
      </label>
    </template>
    <q-input
      id="name"
      v-model.trim="name"
      class="q-mb-xs"
      outlined
      dense
      autofocus
      :rules="[requiredRule]"
    >
      <template #before>
        <label
          for="name"
          class="field-label"
          >Name:</label
        >
      </template>
    </q-input>
    <q-input
      outlined
      dense
      :model-value="store.loggedInGroup.name"
      disable
    >
      <template #before>
        <label class="field-label">Group:</label>
      </template>
    </q-input>
  </DialogComponent>
</template>

<script setup>
import { ref, watch } from "vue";
import DialogComponent from "./DialogComponent.vue";
import { useLoginStore } from "@/stores/LoginStore.ts";

const store = useLoginStore();

const props = defineProps(["editTag"]);
const emit = defineEmits(["addTag", "updateTag"]);

function requiredRule(val) {
  return !!val || "This field is required";
}

const showDialog = defineModel();

const name = ref("");
const locked = ref(true);

watch(showDialog, (newVal) => {
  if (newVal) {
    name.value = props.editTag.name;
  } else {
    name.value = "";
    locked.value = true;
  }
});

function emitAddOrEdit() {
  if (props.editTag) {
    emit("updateTag", name.value, props.editTag.id);
  } else {
    emit("addTag", name.value);
  }
}
</script>
