<template>
  <div class="map-page">
    <!-- Search Panel -->
    <div class="search-panel" :class="{ collapsed: panelCollapsed }">
      <div class="panel-handle" @click="panelCollapsed = !panelCollapsed">
        <div class="handle-bar"></div>
        <span class="panel-title">{{ panelCollapsed ? 'Find Route' : 'Campus Navigation' }}</span>
      </div>

      <div class="panel-content" v-show="!panelCollapsed">
        <!-- Location Status -->
        <div class="location-status" :class="locationStatusClass">
          <span class="status-dot"></span>
          <span>{{ locationMessage }}</span>
        </div>

        <!-- Origin -->
        <div class="form-group">
          <label>From</label>
          <div class="select-wrapper">
            <select v-model="selectedOrigin" @change="onOriginChange">
              <option value="">Select starting point</option>
              <option
                v-for="b in buildings"
                :key="b.id"
                :value="b.id"
              >{{ b.name }}</option>
            </select>
          </div>
          <button class="btn-use-location" @click="useMyLocation" v-if="userLat">
            📍 Use my location
          </button>
        </div>

        <!-- Destination -->
        <div class="form-group">
          <label>To</label>
          <div class="select-wrapper">
            <select v-model="selectedDestination">
              <option value="">Select destination</option>
              <option
                v-for="b in buildings"
                :key="b.id"
                :value="b.id"
                :disabled="b.id === selectedOrigin"
              >{{ b.name }}</option>
            </select>
          </div>
        </div>

        <!-- Accessible Only -->
        <label class="checkbox-label">
          <input type="checkbox" v-model="accessibleOnly" />
          <span>Accessible routes only ♿</span>
        </label>

        <!-- Action Buttons -->
        <div class="action-row">
          <button
            class="btn-route"
            @click="findRoute"
            :disabled="!selectedOrigin || !selectedDestination || navStore.loading"
          >
            {{ navStore.loading ? 'Finding...' : '🗺 Get Directions' }}
          </button>
          <button class="btn-clear" @click="clearRoute" v-if="navStore.route">
            ✕
          </button>
        </div>

        <!-- Error -->
        <div class="error-msg" v-if="navStore.error">
          {{ navStore.error }}
        </div>

        <!-- Route Result -->
        <div class="route-result" v-if="navStore.route?.found">
          <div class="route-summary">
            <span class="route-icon">🚶</span>
            <div>
              <div class="route-distance">
                {{ formatDistance(navStore.route.total_distance) }}
              </div>
              <div class="route-label">
                {{ navStore.route.origin.name }} → {{ navStore.route.destination.name }}
              </div>
            </div>
          </div>

          <div class="route-steps">
            <div
              class="step"
              v-for="(step, i) in navStore.route.steps"
              :key="step.waypoint_id"
              @click="flyToStep(step)"
            >
              <div class="step-number">{{ i + 1 }}</div>
              <div class="step-info">
                <div class="step-name">{{ step.name || stepLabel(step.waypoint_type) }}</div>
                <div class="step-type">{{ step.waypoint_type }}</div>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>

    <!-- Map Container -->
    <div id="map" ref="mapContainer"></div>

    <!-- Buildings Legend -->
    <div class="legend" v-if="!panelCollapsed === false || true">
      <div class="legend-item" v-for="cat in categories" :key="cat.key">
        <span class="legend-dot" :style="{ background: cat.color }"></span>
        <span>{{ cat.label }}</span>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted, onUnmounted, watch } from 'vue'
import L from 'leaflet'
import 'leaflet/dist/leaflet.css'
import { useNavigationStore } from '@/stores/navigation'

const navStore = useNavigationStore()

// Map refs
const mapContainer = ref(null)
let map = null
let buildingMarkers = []
let routePolyline = null
let userMarker = null

// UI state
const panelCollapsed = ref(false)
const selectedOrigin = ref('')
const selectedDestination = ref('')
const accessibleOnly = ref(false)

// User location
const userLat = ref(null)
const userLng = ref(null)
const locationMessage = ref('Detecting your location...')
const locationStatusClass = ref('status-detecting')

// Buildings
const buildings = ref([])

// Caleb University coordinates
const CALEB_CENTER = [6.6333, 3.6167]
const DEFAULT_ZOOM = 17

