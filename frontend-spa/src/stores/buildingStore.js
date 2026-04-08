import { ref } from "vue"
import { defineStore } from "pinia"
import buildingsApi from "@/api/buildings.api"

export const useBuildingStore = defineStore("buildings", () => {
  const buildings = ref([])
  const unassignedBuildings = ref([])
  const currentBuilding = ref(null)
  
  const isLoading = ref(false)
  const isSubmitting = ref(false)
  const isDeleting = ref(false)
  const isAssigning = ref(false)
  const error = ref("")

  async function fetchBuildings() {
    isLoading.value = true
    error.value = ""
    try {
      const { data } = await buildingsApi.list()
      buildings.value = data
      return data
    } catch (err) {
      error.value = err.message
      return null
    } finally {
      isLoading.value = false
    }
  }

  async function fetchBuilding(id) {
    isLoading.value = true
    error.value = ""
    try {
      const { data } = await buildingsApi.getById(id)
      currentBuilding.value = data
      return data
    } catch (err) {
      error.value = err.message
      return null
    } finally {
      isLoading.value = false
    }
  }

  async function fetchUnassignedBuildings() {
    isLoading.value = true
    error.value = ""
    try {
      const { data } = await buildingsApi.listUnassigned()
      unassignedBuildings.value = data
      return data
    } catch (err) {
      error.value = err.message
      return null
    } finally {
      isLoading.value = false
    }
  }

  async function createBuilding(payload) {
    if (isSubmitting.value) return
    isSubmitting.value = true
    error.value = ""
    try {
      const { data } = await buildingsApi.create(payload)
      buildings.value = [data, ...buildings.value]
      return data
    } catch (err) {
      error.value = err.message
      throw err
    } finally {
      isSubmitting.value = false
    }
  }

  async function updateBuilding(id, payload) {
    if (isSubmitting.value) return
    isSubmitting.value = true
    error.value = ""
    try {
      const { data } = await buildingsApi.update(id, payload)
      currentBuilding.value = data
      buildings.value = buildings.value.map(b => b.id === data.id ? data : b)
      return data
    } catch (err) {
      error.value = err.message
      throw err
    } finally {
      isSubmitting.value = false
    }
  }

  async function deleteBuilding(id) {
    if (isDeleting.value) return
    isDeleting.value = true
    error.value = ""
    try {
      await buildingsApi.delete(id)
      buildings.value = buildings.value.filter(b => b.id !== id)
    } catch (err) {
      error.value = err.message
      throw err
    } finally {
      isDeleting.value = false
    }
  }

  async function assignToAdmin(adminId, buildingIds) {
    if (isAssigning.value) return
    isAssigning.value = true
    error.value = ""
    try {
      const { data } = await buildingsApi.assignToAdmin(adminId, buildingIds)
      return data
    } catch (err) {
      error.value = err.message
      throw err
    } finally {
      isAssigning.value = false
    }
  }

  return {
    buildings,
    unassignedBuildings,
    currentBuilding,
    isLoading,
    isSubmitting,
    isDeleting,
    isAssigning,
    error,
    fetchBuildings,
    fetchBuilding,
    fetchUnassignedBuildings,
    createBuilding,
    updateBuilding,
    deleteBuilding,
    assignToAdmin
  }
})
