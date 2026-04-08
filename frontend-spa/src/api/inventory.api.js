import apiClient from "@/utils/apiClient"

export default {
  list(buildingId = null) {
    return apiClient.get("/inventory/", {
      params: buildingId ? { building_id: buildingId } : {},
    })
  },

  add(payload) {
    return apiClient.post("/inventory/", payload)
  },

  consume(itemId, payload) {
    return apiClient.post(`/inventory/${itemId}/consume`, payload)
  },

  adjust(itemId, payload) {
    return apiClient.post(`/inventory/${itemId}/adjust`, payload)
  },
}