const categories = [
  { key: 'academic', label: 'Academic', color: '#2d6a9f' },
  { key: 'administrative', label: 'Admin', color: '#8e44ad' },
  { key: 'hostel', label: 'Hostel', color: '#27ae60' },
  { key: 'facility', label: 'Facility', color: '#e67e22' },
  { key: 'religious', label: 'Chapel', color: '#c0392b' },
  { key: 'medical', label: 'Medical', color: '#e74c3c' },
  { key: 'sport', label: 'Sport', color: '#16a085' },
  { key: 'other', label: 'Other', color: '#7f8c8d' },
]

const categoryColors = Object.fromEntries(categories.map(c => [c.key, c.color]))

function getBuildingColor(category) {
  return categoryColors[category] || '#7f8c8d'
}

function createBuildingIcon(category) {
  const color = getBuildingColor(category)
  return L.divIcon({
    className: '',
    html: `<div style="
      width:14px;height:14px;
      background:${color};
      border:2.5px solid white;
      border-radius:50%;
      box-shadow:0 2px 6px rgba(0,0,0,0.4);
    "></div>`,
    iconSize: [14, 14],
    iconAnchor: [7, 7],
  })
}

function createUserIcon() {
  return L.divIcon({
    className: '',
    html: `<div style="
      width:16px;height:16px;
      background:#1a73e8;
      border:3px solid white;
      border-radius:50%;
      box-shadow:0 0 0 4px rgba(26,115,232,0.3);
    "></div>`,
    iconSize: [16, 16],
    iconAnchor: [8, 8],
  })
}

function initMap() {
  map = L.map(mapContainer.value, {
    center: CALEB_CENTER,
    zoom: DEFAULT_ZOOM,
    zoomControl: false,
  })

  // Add zoom control top-right
  L.control.zoom({ position: 'topright' }).addTo(map)

  // OpenStreetMap tiles
  L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
    attribution: '© OpenStreetMap contributors',
    maxZoom: 20,
  }).addTo(map)
}

function plotBuildings() {
  // Clear existing markers
  buildingMarkers.forEach(m => map.removeLayer(m))
  buildingMarkers = []

  buildings.value.forEach(building => {
    const marker = L.marker([building.latitude, building.longitude], {
      icon: createBuildingIcon(building.category),
    })

    marker.bindPopup(`
      <div style="min-width:160px">
        <strong style="color:#1a3a5c">${building.name}</strong><br/>
        <span style="font-size:12px;color:#666;text-transform:capitalize">
          ${building.category}
        </span>
        ${building.description ? `<br/><span style="font-size:12px">${building.description}</span>` : ''}
        <br/><br/>
        <button
          onclick="window.setAsDestination(${building.id})"
          style="
            background:#1a3a5c;color:white;border:none;
            padding:5px 10px;border-radius:5px;cursor:pointer;
            font-size:12px;width:100%
          "
        >Navigate here</button>
      </div>
    `, { maxWidth: 200 })

    marker.addTo(map)
    buildingMarkers.push(marker)
  })
}

function drawRoute(steps) {
  // Remove existing route
  if (routePolyline) {
    map.removeLayer(routePolyline)
    routePolyline = null
  }

  if (!steps || steps.length === 0) return

  const latlngs = steps.map(s => [s.latitude, s.longitude])

  routePolyline = L.polyline(latlngs, {
    color: '#1a73e8',
    weight: 5,
    opacity: 0.85,
    dashArray: null,
    lineJoin: 'round',
  }).addTo(map)

  // Add start and end markers
  L.circleMarker(latlngs[0], {
    radius: 8, color: '#27ae60', fillColor: '#27ae60', fillOpacity: 1, weight: 2
  }).bindTooltip('Start').addTo(map)

  L.circleMarker(latlngs[latlngs.length - 1], {
    radius: 8, color: '#c0392b', fillColor: '#c0392b', fillOpacity: 1, weight: 2
  }).bindTooltip('End').addTo(map)

  map.fitBounds(routePolyline.getBounds(), { padding: [60, 60] })
}

function getUserLocation() {
  if (!navigator.geolocation) {
    locationMessage.value = 'Geolocation not supported'
    locationStatusClass.value = 'status-error'
    return
  }

  navigator.geolocation.getCurrentPosition(
    (pos) => {
      userLat.value = pos.coords.latitude
      userLng.value = pos.coords.longitude
      locationMessage.value = 'Location detected'
      locationStatusClass.value = 'status-success'

      if (userMarker) map.removeLayer(userMarker)
      userMarker = L.marker([userLat.value, userLng.value], {
        icon: createUserIcon(),
      }).bindTooltip('You are here').addTo(map)
    },
    () => {
      locationMessage.value = 'Location unavailable — select manually'
      locationStatusClass.value = 'status-error'
    },
    { enableHighAccuracy: true, timeout: 10000 }
  )
}

