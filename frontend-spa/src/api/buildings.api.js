import apiClient from "@/utils/apiClient"

export default {
  list() {
    return apiClient.get("/buildings/")
  },

  listUnassigned() {
    return apiClient.get("/buildings/unassigned")
  },

  getById(id) {
    return apiClient.get(`/buildings/${id}`)
  },

  create(payload) {
    return apiClient.post("/buildings/", payload)
  },

  update(id, payload) {
    return apiClient.put(`/buildings/${id}`, payload)
  },

  delete(id) {
    return apiClient.delete(`/buildings/${id}`)
  },

  assignToAdmin(adminId, buildingIds) {
    return apiClient.post("/buildings/assign", {
      admin_id: adminId,
      building_ids: buildingIds,
    })
  },
}
