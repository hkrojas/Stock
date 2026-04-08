import apiClient from "@/utils/apiClient"

export default {
  list(params = {}) {
    return apiClient.get("/orders/", { params })
  },

  getById(id) {
    return apiClient.get(`/orders/${id}`)
  },

  create(buildingId) {
    return apiClient.post("/orders/", { building_id: buildingId })
  },

  addItem(orderId, payload) {
    return apiClient.post(`/orders/${orderId}/items`, payload)
  },

  removeItem(orderId, itemId) {
    return apiClient.delete(`/orders/${orderId}/items/${itemId}`)
  },

  updateItem(orderId, itemId, payload) {
    return apiClient.post(`/orders/${orderId}/items/${itemId}/update`, payload)
  },

  updateStatus(orderId, action) {
    // action: submit, reopen, cancel, receive
    return apiClient.post(`/orders/${orderId}/${action}`)
  },

  getConsumptionReport(buildingId) {
    return apiClient.get("/orders/consumption-report", {
      params: buildingId ? { building_id: buildingId } : {},
    })
  },
}