function useMyLocation() {
  // Find the nearest building to user location and set as origin
  if (!userLat.value) return
  let nearest = null
  let minDist = Infinity

  buildings.value.forEach(b => {
    const d = Math.hypot(b.latitude - userLat.value, b.longitude - userLng.value)
    if (d < minDist) {
      minDist = d
      nearest = b
    }
  })

  if (nearest) {
    selectedOrigin.value = nearest.id
  }
}

async function findRoute() {
  if (!selectedOrigin.value || !selectedDestination.value) return
  const result = await navStore.getRoute(
    selectedOrigin.value,
    selectedDestination.value,
    accessibleOnly.value
  )
  if (result?.found) {
    drawRoute(result.steps)
    panelCollapsed.value = false
  }
}

function clearRoute() {
  navStore.clearRoute()
  if (routePolyline) {
    map.removeLayer(routePolyline)
    routePolyline = null
  }
  selectedOrigin.value = ''
  selectedDestination.value = ''
}

function flyToStep(step) {
  map.flyTo([step.latitude, step.longitude], 19)
}

function onOriginChange() {
  // Pan map to selected origin building
  const building = buildings.value.find(b => b.id === selectedOrigin.value)
  if (building) {
    map.flyTo([building.latitude, building.longitude], 18)
  }
}

function formatDistance(meters) {
  if (meters < 1000) return `${Math.round(meters)}m`
  return `${(meters / 1000).toFixed(1)}km`
}

function stepLabel(type) {
  const labels = {
    entrance: 'Building Entrance',
    junction: 'Path Junction',
    parking: 'Parking Area',
    landmark: 'Landmark',
  }
  return labels[type] || type
}

// Expose setAsDestination to popup buttons
window.setAsDestination = (id) => {
  selectedDestination.value = id
  panelCollapsed.value = false
}

onMounted(async () => {
  initMap()
  getUserLocation()
  await navStore.fetchBuildings()
  buildings.value = navStore.buildings
  plotBuildings()
})

onUnmounted(() => {
  if (map) map.remove()
  delete window.setAsDestination
})

watch(() => navStore.route, (route) => {
  if (route?.found) drawRoute(route.steps)
})
</script>

<style scoped>
.map-page {
  flex: 1;
  position: relative;
  display: flex;
  flex-direction: column;
  overflow: hidden;
}

#map {
  flex: 1;
  z-index: 1;
}

/* Search Panel — slides up from bottom on mobile */
.search-panel {
  position: absolute;
  bottom: 0;
  left: 0;
  right: 0;
  z-index: 1000;
  background: white;
  border-radius: 20px 20px 0 0;
  box-shadow: 0 -4px 20px rgba(0,0,0,0.15);
  transition: transform 0.3s ease;
  max-height: 80vh;
  overflow-y: auto;
}

.search-panel.collapsed {
  transform: translateY(calc(100% - 56px));
}

.panel-handle {
  display: flex;
  flex-direction: column;
  align-items: center;
  padding: 10px 16px 6px;
  cursor: pointer;
  user-select: none;
}

.handle-bar {
  width: 40px;
  height: 4px;
  background: #ddd;
  border-radius: 2px;
  margin-bottom: 6px;
}

.panel-title {
  font-size: 15px;
  font-weight: 700;
  color: #1a3a5c;
}

.panel-content {
  padding: 8px 20px 24px;
}

.location-status {
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 12px;
  padding: 8px 12px;
  border-radius: 8px;
  margin-bottom: 14px;
}

