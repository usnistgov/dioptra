import './assets/main.css';

import { createApp } from 'vue';
import App from './App.vue';
import router from './router';

import { OktaAuth } from '@okta/okta-auth-js'
import OktaVue from '@okta/okta-vue'

const oktaAuth = new OktaAuth({
  issuer: 'https://dev-81274319.okta.com/oauth2/default',
  clientId: '0oaedeisi58ioN2hq5d7',
  redirectUri: window.location.origin + '/login/callback',
  scopes: ['openid', 'profile', 'email']
})

import { createPinia } from 'pinia';
const pinia = createPinia();

import { Quasar, Notify, Loading } from 'quasar';

// Import icon libraries
import '@quasar/extras/material-icons/material-icons.css';

// Import Quasar css
import 'quasar/src/css/index.sass';

const app = createApp(App);
app.use(OktaVue, { oktaAuth })

app.use(router);
app.use(pinia);

app.use(Quasar, {
  plugins: {
    // import Quasar plugins and add here
    Notify,
    Loading,
  },
});

app.mount('#app');
