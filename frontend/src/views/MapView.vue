<template>
  <div class="map-page">
    <div class="search-panel" :class="{ collapsed: panelCollapsed }">
      <div class="panel-handle" @click="panelCollapsed = !panelCollapsed">
        <div class="handle-bar"></div>
        <span class="panel-title">{{ panelCollapsed ? 'Find Route' : 'Campus Navigation' }}</span>
      </div>

      <div class="panel-content" v-show="!panelCollapsed">
        <div class="location-status" :class="locationStatusClass">
          <span class="status-dot"></span>
          <span>{{ locationMessage }}</span>
        </div>

        <div class="form-group">
          <label>From</label>
          <div class="select-wrapper">
            <select v-model="selectedOrigin" @change="onOriginChange">
              <option value="">Select starting point</option>
              <option v-for="b in buildings" :key="b.id" :value="b.id">{{ b.name }}</option>
            </select>
          </div>
          <button class="btn-use-location" @click="useMyLocation" v-if="userLat">
            📍 Use my location
          </button>
        </div>

        <div class="form-group">
          <label>To</label>
          <div class="select-wrapper">
            <select v-model="selectedDestination">
              <option value="">Select destination</option>
              <option
                v-for="b in buildings" :key="b.id" :value="b.id"
                :disabled="b.id === selectedOrigin"
              >
                {{ b.name }}
              </option>
            </select>
          </div>
        </div>

        <label class="checkbox-label">
          <input type="checkbox" v-model="accessibleOnly" />
          <span>Accessible routes only ♿</span>
        </label>

        <div class="action-row">
          <button
            class="btn-route"
            @click="findRoute"
            :disabled="!selectedOrigin || !selectedDestination || navStore.loading"
          >
            {{ navStore.loading ? 'Finding...' : '🗺 Get Directions' }}
          </button>
          <button class="btn-clear" @click="clearRoute" v-if="navStore.route">✕</button>
        </div>

        <div class="error-msg" v-if="navStore.error">{{ navStore.error }}</div>

        <div class="nav-mode-banner" v-if="navigating">
          <div class="nav-mode-info">
            <span class="nav-pulse"></span>
            <span>Navigating — following your position</span>
          </div>
          <button class="btn-stop-nav" @click="stopNavigation">Stop</button>
        </div>

        <div class="route-result" v-if="navStore.route?.found">
          <div class="route-summary">
            <span class="route-icon">🚶</span>
            <div>
              <div class="route-distance">{{ formatDistance(navStore.route.total_distance) }}</div>
              <div class="route-label">
                {{ navStore.route.origin.name }} → {{ navStore.route.destination.name }}
              </div>
            </div>
          </div>

          <button class="btn-start-nav" @click="startNavigation" v-if="!navigating && userLat">
            ▶ Start Navigation
          </button>

          <div class="route-steps">
            <div
              class="step" v-for="(step, i) in navStore.route.steps" :key="step.waypoint_id"
              @click="flyToStep(step)"
              :class="{ 'step-active': i === currentStepIndex }"
            >
              <div class="step-number" :class="{ 'step-done': i < currentStepIndex }">
                {{ i < currentStepIndex ? '✓' : i + 1 }}
              </div>
              <div class="step-info">
                <div class="step-name">{{ step.name || stepLabel(step.waypoint_type) }}</div>
                <div class="step-type">{{ step.waypoint_type }}</div>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>

    <div id="map" ref="mapContainer"></div>

    <div class="legend">
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
const mapContainer = ref(null)
let map = null
let buildingMarkers = []
let buildingPolygons = []
let routePolyline = null
let userMarker = null
let userAccuracyCircle = null
let watchId = null

// Location smoothing — keeps last 5 readings and averages them
const positionBuffer = []
const BUFFER_SIZE = 5
const MAX_ACCURACY = 150 // ignore readings worse than 150m
const MAX_JUMP_METRES = 180 // ignore readings that jump more than 180m suddenly

const panelCollapsed = ref(false)
const selectedOrigin = ref('')
const selectedDestination = ref('')
const accessibleOnly = ref(false)
const navigating = ref(false)
const currentStepIndex = ref(0)

const userLat = ref(null)
const userLng = ref(null)
const locationMessage = ref('Detecting your location...')
const locationStatusClass = ref('status-detecting')

const buildings = ref([])
const CALEB_CENTER = [6.6697, 3.6375]

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

