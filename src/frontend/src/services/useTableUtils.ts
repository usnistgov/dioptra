import { ref } from "vue";
import * as api from "@/services/dataApi";
import * as notify from "../notify";
import type { ResourceType, Pagination } from "@/services/dataApi";

type TableRef = {
  refreshTable: () => void;
  updateTotalRows: (totalRows: number) => void;
};

type ResourceRow = {
  id: number;
  name?: string;
};

export function useTableUtils(resourceType: ResourceType) {
  const isLoading = ref(false);
  const rows = ref<ResourceRow[]>([]);
  const selected = ref<ResourceRow[]>([]);
  const tableRef = ref<TableRef | null>(null);
  const showDeleted = ref(false);
  const showDeleteDialog = ref(false);

  async function getData(pagination: Pagination, showDrafts = false) {
    isLoading.value = true;
    try {
      const res = await api.getData(resourceType, pagination, showDrafts, showDeleted.value);
      rows.value = res.data.data;
      tableRef.value?.updateTotalRows(res.data.totalNumResults);
    } catch (err: any) {
      console.log("err = ", err);
      notify.error(err.response?.data?.message ?? "Something went wrong");
    } finally {
      isLoading.value = false;
    }
  }

  async function deleteRow(draft = false) {
    const item = selected.value[0];

    try {
      if (draft) {
        await api.deleteDraft(resourceType, item.id);
      } else {
        await api.deleteItem(resourceType, item.id);
      }
      notify.success(`Successfully deleted '${item.name ?? item.id}'`);
      selected.value = [];
      tableRef.value?.refreshTable();
      showDeleteDialog.value = false;
    } catch (err: any) {
      notify.error(err.response?.data?.message ?? "Something went wrong");
      showDeleteDialog.value = false;
    }
  }

  return {
    rows,
    selected,
    tableRef,
    isLoading,
    showDeleted,
    showDeleteDialog,
    getData,
    deleteRow,
  };
}
