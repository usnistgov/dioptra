<template>
  <div>
    <h3 class="q-mb-lg">API</h3>
    <p class="text-body1 q-mb-lg">
      To test an endpoint, expand a cetegory and click on the colored button.
      Please note that everything except the Hello endpoints require a login.
    </p>
    <q-list>
      <q-expansion-item
      v-for="category in endpointCategories"
        :key="category"
        :label="`${category} Endpoints`"
        header-class="text-bold shadow-2 text-h6"
        class="q-mb-md"
      >
        <q-list bordered separator>
          <q-item
            v-for="endpoint in endpoints.filter(item => item.category === category)"
            :key="endpoint.url"
            class="column"
          >
            <div>
              <q-btn
                :color="colors[endpoint.method]"
                class="text-bold q-mr-md"
                style="width: 80px;"
                :label="endpoint.method"
                @click="call(endpoint)"
              />
              <span class="text-bold text-body1 q-mr-sm" style="font-family: monospace;">
                {{ endpoint.url }}
              </span>
              {{ endpoint.description }}
            </div>
            <div
              v-if="endpoint.responseStatus"
              class="q-mt-sm"
            >
              <div class="q-mb-sm">
                Response Code:
                <span class="text-bold q-mr-sm" :style="endpoint.responseStatus === 200 ? 'color: green;' : 'color: red;' ">
                  {{ endpoint.responseStatus }}
                </span>
                <q-btn 
                  label="Clear Response"
                  outline 
                  color="primary" 
                  class="text-bold"
                  @click="endpoint.responseStatus = null; endpoint.responseBody = '';"
                />
              </div>
              <q-input
                label="Response Body"
                v-model="endpoint.responseBody"
                filled
                autogrow
                class="shadow-2"
                type="textarea"
              />
            </div>
          </q-item>
        </q-list>
      </q-expansion-item>
    </q-list>
  </div>
</template>

<script setup lang="ts">
  import { ref, computed } from 'vue';

  const endpointCategories = computed(() => {
    let categories: string[] = [];
    endpoints.forEach((endpoint) => {
      if (!categories.includes(endpoint.category)) {
        categories.push(endpoint.category)
      }
    })
    return categories;
  })

  type Endpoint = {
    method: string;
    url: string;
    description: string;
    category: string;
    responseStatus?: number | null;
    responseBody?: string;
  };
  const endpoints: Endpoint[] = ref([
    { method: 'PUT', url: '/api/hello/', description: 'Responds "Hello, World!"', category: 'Hello'},
    { method: 'GET', url: '/api/hello/', description: 'Responds "Hello, World!"', category: 'Hello'},
    { method: 'POST', url: '/api/hello/', description: 'Responds "Hello, World!"', category: 'Hello'},
    { method: 'PUT', url: '/api/test/', description: "Responds with the server's secret key", category: 'Test'},
    { method: 'GET', url: '/api/test/', description: "Responds with the server's secret key", category: 'Test'},
    { method: 'POST', url: '/api/test/', description: "Responds with the server's secret key", category: 'Test'},
    { method: 'PUT', url: '/api/world/', description: "Responds with the user's information", category: 'World'},
    { method: 'GET', url: '/api/world/', description: "Responds with the user's information", category: 'World'},
    { method: 'POST', url: '/api/world/', description: "Responds with the user's information", category: 'World'},
    { method: 'PUT', url: '/api/foo/', description: 'Responds with "bar"', category: 'Foo'},
    { method: 'GET', url: '/api/foo/', description: 'Responds with "bar"', category: 'Foo'},
    { method: 'POST', url: '/api/foo/', description: 'Echoes the JSON playload in the request', category: 'Foo'},
  ]).value;
  interface Colors {
    [key: string]: string;
  }
  const colors: Colors = {
    PUT: 'orange',
    GET: 'primary',
    POST: 'green'
  }

  function call(endpoint: Endpoint) {
    fetch(endpoint.url, {method: endpoint.method})
    .then(res => {
      console.log('res = ', res);
      endpoint.responseStatus = res.status;
      return res.json()
    })
    .then(data => {
      console.log('data = ', data);
      endpoint.responseBody = JSON.stringify(data, null, 2);
    })
    .catch(err => {
      console.warn(err)
    })
  }

</script>