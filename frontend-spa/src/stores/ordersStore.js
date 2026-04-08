import { ref } from "vue"
import { defineStore } from "pinia"
import ordersApi from "@/api/orders.api"

export const useOrdersStore = defineStore("orders", () => {
  const orders = ref([])
  const currentOrder = ref(null)
  const isLoading = ref(false)
  const isCreatingOrder = ref(false)
  const isUpdatingItem = ref(false)
  const isSubmittingOrder = ref(false)
  const isReopeningOrder = ref(false)
  const isCancellingOrder = ref(false)
  const isReceivingOrder = ref(false)
  const error = ref("")

  async function fetchOrders(params = {}) {
    isLoading.value = true
    error.value = ""

    try {
      const { data: result } = await ordersApi.list(params)
      orders.value = result
      return result
    } catch (requestError) {
      error.value = requestError.message
      return null
    } finally {
      isLoading.value = false
    }
  }

  async function fetchOrder(orderId) {
    isLoading.value = true
    error.value = ""

    try {
      const { data: result } = await ordersApi.getById(orderId)
      currentOrder.value = result
      return result
    } catch (requestError) {
      error.value = requestError.message
      return null
    } finally {
      isLoading.value = false
    }
  }

  async function createOrder(buildingId) {
    if (isCreatingOrder.value) return
    isCreatingOrder.value = true
    error.value = ""

    try {
      const { data: result } = await ordersApi.create(buildingId)
      currentOrder.value = result
      return result
    } catch (requestError) {
      error.value = requestError.message
      throw requestError
    } finally {
      isCreatingOrder.value = false
    }
  }

  async function addItem(orderId, payload) {
    if (isUpdatingItem.value) return
    isUpdatingItem.value = true
    error.value = ""

    try {
      await ordersApi.addItem(orderId, payload)
      return await fetchOrder(orderId)
    } catch (requestError) {
      error.value = requestError.message
      throw requestError
    } finally {
      isUpdatingItem.value = false
    }
  }

  async function removeItem(orderId, itemId) {
    if (isUpdatingItem.value) return
    isUpdatingItem.value = true
    error.value = ""

    try {
      await ordersApi.removeItem(orderId, itemId)
      return await fetchOrder(orderId)
    } catch (requestError) {
      error.value = requestError.message
      throw requestError
    } finally {
      isUpdatingItem.value = false
    }
  }

  async function updateItem(orderId, itemId, payload) {
    if (isUpdatingItem.value) return
    isUpdatingItem.value = true
    error.value = ""

    try {
      await ordersApi.updateItem(orderId, itemId, payload)
      return await fetchOrder(orderId)
    } catch (requestError) {
      error.value = requestError.message
      throw requestError
    } finally {
      isUpdatingItem.value = false
    }
  }

  async function updateOrderStatus(orderId, action) {
    const stateMap = {
      submit: isSubmittingOrder,
      reopen: isReopeningOrder,
      cancel: isCancellingOrder,
      receive: isReceivingOrder,
    }
    const state = stateMap[action]
    if (state?.value) return
    if (state) state.value = true
    error.value = ""

    try {
      await ordersApi.updateStatus(orderId, action)
      return await fetchOrder(orderId)
    } catch (requestError) {
      error.value = requestError.message
      throw requestError
    } finally {
      if (state) state.value = false
    }
  }

  return {
    orders,
    currentOrder,
    isLoading,
    isCreatingOrder,
    isUpdatingItem,
    isSubmittingOrder,
    isReopeningOrder,
    isCancellingOrder,
    isReceivingOrder,
    error,
    fetchOrders,
    fetchOrder,
    createOrder,
    addItem,
    removeItem,
    updateItem,
    updateOrderStatus,
  }
})

