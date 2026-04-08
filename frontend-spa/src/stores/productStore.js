import { ref } from "vue"
import { defineStore } from "pinia"
import catalogApi from "@/api/catalog.api"

export const useProductStore = defineStore("products", () => {
  const products = ref([])
  const currentProduct = ref(null)
  const csvUploads = ref([])
  const lastCsvUpload = ref(null)
  
  const isLoading = ref(false)
  const isSubmitting = ref(false)
  const isToggling = ref(false)
  const isSyncing = ref(false)
  const isUploadingCsv = ref(false)
  const isDeletingCsv = ref(false)
  const error = ref("")

  async function fetchProducts(query = "") {
    isLoading.value = true
    error.value = ""
    try {
      const { data } = await catalogApi.getAll(query)
      products.value = data
      return data
    } catch (err) {
      error.value = err.message
      return null
    } finally {
      isLoading.value = false
    }
  }

  async function fetchProduct(id) {
    isLoading.value = true
    error.value = ""
    try {
      const { data } = await catalogApi.getById(id)
      currentProduct.value = data
      return data
    } catch (err) {
      error.value = err.message
      return null
    } finally {
      isLoading.value = false
    }
  }

  async function createProduct(payload) {
    if (isSubmitting.value) return
    isSubmitting.value = true
    error.value = ""
    try {
      const { data } = await catalogApi.create(payload)
      products.value = [data, ...products.value]
      return data
    } catch (err) {
      error.value = err.message
      throw err
    } finally {
      isSubmitting.value = false
    }
  }

  async function updateProduct(id, payload) {
    if (isSubmitting.value) return
    isSubmitting.value = true
    error.value = ""
    try {
      const { data } = await catalogApi.update(id, payload)
      currentProduct.value = data
      products.value = products.value.map(p => p.id === data.id ? data : p)
      return data
    } catch (err) {
      error.value = err.message
      throw err
    } finally {
      isSubmitting.value = false
    }
  }

  async function toggleProduct(id) {
    if (isToggling.value) return
    isToggling.value = true
    error.value = ""
    try {
      const { data } = await catalogApi.toggleStatus(id)
      products.value = products.value.map(p => p.id === data.id ? data : p)
      return data
    } catch (err) {
      error.value = err.message
      throw err
    } finally {
      isToggling.value = false
    }
  }

  async function syncProduct(id) {
    if (isSyncing.value) return
    isSyncing.value = true
    error.value = ""
    try {
      const { data } = await catalogApi.sync(id)
      products.value = products.value.map(p => p.id === data.id ? data : p)
      if (currentProduct.value?.id === data.id) currentProduct.value = data
      return data
    } catch (err) {
      error.value = err.message
      throw err
    } finally {
      isSyncing.value = false
    }
  }

  async function uploadCsv(file) {
    if (isUploadingCsv.value) return
    isUploadingCsv.value = true
    error.value = ""
    try {
      const { data } = await catalogApi.importCsv(file)
      lastCsvUpload.value = data
      await fetchCsvUploads()
      return data
    } catch (err) {
      error.value = err.message
      throw err
    } finally {
      isUploadingCsv.value = false
    }
  }

  async function fetchCsvUploads() {
    isLoading.value = true
    error.value = ""
    try {
      const { data } = await catalogApi.getUploads()
      csvUploads.value = data
      return data
    } catch (err) {
      error.value = err.message
      return null
    } finally {
      isLoading.value = false
    }
  }

  async function deleteCsvUpload(id) {
    if (isDeletingCsv.value) return
    isDeletingCsv.value = true
    error.value = ""
    try {
      await catalogApi.deleteUpload(id)
      csvUploads.value = csvUploads.value.filter(u => u.id !== id)
    } catch (err) {
      error.value = err.message
      throw err
    } finally {
      isDeletingCsv.value = false
    }
  }

  return {
    products,
    currentProduct,
    csvUploads,
    lastCsvUpload,
    isLoading,
    isSubmitting,
    isToggling,
    isSyncing,
    isUploadingCsv,
    isDeletingCsv,
    error,
    fetchProducts,
    fetchProduct,
    createProduct,
    updateProduct,
    toggleProduct,
    syncProduct,
    uploadCsv,
    fetchCsvUploads,
    deleteCsvUpload
  }
})
