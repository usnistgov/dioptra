<template>
  <nav v-if="pageCount > 1">
    <ul class="pagination">
      <li class="page-item" :class="{ disabled: currentPage === 1 }">
        <a class="page-link" href="#" aria-label="Previous" @click.prevent="prevPage">
          <span aria-hidden="true">&laquo;</span>
          <span class="sr-only">Previous</span>
        </a>
      </li>
      <li class="page-item" :class="{ active: i === currentPage }" v-for="i in pageCount" :key="i">
        <a class="page-link" href="#" @click.prevent="goToPage(i)">{{ i }}</a>
      </li>
      <li class="page-item" :class="{ disabled: currentPage === pageCount }">
        <a class="page-link" href="#" aria-label="Next" @click.prevent="nextPage">
          <span aria-hidden="true">&raquo;</span>
          <span class="sr-only">Next</span>
        </a>
      </li>
    </ul>
  </nav>
</template>

<script>
export default {
  props: {
    totalItems: {
      type: Number,
      required: true
    },
    itemsPerPage: {
      type: Number,
      default: 10
    },
    currentPage: {
      type: Number,
      default: 1
    }
  },
  computed: {
    pageCount() {
      return Math.ceil(this.totalItems / this.itemsPerPage);
    }
  },
  methods: {
    prevPage() {
      if (this.currentPage > 1) {
        this.$emit('page-change', this.currentPage - 1);
      }
    },
    nextPage() {
      if (this.currentPage < this.pageCount) {
        this.$emit('page-change', this.currentPage + 1);
      }
    },
    goToPage(page) {
      if (page >= 1 && page <= this.pageCount) {
        this.$emit('page-change', page);
      }
    }
  }
};
</script>
