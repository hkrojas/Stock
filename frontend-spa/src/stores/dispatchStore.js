import { ref } from "vue"
import { defineStore } from "pinia"
import dispatchApi from "@/api/dispatch.api"
import purchasesApi from "@/api/purchases.api"

export const useDispatchStore = defineStore("dispatch", () => {
  const pendingOrders = ref([])
  const history = ref({ batches: [], orders: [] })
  const currentBatch = ref(null)
  const currentPicking = ref(null)
  const purchases = ref([])
  const currentPurchase = ref(null)
  const isLoading = ref(false)
  const isConsolidating = ref(false)
  const isConfirmingBatch = ref(false)
  const isRejectingOrder = ref(false)
  const isExporting = ref(false)
  const isPurchasing = ref(false)
  const error = ref("")

  async function fetchPendingOrders() {
    isLoading.value = true
    error.value = ""

    try {
      const { data } = await dispatchApi.getPendingOrders()
      pendingOrders.value = data
      return data
    } catch (requestError) {
      error.value = requestError.message
      return null
    } finally {
      isLoading.value = false
    }
  }

  async function consolidateOrders(orderIds) {
    if (isConsolidating.value) return
    isConsolidating.value = true
    error.value = ""

    try {
      const { data } = await dispatchApi.consolidate(orderIds)
      return data
    } catch (requestError) {
      error.value = requestError.message
      throw requestError
    } finally {
      isConsolidating.value = false
    }
  }

  async function fetchHistory() {
    isLoading.value = true
    error.value = ""

    try {
      const { data } = await dispatchApi.getHistory()
      history.value = data
      return data
    } catch (requestError) {
      error.value = requestError.message
      return null
    } finally {
      isLoading.value = false
    }
  }

  async function fetchBatchDetail(batchId) {
    isLoading.value = true
    error.value = ""

    try {
      const { data } = await dispatchApi.getBatchDetail(batchId)
      currentBatch.value = data
      return data
    } catch (requestError) {
      error.value = requestError.message
      return null
    } finally {
      isLoading.value = false
    }
  }

  async function fetchPicking(batchId) {
    isLoading.value = true
    error.value = ""

    try {
      const { data } = await dispatchApi.getPicking(batchId)
      currentPicking.value = data
      return data
    } catch (requestError) {
      error.value = requestError.message
      return null
    } finally {
      isLoading.value = false
    }
  }

  async function confirmBatch(batchId) {
    if (isConfirmingBatch.value) return
    isConfirmingBatch.value = true
    error.value = ""

    try {
      const { data } = await dispatchApi.confirmBatch(batchId)
      return data
    } catch (requestError) {
      error.value = requestError.message
      throw requestError
    } finally {
      isConfirmingBatch.value = false
    }
  }

  async function rejectOrder(batchId, orderId, rejectionNote = "") {
    if (isRejectingOrder.value) return
    isRejectingOrder.value = true
    error.value = ""

    try {
      const { data } = await dispatchApi.rejectOrder(batchId, orderId, rejectionNote)
      return data
    } catch (requestError) {
      error.value = requestError.message
      throw requestError
    } finally {
      isRejectingOrder.value = false
    }
  }

  async function exportBatch(batchId, kind = "consolidated") {
    isExporting.value = true
    error.value = ""

    try {
      const response = await dispatchApi.exportBatch(batchId, kind)
      const header = response.headers["content-disposition"] ?? ""
      const filenameMatch = header.match(/filename=([^;]+)/i)
      const fallback = kind === "buildings" ? `distribucion_edificios_lote_${batchId}.pdf` : `consolidado_lote_${batchId}.pdf`

      return {
        blob: response.data,
        filename: filenameMatch?.[1]?.replace(/"/g, "") ?? fallback,
      }
    } catch (requestError) {
      error.value = requestError.message
      throw requestError
    } finally {
      isExporting.value = false
    }
  }

  async function fetchPurchases() {
    isLoading.value = true
    error.value = ""

    try {
      const { data } = await purchasesApi.list()
      purchases.value = data
      return data
    } catch (requestError) {
      error.value = requestError.message
      return null
    } finally {
      isLoading.value = false
    }
  }

  async function fetchPurchase(purchaseId) {
    isLoading.value = true
    error.value = ""

    try {
      const { data } = await purchasesApi.getById(purchaseId)
      currentPurchase.value = data
      return data
    } catch (requestError) {
      error.value = requestError.message
      return null
    } finally {
      isLoading.value = false
    }
  }

  async function createPurchase(payload) {
    if (isPurchasing.value) return
    isPurchasing.value = true
    error.value = ""

    try {
      const { data } = await purchasesApi.create(payload)
      purchases.value = [data, ...purchases.value]
      return data
    } catch (requestError) {
      error.value = requestError.message
      throw requestError
    } finally {
      isPurchasing.value = false
    }
  }

  return {
    pendingOrders,
    history,
    currentBatch,
    currentPicking,
    purchases,
    currentPurchase,
    isLoading,
    isConsolidating,
    isConfirmingBatch,
    isRejectingOrder,
    isExporting,
    isPurchasing,
    error,
    fetchPendingOrders,
    consolidateOrders,
    fetchHistory,
    fetchBatchDetail,
    fetchPicking,
    confirmBatch,
    rejectOrder,
    exportBatch,
    fetchPurchases,
    fetchPurchase,
    createPurchase,
  }
})

