<template>
  <PageTitle title="Create Group" resourceType="group" />
  <q-banner rounded class="bg-orange-2 text-dark q-mt-md">
    Warning: all future users have access to groups created in this phase.
  </q-banner>
  <div :style="{ width: isMobile ? '100%' : isMedium ? '60%' : '50%' }">
    <fieldset class="q-mt-lg">
      <legend>Basic Info</legend>
      <q-form ref="form" class="q-ma-lg" @submit="submit">
        <q-input
          outlined
          dense
          v-model.trim="name"
          :rules="[requiredRule]"
          aria-required="true"
          class="q-mb-sm"
        >
          <template #before>
            <label class="field-label">Name:</label>
          </template>
        </q-input>
        <q-checkbox
          v-model="isPublic"
          label="Public"
          disable
          class="q-mb-sm"
        />
      </q-form>
    </fieldset>

    <div class="float-right q-mt-lg">
      <q-btn
        outline
        color="primary"
        label="Cancel"
        class="q-mr-lg cancel-btn"
        @click="router.push('/groups')"
      />
      <q-btn
        color="primary"
        label="Submit"
        @click="submit"
      />
    </div>
  </div>
</template>

<script setup>
import { inject, ref } from 'vue'
import { useRouter } from 'vue-router'

import PageTitle from '@/components/PageTitle.vue'
import * as api from '@/services/dataApi'
import * as notify from '../notify'

const router = useRouter()
const isMobile = inject('isMobile')
const isMedium = inject('isMedium')

const form = ref()
const name = ref('')
const isPublic = ref(true)

const requiredRule = (val) => (val && val.length > 0) || 'This field is required'

async function submit() {
  const valid = await form.value?.validate()
  if(!valid) {
    return
  }

  try {
    await api.addItem('groups', { name: name.value, public: isPublic.value })
    notify.success('Group created')
    router.push('/groups')
  } catch(err) {
    notify.error(err.response?.data?.message || 'Failed to create group')
  }
}
</script>
