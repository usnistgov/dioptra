import './assets/main.css'

import { createApp } from 'vue'
import App from './App.vue'
import router from './router'

import { createPinia } from 'pinia'
const pinia = createPinia()

import { Quasar, Notify, Loading } from 'quasar'

// Import icon libraries
import '@quasar/extras/material-icons/material-icons.css'

// Import Quasar css
import 'quasar/src/css/index.sass'

const app = createApp(App)

app.use(router)
app.use(pinia)

app.use(Quasar, {
  plugins: {
    // import Quasar plugins and add here
    Notify,
    Loading,
  },
})

app.mount('#app')
