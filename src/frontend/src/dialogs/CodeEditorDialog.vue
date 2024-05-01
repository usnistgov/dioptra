<template>
  <q-dialog v-model="showDialog" aria-labelledby="modalTitle">
    <q-card flat style="min-width: 60%;" >
      <q-card-section class="bg-primary text-white q-mb-md">
        <div class="text-h6">
          <slot name="title" />
        </div>
      </q-card-section>
      <q-card-section>
        <CodeEditor v-model="editCode" :placeholder="'#Enter plugin file code here...'"  />
      </q-card-section>
      <q-separator />
      <q-card-actions align="right" class="text-primary">
        <q-btn color="red" class="text-white" label="Cancel" v-close-popup />
        <q-btn color="primary" class="text-white" label="Save" @click="submit" />
      </q-card-actions>
    </q-card>
  </q-dialog>
</template>

<script setup>
  import { onMounted, ref, watch } from 'vue'
  import CodeEditor from '@/components/CodeEditor.vue'

  const showDialog = defineModel('showDialog')
  const code = defineModel('code')

  const editCode = ref('')

  watch(showDialog, (newVal) => {
    if(newVal) {
      editCode.value = JSON.parse(JSON.stringify(code.value))
    }
  })

  function submit() {
    showDialog.value = false
    code.value = editCode.value
  }

</script>