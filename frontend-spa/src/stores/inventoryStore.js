import { ref } from "vue"
import { defineStore } from "pinia"
import inventoryApi from "@/api/inventory.api"
import ordersApi from "@/api/orders.api"

export const useInventoryStore = defineStore("inventory", () => {
  const items = ref([])
  const consumptionRows = ref([])
  const isLoading = ref(false)
  const isSubmittingEntry = ref(false)
  const isConsuming = ref(false)
  const isAdjusting = ref(false)
  const error = ref("")

  async function fetchInventory(buildingId) {
    isLoading.value = true
    error.value = ""

    try {
      const { data } = await inventoryApi.list(buildingId)
      items.value = data
      return data
    } catch (requestError) {
      error.value = requestError.message
      return null
    } finally {
      isLoading.value = false
    }
  }

  async function addInventory(payload) {
    if (isSubmittingEntry.value) return
    isSubmittingEntry.value = true
    error.value = ""

    try {
      const { data } = await inventoryApi.add(payload)
      return data
    } catch (requestError) {
      error.value = requestError.message
      throw requestError
    } finally {
      isSubmittingEntry.value = false
    }
  }

  async function consumeInventory(itemId, payload) {
    if (isConsuming.value) return
    isConsuming.value = true
    error.value = ""

    try {
      const { data } = await inventoryApi.consume(itemId, payload)
      items.value = items.value.map((item) => (item.id === data.id ? data : item))
      return data
    } catch (requestError) {
      error.value = requestError.message
      throw requestError
    } finally {
      isConsuming.value = false
    }
  }

  async function adjustInventory(itemId, payload) {
    if (isAdjusting.value) return
    isAdjusting.value = true
    error.value = ""

    try {
      const { data } = await inventoryApi.adjust(itemId, payload)
      items.value = items.value.map((item) => (item.id === data.id ? data : item))
      return data
    } catch (requestError) {
      error.value = requestError.message
      throw requestError
    } finally {
      isAdjusting.value = false
    }
  }

  async function fetchConsumptionReport(buildingId) {
    isLoading.value = true
    error.value = ""

    try {
      const { data } = await ordersApi.getConsumptionReport(buildingId)
      consumptionRows.value = data
      return data
    } catch (requestError) {
      error.value = requestError.message
      return null
    } finally {
      isLoading.value = false
    }
  }

  return {
    items,
    consumptionRows,
    isLoading,
    isSubmittingEntry,
    isConsuming,
    isAdjusting,
    error,
    fetchInventory,
    addInventory,
    consumeInventory,
    adjustInventory,
    fetchConsumptionReport,
  }
})