// Only buildings missing from OSM — Joshua, New Cafeteria, Main Library removed
// as they already appear on the map
const BUILDING_FOOTPRINTS = {
  'JUPEB Building':                    [6.671246667, 3.639013333, 0.00010, 0.00013],
  'Nursing Building':                  [6.670425000, 3.639011667, 0.00009, 0.00011],
  'Levi Hall':                         [6.672691667, 3.634570000, 0.00011, 0.00009],
  'Integrity Hall':                    [6.671968333, 3.634451667, 0.00011, 0.00009],
  'Psychology & Criminology Building': [6.670145000, 3.639200000, 0.00011, 0.00010],
}

function getBuildingColor(category) {
  return categoryColors[category] || '#7f8c8d'
}

function createBuildingIcon(category) {
  const color = getBuildingColor(category)
  return L.divIcon({
    className: '',
    html: `<div style="width:12px;height:12px;background:${color};border:2.5px solid white;border-radius:50%;box-shadow:0 2px 6px rgba(0,0,0,0.4);"></div>`,
    iconSize: [12, 12],
    iconAnchor: [6, 6],
  })
}

function createUserIcon() {
  return L.divIcon({
    className: '',
    html: `<div style="width:16px;height:16px;background:#1a73e8;border:3px solid white;border-radius:50%;box-shadow:0 0 0 4px rgba(26,115,232,0.3);"></div>`,
    iconSize: [16, 16],
    iconAnchor: [8, 8],
  })
}

function initMap() {
  map = L.map(mapContainer.value, {
    center: CALEB_CENTER,
    zoom: 17,
    zoomControl: false,
  })
  L.control.zoom({ position: 'topright' }).addTo(map)
  L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
    attribution: '© OpenStreetMap contributors',
    maxZoom: 20,
  }).addTo(map)
}

function drawBuildingFootprints(buildingList) {
  buildingPolygons.forEach(p => map.removeLayer(p))
  buildingPolygons = []

  buildingList.forEach(building => {
    const fp = BUILDING_FOOTPRINTS[building.name]
    if (!fp) return

    const [clat, clng, dLat, dLng] = fp

    const bounds = [
      [clat - dLat, clng - dLng],
      [clat - dLat, clng + dLng],
      [clat + dLat, clng + dLng],
      [clat + dLat, clng - dLng],
    ]

    const polygon = L.polygon(bounds, {
      color: '#b8b4a8',
      fillColor: '#d9d5c9',
      fillOpacity: 0.9,
      weight: 1,
      opacity: 1,
    }).addTo(map)

    polygon.bindTooltip(building.name, {
      permanent: false,
      direction: 'center',
    })

    buildingPolygons.push(polygon)
  })
}

function plotBuildings(buildingList) {
  buildingMarkers.forEach(m => map.removeLayer(m))
  buildingMarkers = []

  buildingList.forEach(building => {
    const marker = L.marker([building.latitude, building.longitude], {
      icon: createBuildingIcon(building.category),
    })

    marker.bindPopup(
      `
      <div style="min-width:160px">
        <strong style="color:#1a3a5c">${building.name}</strong><br/>
        <span style="font-size:12px;color:#666;text-transform:capitalize">${building.category}</span>
        ${building.description ? `<br/><span style="font-size:12px">${building.description}</span>` : ''}
        <br/><br/>
        <button onclick="window.setAsDestination(${building.id})"
          style="background:#1a3a5c;color:white;border:none;padding:5px 10px;border-radius:5px;cursor:pointer;font-size:12px;width:100%">
          Navigate here
        </button>
      </div>
    `,
      { maxWidth: 200 },
    )

    marker.addTo(map)
    buildingMarkers.push(marker)
  })
}

function drawRoute(steps) {
  if (routePolyline) {
    map.eachLayer(l => {
      if (l instanceof L.Polyline || l instanceof L.CircleMarker) {
        if (l !== userAccuracyCircle) map.removeLayer(l)
      }
    })
    routePolyline = null
  }

  if (!steps || steps.length === 0) return

  const latlngs = steps.map((s) => [s.latitude, s.longitude])

  routePolyline = L.polyline(latlngs, {
    color: '#1a73e8',
    weight: 6,
    opacity: 0.9,
    lineJoin: 'round',
  }).addTo(map)

  L.circleMarker(latlngs[0], {
    radius: 8, color: '#27ae60', fillColor: '#27ae60', fillOpacity: 1, weight: 2,
  }).bindTooltip('Start').addTo(map)

  L.circleMarker(latlngs[latlngs.length - 1], {
    radius: 8, color: '#c0392b', fillColor: '#c0392b', fillOpacity: 1, weight: 2,
  }).bindTooltip('End').addTo(map)

  map.fitBounds(routePolyline.getBounds(), { padding: [60, 60] })
}