.status-detecting { background: #fff9e6; color: #b7791f; }
.status-success { background: #f0fff4; color: #276749; }
.status-error { background: #fff5f5; color: #c53030; }

.status-dot {
  width: 8px;
  height: 8px;
  border-radius: 50%;
  flex-shrink: 0;
  background: currentColor;
}

.form-group {
  margin-bottom: 14px;
}

.form-group label {
  display: block;
  font-size: 12px;
  font-weight: 700;
  color: #444;
  margin-bottom: 6px;
  text-transform: uppercase;
  letter-spacing: 0.5px;
}

.select-wrapper select {
  width: 100%;
  padding: 11px 14px;
  border: 1.5px solid #e2e8f0;
  border-radius: 10px;
  font-size: 14px;
  background: #f8fafc;
  color: #1a202c;
  outline: none;
  appearance: none;
  background-image: url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' width='12' height='12' viewBox='0 0 12 12'%3E%3Cpath fill='%23666' d='M6 8L1 3h10z'/%3E%3C/svg%3E");
  background-repeat: no-repeat;
  background-position: right 14px center;
}

.select-wrapper select:focus {
  border-color: #2d6a9f;
  background-color: white;
}

.btn-use-location {
  margin-top: 6px;
  background: none;
  border: 1px solid #2d6a9f;
  color: #2d6a9f;
  padding: 5px 12px;
  border-radius: 6px;
  font-size: 12px;
  cursor: pointer;
}

.checkbox-label {
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 13px;
  color: #444;
  margin-bottom: 14px;
  cursor: pointer;
}

.action-row {
  display: flex;
  gap: 8px;
  margin-bottom: 12px;
}

.btn-route {
  flex: 1;
  padding: 13px;
  background: #1a3a5c;
  color: white;
  border: none;
  border-radius: 10px;
  font-size: 15px;
  font-weight: 600;
  cursor: pointer;
  transition: background 0.2s;
}

.btn-route:hover:not(:disabled) { background: #2d6a9f; }
.btn-route:disabled { opacity: 0.5; cursor: not-allowed; }

.btn-clear {
  padding: 13px 16px;
  background: #f1f5f9;
  color: #555;
  border: none;
  border-radius: 10px;
  font-size: 15px;
  cursor: pointer;
}

.error-msg {
  background: #fff5f5;
  color: #c53030;
  border: 1px solid #fed7d7;
  border-radius: 8px;
  padding: 10px 14px;
  font-size: 13px;
  margin-bottom: 12px;
}

.route-result {
  background: #f8fafc;
  border-radius: 12px;
  padding: 14px;
  border: 1px solid #e2e8f0;
}

.route-summary {
  display: flex;
  align-items: center;
  gap: 12px;
  margin-bottom: 12px;
}

.route-icon { font-size: 28px; }

.route-distance {
  font-size: 20px;
  font-weight: 700;
  color: #1a3a5c;
}

.route-label {
  font-size: 12px;
  color: #666;
  margin-top: 2px;
}

.route-steps {
  display: flex;
  flex-direction: column;
  gap: 6px;
  max-height: 180px;
  overflow-y: auto;
}

.step {
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 8px 10px;
  background: white;
  border-radius: 8px;
  cursor: pointer;
  border: 1px solid #e2e8f0;
  transition: background 0.15s;
}

.step:hover { background: #ebf4ff; }

.step-number {
  width: 24px;
  height: 24px;
  background: #1a3a5c;
  color: white;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 11px;
  font-weight: 700;
  flex-shrink: 0;
}

.step-name {
  font-size: 13px;
  font-weight: 600;
  color: #1a202c;
}

.step-type {
  font-size: 11px;
  color: #888;
  text-transform: capitalize;
}

/* Legend */
.legend {
  position: absolute;
  top: 12px;
  left: 12px;
  z-index: 999;
  background: white;
  border-radius: 10px;
  padding: 10px 12px;
  box-shadow: 0 2px 10px rgba(0,0,0,0.15);
  display: flex;
  flex-direction: column;
  gap: 5px;
}

.legend-item {
  display: flex;
  align-items: center;
  gap: 7px;
  font-size: 11px;
  color: #444;
}

.legend-dot {
  width: 10px;
  height: 10px;
  border-radius: 50%;
  flex-shrink: 0;
}

/* Desktop: panel on the left side */
@media (min-width: 768px) {
  .search-panel {
    top: 0;
    bottom: 0;
    left: 0;
    right: auto;
    width: 340px;
    border-radius: 0;
    max-height: 100%;
    transform: none !important;
    box-shadow: 4px 0 20px rgba(0,0,0,0.1);
  }

  .panel-handle {
    display: none;
  }

  .panel-content {
    padding: 20px;
    display: block !important;
  }

  .panel-title {
    display: block;
    font-size: 16px;
    padding: 16px 20px 0;
  }

  .legend {
    left: 356px;
  }
}
</style>