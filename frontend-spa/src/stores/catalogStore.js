import { ref } from "vue"
import { defineStore } from "pinia"

import apiClient from "@/utils/apiClient"

export const useCatalogStore = defineStore("catalog", () => {
  const products = ref([])
  const currentProduct = ref(null)
  const admins = ref([])
  const currentAdmin = ref(null)
  const buildings = ref([])
  const unassignedBuildings = ref([])
  const currentBuilding = ref(null)
  const csvUploads = ref([])
  const lastCsvUpload = ref(null)
  const isLoading = ref(false)
  const isSubmittingProduct = ref(false)
  const isSubmittingAdmin = ref(false)
  const isSubmittingBuilding = ref(false)
  const isTogglingProduct = ref(false)
  const isUploadingCsv = ref(false)
  const isDeletingAdmin = ref(false)
  const isDeletingBuilding = ref(false)
  const isAssigningBuildings = ref(false)
  const isDeletingCsv = ref(false)
  const isPreviewingProduct = ref(false)
  const isSyncingProduct = ref(false)
  const submitLoading = ref(false) // Generic fallback
  const error = ref("")

  async function fetchProducts(query = "") {
    isLoading.value = true
    error.value = ""

    try {
      const { data } = await apiClient.get("/catalog/all", {
        params: query ? { q: query } : {},
      })
      products.value = data
      return data
    } catch (requestError) {
      error.value = requestError.message
      return null
    } finally {
      isLoading.value = false
    }
  }

  async function fetchProduct(productId) {
    isLoading.value = true
    error.value = ""

    try {
      const { data } = await apiClient.get(`/catalog/${productId}`)
      currentProduct.value = data
      return data
    } catch (requestError) {
      error.value = requestError.message
      return null
    } finally {
      isLoading.value = false
    }
  }

  async function createProduct(payload) {
    if (isSubmittingProduct.value) return
    isSubmittingProduct.value = true
    error.value = ""

    try {
      const { data } = await apiClient.post("/catalog/", payload)
      if (Array.isArray(products.value)) {
        products.value = [data, ...products.value]
      }
      return data
    } catch (requestError) {
      error.value = requestError.message
      throw requestError
    } finally {
      isSubmittingProduct.value = false
    }
  }

  async function updateProduct(productId, payload) {
    if (isSubmittingProduct.value) return
    isSubmittingProduct.value = true
    error.value = ""

    try {
      const { data } = await apiClient.put(`/catalog/${productId}`, payload)
      currentProduct.value = data
      if (Array.isArray(products.value)) {
        products.value = products.value.map((product) => (product.id === data.id ? data : product))
      }
      return data
    } catch (requestError) {
      error.value = requestError.message
      throw requestError
    } finally {
      isSubmittingProduct.value = false
    }
  }

  async function toggleProduct(productId) {
    if (isTogglingProduct.value) return
    isTogglingProduct.value = true
    error.value = ""

    try {
      const { data } = await apiClient.patch(`/catalog/${productId}/toggle`)
      products.value = products.value.map((product) => (product.id === data.id ? data : product))
      return data
    } catch (requestError) {
      error.value = requestError.message
      throw requestError
    } finally {
      isTogglingProduct.value = false
    }
  }

  async function uploadCsv(file) {
    if (isUploadingCsv.value) return
    isUploadingCsv.value = true
    error.value = ""

    try {
      const formData = new FormData()
      formData.append("file", file)
      const { data } = await apiClient.post("/catalog/import-csv", formData, {
        headers: {
          "Content-Type": "multipart/form-data",
        },
      })
      lastCsvUpload.value = data
      await fetchCsvUploads()
      return data
    } catch (requestError) {
      error.value = requestError.message
      throw requestError
    } finally {
      isUploadingCsv.value = false
    }
  }

  async function fetchAdmins(role = "") {
    isLoading.value = true
    error.value = ""

    try {
      const { data } = await apiClient.get("/users/", {
        params: role ? { role } : {},
      })
      admins.value = data
      return data
    } catch (requestError) {
      error.value = requestError.message
      return null
    } finally {
      isLoading.value = false
    }
  }

  async function fetchAdmin(adminId) {
    isLoading.value = true
    error.value = ""

    try {
      const { data } = await apiClient.get(`/users/${adminId}`)
      currentAdmin.value = data
      return data
    } catch (requestError) {
      error.value = requestError.message
      return null
    } finally {
      isLoading.value = false
    }
  }

  async function createAdmin(payload) {
    if (isSubmittingAdmin.value) return
    isSubmittingAdmin.value = true
    error.value = ""

    try {
      const { data } = await apiClient.post("/users/", payload)
      if (Array.isArray(admins.value)) {
        admins.value = [data, ...admins.value]
      }
      return data
    } catch (requestError) {
      error.value = requestError.message
      throw requestError
    } finally {
      isSubmittingAdmin.value = false
    }
  }

  async function updateAdmin(adminId, payload, options = {}) {
    if (isSubmittingAdmin.value) return
    isSubmittingAdmin.value = true
    error.value = ""

    try {
      const params = {}
      if (Array.isArray(options.buildingIds)) {
        params.building_ids = options.buildingIds
      }
      if (options.clearBuildings) {
        params.clear_buildings = true
      }

      const { data } = await apiClient.put(`/users/${adminId}`, payload, { params })
      currentAdmin.value = data
      if (Array.isArray(admins.value)) {
        admins.value = admins.value.map((admin) => (admin.id === data.id ? data : admin))
      }
      return data
    } catch (requestError) {
      error.value = requestError.message
      throw requestError
    } finally {
      isSubmittingAdmin.value = false
    }
  }

  async function deleteAdmin(adminId) {
    if (isDeletingAdmin.value) return
    isDeletingAdmin.value = true
    error.value = ""

    try {
      const { data } = await apiClient.delete(`/users/${adminId}`)
      admins.value = admins.value.filter((admin) => admin.id !== adminId)
      return data
    } catch (requestError) {
      error.value = requestError.message
      throw requestError
    } finally {
      isDeletingAdmin.value = false
    }
  }

  async function fetchBuildings() {
    isLoading.value = true
    error.value = ""

    try {
      const { data } = await apiClient.get("/buildings/")
      buildings.value = data
      return data
    } catch (requestError) {
      error.value = requestError.message
      return null
    } finally {
      isLoading.value = false
    }
  }

  async function fetchBuilding(buildingId) {
    isLoading.value = true
    error.value = ""

    try {
      const { data } = await apiClient.get(`/buildings/${buildingId}`)
      currentBuilding.value = data
      return data
    } catch (requestError) {
      error.value = requestError.message
      return null
    } finally {
      isLoading.value = false
    }
  }

  async function fetchUnassignedBuildings() {
    isLoading.value = true
    error.value = ""

    try {
      const { data } = await apiClient.get("/buildings/unassigned")
      unassignedBuildings.value = data
      return data
    } catch (requestError) {
      error.value = requestError.message
      return null
    } finally {
      isLoading.value = false
    }
  }

  async function createBuilding(payload) {
    if (isSubmittingBuilding.value) return
    isSubmittingBuilding.value = true
    error.value = ""

    try {
      const { data } = await apiClient.post("/buildings/", payload)
      if (Array.isArray(buildings.value)) {
        buildings.value = [data, ...buildings.value]
      }
      return data
    } catch (requestError) {
      error.value = requestError.message
      throw requestError
    } finally {
      isSubmittingBuilding.value = false
    }
  }

  async function updateBuilding(buildingId, payload) {
    if (isSubmittingBuilding.value) return
    isSubmittingBuilding.value = true
    error.value = ""

    try {
      const { data } = await apiClient.put(`/buildings/${buildingId}`, payload)
      currentBuilding.value = data
      if (Array.isArray(buildings.value)) {
        buildings.value = buildings.value.map((building) => (building.id === data.id ? data : building))
      }
      return data
    } catch (requestError) {
      error.value = requestError.message
      throw requestError
    } finally {
      isSubmittingBuilding.value = false
    }
  }

  async function deleteBuilding(buildingId) {
    if (isDeletingBuilding.value) return
    isDeletingBuilding.value = true
    error.value = ""

    try {
      const { data } = await apiClient.delete(`/buildings/${buildingId}`)
      buildings.value = buildings.value.filter((building) => building.id !== buildingId)
      return data
    } catch (requestError) {
      error.value = requestError.message
      throw requestError
    } finally {
      isDeletingBuilding.value = false
    }
  }

  async function assignBuildings(adminId, buildingIds) {
    if (isAssigningBuildings.value) return
    isAssigningBuildings.value = true
    error.value = ""

    try {
      const { data } = await apiClient.post("/buildings/assign", {
        admin_id: adminId,
        building_ids: buildingIds,
      })
      return data
    } catch (requestError) {
      error.value = requestError.message
      throw requestError
    } finally {
      isAssigningBuildings.value = false
    }
  }

  async function fetchCsvUploads() {
    isLoading.value = true
    error.value = ""

    try {
      const { data } = await apiClient.get("/catalog/uploads")
      csvUploads.value = data
      return data
    } catch (requestError) {
      error.value = requestError.message
      return null
    } finally {
      isLoading.value = false
    }
  }

  async function deleteCsvUpload(uploadId) {
    if (isDeletingCsv.value) return
    isDeletingCsv.value = true
    error.value = ""

    try {
      const { data } = await apiClient.delete(`/catalog/uploads/${uploadId}`)
      csvUploads.value = csvUploads.value.filter((upload) => upload.id !== uploadId)
      return data
    } catch (requestError) {
      error.value = requestError.message
      throw requestError
    } finally {
      isDeletingCsv.value = false
    }
  }

  async function previewProduct(sourceUrl) {
    if (isPreviewingProduct.value) return
    isPreviewingProduct.value = true
    error.value = ""

    try {
      const { data } = await apiClient.post("/catalog/preview", null, {
        params: { url: sourceUrl },
      })
      return data
    } catch (requestError) {
      error.value = requestError.message
      throw requestError
    } finally {
      isPreviewingProduct.value = false
    }
  }

  async function syncProduct(productId) {
    if (isSyncingProduct.value) return
    isSyncingProduct.value = true
    error.value = ""

    try {
      const { data } = await apiClient.put(`/catalog/${productId}/sync`)
      products.value = products.value.map((product) => (product.id === data.id ? data : product))
      if (currentProduct.value?.id === data.id) {
        currentProduct.value = data
      }
      return data
    } catch (requestError) {
      error.value = requestError.message
      throw requestError
    } finally {
      isSyncingProduct.value = false
    }
  }

  return {
    products,
    currentProduct,
    admins,
    currentAdmin,
    buildings,
    currentBuilding,
    unassignedBuildings,
    csvUploads,
    lastCsvUpload,
    isLoading,
    isSubmittingProduct,
    isSubmittingAdmin,
    isSubmittingBuilding,
    isTogglingProduct,
    isUploadingCsv,
    isDeletingAdmin,
    isDeletingBuilding,
    isAssigningBuildings,
    isDeletingCsv,
    isPreviewingProduct,
    isSyncingProduct,
    submitLoading,
    error,
    fetchProducts,
    fetchProduct,
    createProduct,
    updateProduct,
    toggleProduct,
    uploadCsv,
    fetchAdmins,
    fetchAdmin,
    createAdmin,
    updateAdmin,
    deleteAdmin,
    fetchBuildings,
    fetchBuilding,
    fetchUnassignedBuildings,
    createBuilding,
    updateBuilding,
    deleteBuilding,
    assignBuildings,
    fetchCsvUploads,
    deleteCsvUpload,
    previewProduct,
    syncProduct,
  }
})
