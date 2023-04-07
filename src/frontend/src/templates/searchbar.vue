<template>
  <form class="form-inline my-2 my-lg-0" @submit.prevent="handleSearch">
    <input class="form-control mr-sm-2" type="search" placeholder="Search" aria-label="Search" v-model="searchTerm">
    <button class="btn btn-outline-success my-2 my-sm-0" type="submit">Search</button>
  </form>
</template>

<script>
export default {
  data() {
    return {
      searchTerm: ''
    };
  },
  methods: {
    handleSearch() {
      this.$emit('search', this.searchTerm);
    }
  }
};
</script>
