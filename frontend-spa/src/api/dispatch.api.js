import apiClient from "@/utils/apiClient"

export default {
  getPendingOrders() {
    return apiClient.get("/dispatch/pending-orders")
  },

  consolidate(orderIds) {
    return apiClient.post("/dispatch/consolidate", orderIds)
  },

  getHistory() {
    return apiClient.get("/dispatch/history")
  },

  getBatchDetail(id) {
    return apiClient.get(`/dispatch/batch/${id}`)
  },

  getPicking(batchId) {
    return apiClient.get(`/dispatch/batch/${batchId}/picking`)
  },

  confirmBatch(batchId) {
    return apiClient.post(`/dispatch/batch/${batchId}/confirm`)
  },

  rejectOrder(batchId, orderId, rejectionNote = "") {
    return apiClient.post(`/dispatch/batch/${batchId}/reject-order/${orderId}`, null, {
      params: rejectionNote ? { rejection_note: rejectionNote } : {},
    })
  },

  exportBatch(batchId, kind = "consolidated") {
    const endpoint =
      kind === "buildings"
        ? `/dispatch/batch/${batchId}/export/buildings`
        : `/dispatch/batch/${batchId}/export/consolidated`

    return apiClient.get(endpoint, { responseType: "blob" })
  },
}
