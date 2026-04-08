import apiClient from "@/utils/apiClient"

export default {
  getSuperadminDashboard() {
    return apiClient.get("/analytics/superadmin")
  },

  getManagerDashboard() {
    return apiClient.get("/analytics/manager")
  },

  getAdminDashboard() {
    return apiClient.get("/analytics/admin")
  },
}
