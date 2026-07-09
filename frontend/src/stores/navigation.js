import { defineStore } from 'pinia'
import { ref } from 'vue'
import api from '@/api'

export const useNavigationStore = defineStore('navigation', () => {
  const buildings = ref([])
  const route = ref(null)
  const loading = ref(false)
  const error = ref(null)

  async function fetchBuildings() {
    try {
      const res = await api.get('/navigation/buildings/')
      buildings.value = res.data
    } catch (err) {
      error.value = 'Failed to load buildings'
    }
  }

  async function getRoute(originId, destinationId, accessibleOnly = false) {
    loading.value = true
    error.value = null
    route.value = null
    try {
      const res = await api.post('/navigation/route/', {
        origin_id: originId,
        destination_id: destinationId,
        accessible_only: accessibleOnly,
      })
      route.value = res.data
      return res.data
    } catch (err) {
      error.value = 'No route found between these locations'
      return null
    } finally {
      loading.value = false
    }
  }

  function clearRoute() {
    route.value = null
    error.value = null
  }

  return { buildings, route, loading, error, fetchBuildings, getRoute, clearRoute }
})