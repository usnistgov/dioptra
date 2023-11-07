<template>
  <q-card bordered class="q-pa-lg" style="min-width: 600px;">
    <q-card-section class="text-center">
        <div class="text-h5 text-weight-bold">Register</div>
        <div>Register a new user account</div>
    </q-card-section>
    <q-form @submit="$emit('submit', 'api/user/', 'POST')">
      <q-input
        class="q-py-sm"
        outlined
        label="Username"
        :rules="[requiredRule]"
        :model-value="username"
        @update:model-value="newValue => $emit('update:username', newValue)"
      >
      </q-input>
      <q-input
        class="q-py-md"
        outlined
        label="Password"
        :rules="[requiredRule]"
        :model-value="password"
        @update:model-value="newValue => $emit('update:password', newValue)"
      >
      </q-input>
      <q-input
        class="q-py-sm"
        outlined
        label="Confirm Password"
        :rules="[requiredRule, matchRule]"
        :model-value="confirmPassword"
        @update:model-value="newValue => $emit('update:confirmPassword', newValue)"
      >
      </q-input>
      <q-btn
        color="primary"
        class="full-width q-mt-md"
        type="submit"
      >
        Register
      </q-btn>
      <q-card-section class="text-center q-pt-md">
        <div>Go back to
          <a 
            role="button" 
            class="text-weight-bold text-primary" 
            style="text-decoration: none; cursor: pointer" 
            @click="$emit('update:state', 'login')"
          >
            Login Menu.
          </a>
        </div>
      </q-card-section>
    </q-form>
  </q-card>
</template>

<script setup lang="ts">

  const props = defineProps(['username', 'password', 'confirmPassword', 'state'])
  defineEmits(['update:username', 'update:password', 'update:confirmPassword', 'update:state', 'submit'])

  const requiredRule = (val: string) => (val && val.length > 0) || "This field is required";
  const matchRule = (val: string) => (val && val === props.password) || 'Password mismatch';

</script>