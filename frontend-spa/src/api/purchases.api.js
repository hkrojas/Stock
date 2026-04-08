import apiClient from "@/utils/apiClient"

export default {
  list() {
    return apiClient.get("/purchases/")
  },

  getById(id) {
    return apiClient.get(`/purchases/${id}`)
  },

  create(payload) {
    return apiClient.post("/purchases/", payload)
  },
}