function metresBetween(lat1, lng1, lat2, lng2) {
  const R = 6371000
  const dLat = (lat2 - lat1) * Math.PI / 180
  const dLng = (lng2 - lng1) * Math.PI / 180
  const a = Math.sin(dLat/2)**2 +
    Math.cos(lat1 * Math.PI/180) * Math.cos(lat2 * Math.PI/180) * Math.sin(dLng/2)**2
  return R * 2 * Math.atan2(Math.sqrt(a), Math.sqrt(1-a))
}

function smoothPosition(lat, lng, accuracy) {
  // 1. Reject low quality readings
  if (accuracy > MAX_ACCURACY) return null

  // 2. Reject sudden jumps (GPS multipath error)
  if (positionBuffer.length > 0) {
    const last = positionBuffer[positionBuffer.length - 1]
    const jump = metresBetween(last.lat, last.lng, lat, lng)
    if (jump > MAX_JUMP_METRES) return null
  }

  // 3. Add to buffer
  positionBuffer.push({ lat, lng, accuracy })
  if (positionBuffer.length > BUFFER_SIZE) positionBuffer.shift()

  // 4. Weighted average — more accurate readings get more weight
  let totalWeight = 0
  let avgLat = 0
  let avgLng = 0

  positionBuffer.forEach(p => {
    const weight = 1 / p.accuracy
    avgLat += p.lat * weight
    avgLng += p.lng * weight
    totalWeight += weight
  })

  return {
    lat: avgLat / totalWeight,
    lng: avgLng / totalWeight,
    accuracy: positionBuffer.reduce((s, p) => s + p.accuracy, 0) / positionBuffer.length,
  }
}

function updateUserPosition(lat, lng, accuracy) {
  if (accuracy > MAX_ACCURACY) return

  positionBuffer.push({ lat, lng, accuracy })
  if (positionBuffer.length > BUFFER_SIZE) positionBuffer.shift()

  let totalWeight = 0
  let avgLat = 0
  let avgLng = 0
  positionBuffer.forEach(p => {
    const weight = 1 / p.accuracy
    avgLat += p.lat * weight
    avgLng += p.lng * weight
    totalWeight += weight
  })

  const smoothedLat = avgLat / totalWeight
  const smoothedLng = avgLng / totalWeight
  const smoothedAccuracy = positionBuffer.reduce((s, p) => s + p.accuracy, 0) / positionBuffer.length

  userLat.value = smoothedLat
  userLng.value = smoothedLng

  if (userMarker) map.removeLayer(userMarker)
  if (userAccuracyCircle) map.removeLayer(userAccuracyCircle)

  userAccuracyCircle = L.circle([smoothedLat, smoothedLng], {
    radius: smoothedAccuracy,
    color: '#1a73e8',
    fillColor: '#1a73e8',
    fillOpacity: 0.08,
    weight: 1,
  }).addTo(map)

  userMarker = L.marker([smoothedLat, smoothedLng], { icon: createUserIcon() })
    .bindTooltip(`You (±${Math.round(smoothedAccuracy)}m)`, { direction: 'top' })
    .addTo(map)

  if (navigating.value) {
    map.panTo([smoothedLat, smoothedLng])
    updateCurrentStep(smoothedLat, smoothedLng)
  }
}

function startWatchingLocation() {
  if (!navigator.geolocation) {
    locationMessage.value = 'Geolocation not supported'
    locationStatusClass.value = 'status-error'
    return
  }

  // Get an immediate first fix
  navigator.geolocation.getCurrentPosition(
    (pos) => {
      const { latitude, longitude, accuracy } = pos.coords
      locationMessage.value = `Location active (±${Math.round(accuracy)}m)`
      locationStatusClass.value = accuracy < 30 ? 'status-success' : 'status-detecting'
      updateUserPosition(latitude, longitude, accuracy)
    },
    () => {
      // High accuracy failed, try network-based fallback
      navigator.geolocation.getCurrentPosition(
        (pos) => {
          const { latitude, longitude, accuracy } = pos.coords
          locationMessage.value = `Location active (±${Math.round(accuracy)}m)`
          locationStatusClass.value = 'status-detecting'
          updateUserPosition(latitude, longitude, accuracy)
        },
        () => {
          locationMessage.value = 'Location unavailable — select manually'
          locationStatusClass.value = 'status-error'
        },
        { enableHighAccuracy: false, timeout: 10000, maximumAge: 60000 }
      )
    },
    { enableHighAccuracy: true, timeout: 10000, maximumAge: 0 }
  )

  // Then watch continuously
  watchId = navigator.geolocation.watchPosition(
    (pos) => {
      const { latitude, longitude, accuracy } = pos.coords
      if (accuracy > MAX_ACCURACY) {
        locationMessage.value = `Weak signal (±${Math.round(accuracy)}m) — improving...`
        locationStatusClass.value = 'status-detecting'
      } else {
        locationMessage.value = `Location active (±${Math.round(accuracy)}m)`
        locationStatusClass.value = accuracy < 30 ? 'status-success' : 'status-detecting'
      }
      updateUserPosition(latitude, longitude, accuracy)
    },
    () => {
      locationMessage.value = 'Location unavailable — select manually'
      locationStatusClass.value = 'status-error'
    },
    {
      enableHighAccuracy: true,
      maximumAge: 5000,
      timeout: 20000,
    }
  )
}

