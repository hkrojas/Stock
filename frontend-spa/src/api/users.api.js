import apiClient from "@/utils/apiClient"

export default {
  getMe() {
    return apiClient.get("/users/me")
  },

  list(role = "") {
    return apiClient.get("/users/", {
      params: role ? { role } : {},
    })
  },

  getById(id) {
    return apiClient.get(`/users/${id}`)
  },

  create(payload) {
    return apiClient.post("/users/", payload)
  },

  update(id, payload, queryParams = {}) {
    return apiClient.put(`/users/${id}`, payload, { params: queryParams })
  },

  delete(id) {
    return apiClient.delete(`/users/${id}`)
  },
}
