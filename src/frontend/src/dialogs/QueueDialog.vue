<template>
  <DialogComponent 
    v-model:showDialog="showDialog"
    v-model:history="history"
    @emitSubmit="emitAddOrEdit"
    @emitSaveDraft="saveDraft"
    :hideDraftBtn="editQueue ? true : false"
    :showHistoryToggle="editQueue && !Object.hasOwn(editQueue, 'payload')"
    :disableConfirm="history"
  >
    <template #title>
      <label id="modalTitle">
        {{editQueue ? 'Edit Queue' : 'Register Queue'}}
      </label>
    </template>
    <div class="row no-wrap">
      <!-- this is the form col -->
      <div 
        style="width: 500px;"
        :style="{ 
          pointerEvents: history ? 'none' : 'auto', 
          opacity: history ? .65 : 1, 
          cursor: history ? 'not-allowed' : 'default' 
        }"
      >
        <div class="row items-center">
          <label class="col-3 q-mb-lg" id="queueName">
            Queue Name:
          </label>
          <q-input 
            class="col q-mb-xs" 
            outlined 
            dense 
            v-model.trim="name"  
            autofocus 
            :rules="[requiredRule]" 
            aria-labelledby="queueName"
            aria-required="true"
          />
        </div>
        <div class="row items-center q-mb-xs">
          <label class="col-3 q-mb-lg" id="pluginGroup">
            Group:
          </label>
          <q-select
            class="col"
            outlined 
            v-model="group" 
            :options="store.groups"
            option-label="name"
            option-value="id"
            emit-value
            map-options
            dense
            :rules="[requiredRule]"
            aria-labelledby="pluginGroup"
            aria-required="true"
          />
        </div>
        <div class="row items-center">
          <label class="col-3" id="description">
            Description:
          </label>
          <q-input
            class="col"
            v-model.trim="description"
            outlined
            type="textarea"
            aria-labelledby="description"
          />
        </div>
        <!-- <q-inner-loading :showing="history" size="0px" /> -->
      </div>
      <!-- this is the history col -->
      <q-card 
        v-if="history" 
        style="width: 240px; max-height: 263px; overflow: auto;"
        flat
        bordered
        class="q-ml-sm col"
      >
        <q-list bordered separator>
          <q-item
            v-for="(snapshot, i) in snapshots"
            tag="label" 
            v-ripple
            dense
            clickable
            @click="loadSnapshot(snapshot, i)"
            @keydown="keydown"
            :class="`${getSelectedColor(selectedSnapshotIndex === i)} cursor-pointer` " 
          >
            <!-- <q-item-section avatar>
              <q-radio
                v-model="selectedSnapshot"
                :val="snapshot"
                @update:model-value="loadSnapshot(snapshot)"
              />
            </q-item-section> -->
            <q-item-section>
              <q-item-label>
                {{
                  new Intl.DateTimeFormat('en-US', { 
                    year: '2-digit', 
                    month: '2-digit', 
                    day: '2-digit', 
                    hour: 'numeric', 
                    minute: 'numeric', 
                    hour12: true 
                  }).format(new Date(snapshot.snapshotCreatedOn))
                }}
                <q-chip
                  v-if="snapshot.latestSnapshot"
                  label="latest"
                  size="md"
                  dense
                  color="orange"
                  text-color="white"
                />
              </q-item-label>
            </q-item-section>
          </q-item>
        </q-list>
      </q-card>
    </div>
  </DialogComponent>
</template>

<script setup>
  import { ref, watch, computed } from 'vue'
  import DialogComponent from './DialogComponent.vue'
  import { useLoginStore } from '@/stores/LoginStore.ts'
  import * as api from '@/services/dataApi'
  import { useQuasar } from 'quasar'

  const store = useLoginStore()

  const props = defineProps(['editQueue'])
  const emit = defineEmits(['addQueue', 'updateQueue', 'saveDraft'])

  function requiredRule(val) {
    return (!!val) || "This field is required"
  }

  const showDialog = defineModel()

  const name = ref('')
  const group = ref('')
  const description = ref('')

  function loadSnapshot(snapshot, index) {
    selectedSnapshotIndex.value = index
    name.value = snapshot.name
    group.value = snapshot.group
    description.value = snapshot.description
  }

  watch(showDialog, (newVal) => {
    if(newVal) {
      name.value = props.editQueue.name
      description.value = props.editQueue.description
      group.value = props.editQueue.group
    }
    else {
      name.value = ''
      description.value = ''
      history.value = false
      snapshots.value = []
    }
  })

  function emitAddOrEdit() {
    if(props.editQueue) {
      emit(
        'updateQueue', 
        name.value, 
        props.editQueue.id, 
        description.value, 
        Object.hasOwn(props.editQueue, 'payload') ? true : false
      )
    } else {
      emit('addQueue', name.value, description.value)
    }
  }

  function saveDraft() {
    emit('saveDraft', name.value, description.value, props.editQueue.id)
  }

  const history = ref(false)

  const snapshots = ref([])
  const selectedSnapshot = ref()
  const selectedSnapshotIndex = ref()

  async function getSnapshots() {
    try {
      const res = await api.getSnapshots('queues', props.editQueue.id)
      snapshots.value = res.data.data.reverse()
      selectedSnapshot.value = snapshots.value[0]
      selectedSnapshotIndex.value = 0
      loadSnapshot(snapshots.value[0], 0)
    } catch(err) {
      console.warn(err)
    }
  }

  watch(history, (newVal) => {
    if(newVal) {
      getSnapshots()
    } else {
      selectedSnapshotIndex.value = 0
      name.value = props.editQueue.name
      description.value = props.editQueue.description
      group.value = props.editQueue.group
    }
  })

  const $q = useQuasar()

  const darkMode = computed(() => {
    if($q.dark.mode === 'auto') {
      return window.matchMedia('(prefers-color-scheme: dark)').matches
    }
    return $q.dark.mode
  })

  function getSelectedColor(selected) {
    if(darkMode.value && selected) return 'bg-deep-purple-10'
    else if(selected) return 'bg-blue-grey-2'
  }

  function keydown(event) {
    if(event.key === 'ArrowUp' && selectedSnapshotIndex.value > 0) {
      const newIndex = selectedSnapshotIndex.value - 1
      loadSnapshot(snapshots.value[newIndex], newIndex)
    }
    else if(event.key === 'ArrowDown' && selectedSnapshotIndex.value < snapshots.value.length - 1) {
      const newIndex = selectedSnapshotIndex.value + 1
      loadSnapshot(snapshots.value[newIndex], newIndex)
    }
  }


</script>