function updateCurrentStep(lat, lng) {
  if (!navStore.route?.steps) return
  const steps = navStore.route.steps
  const THRESHOLD = 0.00015

  for (let i = currentStepIndex.value; i < steps.length; i++) {
    const dLat = Math.abs(steps[i].latitude - lat)
    const dLng = Math.abs(steps[i].longitude - lng)
    if (dLat < THRESHOLD && dLng < THRESHOLD) {
      currentStepIndex.value = i
      const stepEl = document.querySelector(`.step:nth-child(${i + 1})`)
      if (stepEl) stepEl.scrollIntoView({ behavior: 'smooth', block: 'nearest' })
      break
    }
  }
}

function startNavigation() {
  navigating.value = true
  currentStepIndex.value = 0
  panelCollapsed.value = false
  if (userLat.value) map.setView([userLat.value, userLng.value], 19)
}

function stopNavigation() {
  navigating.value = false
  currentStepIndex.value = 0
  if (navStore.route?.steps) drawRoute(navStore.route.steps)
}

function useMyLocation() {
  if (!userLat.value) return
  let nearest = null
  let minDist = Infinity
  buildings.value.forEach(b => {
    const d = Math.hypot(b.latitude - userLat.value, b.longitude - userLng.value)
    if (d < minDist) { minDist = d; nearest = b }
  })
  if (nearest) selectedOrigin.value = nearest.id
}

async function findRoute() {
  if (!selectedOrigin.value || !selectedDestination.value) return
  const result = await navStore.getRoute(
    selectedOrigin.value, selectedDestination.value, accessibleOnly.value
  )
  if (result?.found) {
    drawRoute(result.steps)
    currentStepIndex.value = 0
    navigating.value = false
    panelCollapsed.value = false
  }
}

function clearRoute() {
  navStore.clearRoute()
  if (routePolyline) { map.removeLayer(routePolyline); routePolyline = null }
  selectedOrigin.value = ''
  selectedDestination.value = ''
  navigating.value = false
  currentStepIndex.value = 0
}

function flyToStep(step) {
  map.flyTo([step.latitude, step.longitude], 19)
}

function onOriginChange() {
  const b = buildings.value.find(b => b.id === selectedOrigin.value)
  if (b) map.flyTo([b.latitude, b.longitude], 18)
}

function formatDistance(meters) {
  if (meters < 1000) return `${Math.round(meters)}m`
  return `${(meters / 1000).toFixed(1)}km`
}

function stepLabel(type) {
  return {
    entrance: 'Building Entrance',
    junction: 'Path Junction',
    parking: 'Parking',
    landmark: 'Landmark'
  }[type] || type
}

window.setAsDestination = (id) => {
  selectedDestination.value = id
  panelCollapsed.value = false
}

onMounted(async () => {
  initMap()
  startWatchingLocation()
  await navStore.fetchBuildings()
  buildings.value = navStore.buildings
  plotBuildings(buildings.value)
  drawBuildingFootprints(buildings.value)
})

onUnmounted(() => {
  if (map) map.remove()
  if (watchId !== null) navigator.geolocation.clearWatch(watchId)
  delete window.setAsDestination
})

watch(
  () => navStore.route,
  (route) => {
    if (route?.found) drawRoute(route.steps)
  },
)
</script>

<style scoped>
.map-page {
  flex: 1;
  position: relative;
  display: flex;
  flex-direction: column;
  overflow: hidden;
}

#map { flex: 1; z-index: 1; }

