<template>
  <DialogComponent
    v-model="showDialog"
    :hideDraftBtn="true"
    @emitSubmit="emitSubmit()"
  >
    <template #title>
      <label id="modalTitle"> {{ props.editParam ? "Edit" : "Create" }} Parameter </label>
    </template>
    <q-input
      v-model.trim="parameter.name"
      outlined
      dense
      :rules="[requiredRule]"
      class="q-mb-sm"
      aria-required="true"
    >
      <template #before>
        <label :class="`field-label`">Name:</label>
      </template>
    </q-input>
    <q-select
      v-model="parameter.parameterType"
      outlined
      :options="typeOptions"
      dense
      :rules="[requiredRule]"
      aria-required="true"
    >
      <template #before>
        <label :class="`field-label`">Type:</label>
      </template>
    </q-select>
    <q-toggle
      :model-value="parameter.defaultValue !== null"
      label="Set Default Value?"
      style="margin-left: 100px; margin-top: 0"
      @update:model-value="
        (val) => {
          parameter.defaultValue = val ? '' : null;
        }
      "
    />
    <div v-if="parameter.defaultValue === null">
      Default Value:
      <q-chip
        label="No Default"
        color="negative"
        text-color="white"
        class="q-ml-md"
      />
    </div>
    <q-input
      v-else
      v-model.trim="parameter.defaultValue"
      outlined
      dense
      class="q-mb-sm"
      aria-required="false"
      :hint="
        parameter.defaultValue === ''
          ? `The default value is an empty string that will be coersed into type: ${parameter.parameterType.toUpperCase()}`
          : ''
      "
      placeholder="[Empty String]"
      :disable="parameter.defaultValue === null"
    >
      <template #before>
        <label
          class="field-label"
          :class="{ 'text-grey-6': parameter.defaultValue === null }"
        >
          Default Value:
        </label>
      </template>
    </q-input>
  </DialogComponent>
</template>

<script setup>
import DialogComponent from "./DialogComponent.vue";
import { ref, watch } from "vue";

const emit = defineEmits(["updateParam", "createParam"]);

const requiredRule = (val) => (val && val.length > 0) || "This field is required";

const showDialog = defineModel();
const props = defineProps(["editParam"]);

const parameter = ref({
  name: "",
  parameterType: "",
  defaultValue: "",
});

const typeOptions = ref(["string", "float", "integer", "boolean", "list", "mapping"]);

watch(showDialog, (newVal) => {
  if (newVal && props.editParam) {
    // edit param
    parameter.value.name = props.editParam.name;
    parameter.value.parameterType = props.editParam.parameterType;
    parameter.value.defaultValue = props.editParam.defaultValue;
  } else {
    // close dialog
    parameter.value.name = "";
    parameter.value.parameterType = "";
    parameter.value.defaultValue = "";
  }
});

function emitSubmit() {
  if (props.editParam) {
    emit("updateParam", parameter.value);
  } else {
    emit("createParam", parameter.value);
  }
}
</script>
