<template>
  <div>
    <h3 class="q-mb-lg">Okta Login</h3>
    <p class="text-body1 q-mb-lg">
      This is a login page using the <a href="https://github.com/okta/okta-vue" target="_blank">okta-vue</a> library.
      The login button below will redirect you to an Okta login page.  After sucessful login, the Okta token will be
      passed in API calls as the bearer token.  This can be verified by testing some endpoints on the API page and
      checking the network tab in chrome dev tools.
      <br><br>
      Please note that this Okta login logic is completely seperate from the login form on the main page that uses session cookies.
      <br><br>
      Below is a test user that you can use: <br>
      User: test@test.com <br>
      Password: dioptrapass 
      <br><br>
      <span class="text-bold">Okta Status: </span>
      You are currently <span class="text-primary text-bold">{{ authState.isAuthenticated ? 'logged in' : 'logged out'  }}</span>.
    </p>


    <q-btn
      v-if='authState && authState.isAuthenticated'
      label="Logout"
      class="q-mb-xl"
      color="primary"
      icon="logout"
      @click='logout'
    />
    <q-btn
      v-else
      label="Login"
      class="q-mb-xl"
      color="primary"
      icon="login"
      @click='login'
    />
  </div>
</template>

<script setup lang="ts">
  import { useAuth } from '@okta/okta-vue';
  import { ShallowRef, inject, computed } from 'vue';
  import { AuthState } from '@okta/okta-auth-js';

  const authState = inject<ShallowRef<AuthState>>('okta.authState')

  const $auth = useAuth();

  console.log('authState = ', authState)
  console.log('$auth = ', $auth)

  console.log('ID Token = ', authState.value.idToken.idToken)

  const login = async () => {
    await $auth.signInWithRedirect({ originalUri: '/okta' });
  };

  const logout = async () => {
    await $auth.signOut({postLogoutRedirectUri: window.location.origin + '/okta'});
  };

</script>