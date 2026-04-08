import { ref } from "vue"

/**
 * Standardizes async API call state management.
 * Provides institutional error handling and loading indicators.
 */
export function useApi(apiCall) {
  const isLoading = ref(false)
  const error = ref(null)
  const data = ref(null)

  const execute = async (...args) => {
    isLoading.value = true
    error.value = null
    
    try {
      const response = await apiCall(...args)
      data.value = response.data
      return response.data
    } catch (err) {
      error.value = err.message || "Error inesperado en el servidor"
      // Re-throw for specific component-level handling if needed (like 409 conflicts)
      throw err
    } finally {
      isLoading.value = false
    }
  }

  return {
    isLoading,
    error,
    data,
    execute
  }
}
