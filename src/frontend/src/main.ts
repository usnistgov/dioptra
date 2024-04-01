import './assets/main.css'

import { createApp } from 'vue'
import { createPinia } from 'pinia'
import VueCodemirror from 'vue-codemirror'

import { Quasar, AppFullscreen, Loading, Notify } from 'quasar'

// Import icon libraries
import '@quasar/extras/material-icons/material-icons.css'
import '@quasar/extras/material-symbols-outlined/material-symbols-outlined.css'
import '@quasar/extras/fontawesome-v6/fontawesome-v6.css'

// Import Quasar css
import 'quasar/src/css/index.sass'

import App from './App.vue'
import router from './router'

const app = createApp(App)

app.use(Quasar, {
  plugins: {
    AppFullscreen,
    Loading,
    Notify
  },
  config: {
    dark: 'auto'
  }
})

app.use(createPinia())
app.use(router)
app.use(VueCodemirror)

app.mount('#app')