.search-panel {
  position: absolute;
  bottom: 0; left: 0; right: 0;
  z-index: 1000;
  background: white;
  border-radius: 20px 20px 0 0;
  box-shadow: 0 -4px 20px rgba(0, 0, 0, 0.15);
  transition: transform 0.3s ease;
  max-height: 80vh;
  overflow-y: auto;
}

.search-panel.collapsed { transform: translateY(calc(100% - 56px)); }

.panel-handle {
  display: flex;
  flex-direction: column;
  align-items: center;
  padding: 10px 16px 6px;
  cursor: pointer;
  user-select: none;
}

.handle-bar {
  width: 40px; height: 4px;
  background: #ddd;
  border-radius: 2px;
  margin-bottom: 6px;
}

.panel-title { font-size: 15px; font-weight: 700; color: #1a3a5c; }
.panel-content { padding: 8px 20px 24px; }

.location-status {
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 12px;
  padding: 8px 12px;
  border-radius: 8px;
  margin-bottom: 14px;
}

.status-detecting {
  background: #fff9e6;
  color: #b7791f;
}
.status-success {
  background: #f0fff4;
  color: #276749;
}
.status-error {
  background: #fff5f5;
  color: #c53030;
}

.status-dot {
  width: 8px; height: 8px;
  border-radius: 50%;
  flex-shrink: 0;
  background: currentColor;
}

.form-group { margin-bottom: 14px; }

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

.select-wrapper select:focus { border-color: #2d6a9f; background-color: white; }

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

.action-row { display: flex; gap: 8px; margin-bottom: 12px; }

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

.btn-route:hover:not(:disabled) {
  background: #2d6a9f;
}
.btn-route:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

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

.nav-mode-banner {
  display: flex;
  align-items: center;
  justify-content: space-between;
  background: #1a3a5c;
  color: white;
  border-radius: 10px;
  padding: 10px 14px;
  margin-bottom: 12px;
}

.nav-mode-info {
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 13px;
}

.nav-pulse {
  width: 10px; height: 10px;
  background: #4ade80;
  border-radius: 50%;
  animation: pulse 1.5s infinite;
}

@keyframes pulse {
  0%, 100% { opacity: 1; transform: scale(1); }
  50% { opacity: 0.5; transform: scale(1.3); }
}

.btn-stop-nav {
  background: rgba(255,255,255,0.2);
  color: white;
  border: 1px solid rgba(255,255,255,0.3);
  padding: 5px 12px;
  border-radius: 6px;
  font-size: 12px;
  cursor: pointer;
}

.btn-start-nav {
  width: 100%;
  padding: 11px;
  background: #27ae60;
  color: white;
  border: none;
  border-radius: 10px;
  font-size: 14px;
  font-weight: 600;
  cursor: pointer;
  margin-bottom: 12px;
}

.route-result {
  background: #f8fafc;
  border-radius: 12px;
  padding: 14px;
  border: 1px solid #e2e8f0;
}

.route-summary { display: flex; align-items: center; gap: 12px; margin-bottom: 12px; }
.route-icon { font-size: 28px; }
.route-distance { font-size: 20px; font-weight: 700; color: #1a3a5c; }
.route-label { font-size: 12px; color: #666; margin-top: 2px; }

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
.step-active { border-color: #1a73e8; background: #ebf4ff; }

.step-number {
  width: 24px; height: 24px;
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

.step-done { background: #27ae60; }
.step-name { font-size: 13px; font-weight: 600; color: #1a202c; }
.step-type { font-size: 11px; color: #888; text-transform: capitalize; }

.legend {
  position: absolute;
  top: 12px; left: 12px;
  z-index: 999;
  background: white;
  border-radius: 10px;
  padding: 10px 12px;
  box-shadow: 0 2px 10px rgba(0, 0, 0, 0.15);
  display: flex;
  flex-direction: column;
  gap: 5px;
}

.legend-item { display: flex; align-items: center; gap: 7px; font-size: 11px; color: #444; }
.legend-dot { width: 10px; height: 10px; border-radius: 50%; flex-shrink: 0; }

@media (min-width: 768px) {
  .search-panel {
    top: 0; bottom: 0; left: 0; right: auto;
    width: 340px;
    border-radius: 0;
    max-height: 100%;
    transform: none !important;
    box-shadow: 4px 0 20px rgba(0, 0, 0, 0.1);
  }
  .panel-handle { display: none; }
  .panel-content { padding: 20px; display: block !important; }
  .panel-title { display: block; font-size: 16px; padding: 16px 20px 0; }
  .legend { left: 356px; }
}
</style>
