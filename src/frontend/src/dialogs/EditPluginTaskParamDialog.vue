<template>
  <DialogComponent
    v-model="showDialog"
    :hideDraftBtn="true"
    @emitSubmit="emitAddOrEdit"
  >
    <template #title>
      <label id="modalTitle">
        {{ props.editParam ? `Edit Param '${editParam.name}'` : "Create Param" }}
      </label>
    </template>
    <q-input
      id="name"
      v-model.trim="name"
      :rules="[requiredRule]"
      dense
      outlined
      class="q-mb-xs"
    >
      <template #before>
        <label
          for="name"
          class="field-label"
          >Name:</label
        >
      </template>
    </q-input>
    <q-select
      id="type"
      v-model="parameterType"
      emit-value
      option-label="name"
      map-options
      :options="pluginParameterTypes"
      outlined
      dense
      :rules="[requiredRule]"
    >
      <template #before>
        <label
          for="type"
          class="field-label"
          >Type:</label
        >
      </template>
    </q-select>
    <div
      v-if="inputOrOutputParams === 'inputParams'"
      class="row items-center"
    >
      <label
        class="col-3"
        for="required"
      >
        Required:
      </label>
      <q-checkbox
        id="required"
        v-model="required"
      />
    </div>
  </DialogComponent>
</template>

<script setup>
import { ref, watch } from "vue";
import DialogComponent from "./DialogComponent.vue";

const props = defineProps(["editParam", "pluginParameterTypes", "inputOrOutputParams"]);
const emit = defineEmits(["addParam", "updateParam"]);

function requiredRule(val) {
  return !!val || "This field is required";
}

const showDialog = defineModel();

const name = ref("");
const parameterType = ref("");
const required = ref(true);

watch(showDialog, (newVal) => {
  if (newVal) {
    name.value = props.editParam.name;
    if (props.editParam.parameterType?.id) {
      parameterType.value = props.editParam.parameterType;
    }
    required.value = props.editParam && Object.hasOwn(props.editParam, "required") ? props.editParam.required : true;
  } else {
    name.value = "";
    parameterType.value = "";
  }
});

function emitAddOrEdit() {
  const param = { name: name.value, parameterType: parameterType.value };
  if (props.inputOrOutputParams === "inputParams") {
    param.required = required.value;
  }
  if (props.editParam) {
    emit("updateParam", param);
  } else {
    emit("addParam", param);
  }
  showDialog.value = false;
}
</script>
